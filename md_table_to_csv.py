"""
Markdown Table to CSV Converter
================================

Reads .md files, extracts every Markdown table, and writes each table as a
separate CSV file.

Usage:
    python md_table_to_csv.py                          # default ./input/ -> ./output/
    python md_table_to_csv.py -i docs/ -o results/     # custom directories
    python md_table_to_csv.py -i report.md              # single file
    python md_table_to_csv.py -r                        # recursive scan
    python md_table_to_csv.py --no-bom                  # plain UTF-8 output

Output naming convention:
    {original_filename}_table1.csv, {original_filename}_table2.csv, ...

Supports three table formats:

1. Standard Markdown pipe tables:

    | Name  | Age | City     |
    |-------|-----|----------|
    | Alice | 30  | New York |

2. Pipe tables without outer delimiters:

    Name  | Age | City
    ------|-----|----------
    Alice | 30  | New York

3. Unicode box-drawing tables:

    ┌───────┬─────┬──────────┐
    │ Name  │ Age │ City     │
    ├───────┼─────┼──────────┤
    │ Alice │ 30  │ New York │
    └───────┴─────┴──────────┘

Tables inside blockquotes (> prefixed lines) are also detected.
Escaped pipes (\\|) in cell values are preserved as literal pipe characters.
Separator/border rows are detected and excluded from the CSV output.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Directories are relative to the script's location
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = SCRIPT_DIR / "input"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output"

# Characters that mark the start of a table line:
#   - '|'  for standard Markdown pipe tables
#   - '│'  for box-drawing data rows
#   - '┌'  for box-drawing top border
#   - '├'  for box-drawing mid separator
#   - '└'  for box-drawing bottom border
TABLE_LINE_STARTS = ("|", "│", "┌", "├", "└")

# Box-drawing characters used in borders and separators (no text content)
BOX_BORDER_CHARS = set("┌┐└┘├┤┬┴┼─│")

# Regex to match a Markdown separator row without outer pipes:
#   e.g.  "------|-----|----------"  or  ":---: | ---: | :---"
_BARE_SEPARATOR_RE = re.compile(
    r"^[\s:\-]+(?:\|[\s:─\-]+)+$"
)

# Regex to match a pipe-less table row (at least one unescaped pipe in the middle):
#   e.g.  "Alice | 30 | New York"
_BARE_TABLE_ROW_RE = re.compile(
    r"^[^|]+(?<!\\)\|.+$"
)


def _strip_blockquote(line: str) -> str:
    """
    Remove leading blockquote markers (>) from a line.

    Handles nested blockquotes like '> > | cell |'.
    Returns the line with all leading '>' prefixes stripped.
    """
    stripped = line.strip()
    while stripped.startswith(">"):
        stripped = stripped[1:].lstrip()
    return stripped


def _is_table_line(line: str) -> bool:
    """
    Check if a line (after blockquote stripping) looks like a table line.

    Detects:
    - Standard pipe-prefixed lines:  | cell | cell |
    - Box-drawing lines:             │ cell │ cell │
    - Bare table rows (no outer pipes):  cell | cell | cell
    - Bare separator rows:           ------|------|------
    """
    if not line:
        return False

    # Standard table lines starting with pipe or box-drawing chars
    if line[0] in TABLE_LINE_STARTS:
        return True

    # Bare separator row:  ------|------|------
    if _BARE_SEPARATOR_RE.match(line):
        return True

    # Bare table row:  cell | cell | cell
    if _BARE_TABLE_ROW_RE.match(line):
        return True

    return False


def find_tables(text: str) -> list[list[str]]:
    """
    Scan markdown text and group consecutive table lines into blocks.

    A table line is any line whose stripped form (after removing blockquote
    prefixes) starts with a pipe '|', a Unicode box-drawing character, or
    looks like a bare pipe-delimited row.  Consecutive table lines are
    grouped into one block.  Non-table lines act as block boundaries.

    Args:
        text: The full markdown file content as a string.

    Returns:
        A list of table blocks. Each block is a list of raw line strings
        (with blockquote prefixes already removed).
    """
    tables = []
    current_block = []

    for line in text.splitlines():
        cleaned = _strip_blockquote(line)

        if _is_table_line(cleaned):
            current_block.append(cleaned)
        else:
            # End of a contiguous block — save it if it has enough lines to
            # be a valid table (at least a header + separator = 2 lines).
            if len(current_block) >= 2:
                tables.append(current_block)
            current_block = []

    # Don't forget a table that extends to the end of the file
    if len(current_block) >= 2:
        tables.append(current_block)

    return tables


def _is_separator_row(line: str) -> bool:
    """
    Return True if the line is a table separator or border row.

    Matches both formats:
      - Markdown:    |---|---| or | :---: | ---: |
      - Bare:        ------|------|------
      - Box-drawing: ┌───┬───┐  or  ├───┼───┤  or  └───┴───┘

    The key insight: separator/border rows contain NO alphanumeric text.
    """
    # Remove all characters that are valid in a separator/border row.
    # Standard pipe separators: |, -, :, whitespace
    # Box-drawing borders: ┌┐└┘├┤┬┴┼─│ and whitespace
    cleaned = re.sub(r"[|\-:\s┌┐└┘├┤┬┴┼─│]", "", line)
    return len(cleaned) == 0


def _split_row(line: str) -> list[str]:
    """
    Split a single table row on its delimiter and return stripped cell values.

    Automatically detects whether the row uses '|' (Markdown) or '│'
    (box-drawing) as the cell delimiter.  Escaped pipes (\\|) in Markdown
    tables are preserved as literal '|' in the output.

    Leading and trailing empty strings (from the outer delimiters) are removed.
    Examples:
        "| Alice | 30 |"       →  ["Alice", "30"]
        "│ Alice │ 30 │"       →  ["Alice", "30"]
        "| A \\| B | 30 |"    →  ["A | B", "30"]
        "Alice | 30 | NYC"     →  ["Alice", "30", "NYC"]
    """
    if "│" in line:
        # Box-drawing delimiter — no escape handling needed
        cells = line.split("│")
    else:
        # Markdown pipe delimiter — handle escaped pipes (\|)
        # Replace escaped pipes with a placeholder, split, then restore
        placeholder = "\x00PIPE\x00"
        protected = line.replace("\\|", placeholder)
        cells = protected.split("|")
        cells = [cell.replace(placeholder, "|") for cell in cells]

    # The split produces empty strings at the start/end when the line begins
    # and ends with the delimiter. Strip those off.
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]

    return [cell.strip() for cell in cells]


def parse_table(lines: list[str]) -> list[list[str]]:
    """
    Parse a raw table block into a 2-D list of cell values.

    Separator and border rows are automatically detected and excluded.
    The first non-separator row becomes the header row in the output.

    Args:
        lines: Raw table lines from find_tables().

    Returns:
        A list of rows, where each row is a list of cell strings.
        The first row is the header.  Returns an empty list if no
        data rows are found.
    """
    rows = []
    for line in lines:
        if _is_separator_row(line):
            continue
        rows.append(_split_row(line))
    return rows


def _clean_output_dir(output_dir: Path) -> int:
    """
    Remove existing .csv files from the output directory.

    Returns the number of files removed.
    """
    removed = 0
    for csv_file in output_dir.glob("*.csv"):
        csv_file.unlink()
        removed += 1
    return removed


def convert_file(input_path: Path, output_dir: Path, encoding: str = "utf-8-sig") -> int:
    """
    Read a single Markdown file, extract all tables, and write each as CSV.

    Each table is written to a separate file named:
        {stem}_table{n}.csv   (n starts at 1, sequential with no gaps)

    If the file contains no tables, nothing is written.

    Args:
        input_path: Path to the .md file.
        output_dir: Directory where CSV files will be created.
        encoding:   Output encoding ('utf-8-sig' for BOM, 'utf-8' for plain).

    Returns:
        The number of tables successfully converted.
    """
    text = input_path.read_text(encoding="utf-8")
    raw_tables = find_tables(text)

    if not raw_tables:
        print(f"  No tables found in {input_path.name}")
        return 0

    tables_written = 0
    for raw_table in raw_tables:
        rows = parse_table(raw_table)
        if not rows:
            continue

        tables_written += 1
        output_name = f"{input_path.stem}_table{tables_written}.csv"
        output_path = output_dir / output_name

        with open(output_path, "w", newline="", encoding=encoding) as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"  Wrote {output_path.name}  ({len(rows)} rows, {len(rows[0])} columns)")

    return tables_written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown tables to CSV files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                          # default ./input/ -> ./output/\n"
            "  %(prog)s -i docs/ -o results/     # custom directories\n"
            "  %(prog)s -i report.md              # single file\n"
            "  %(prog)s -r                        # recursive scan of input/\n"
            "  %(prog)s --no-bom                  # plain UTF-8 output (no BOM)\n"
        ),
    )
    parser.add_argument(
        "-i", "--input",
        default=None,
        help="Input .md file or directory (default: ./input/)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory for CSV files (default: ./output/)",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan input directory for .md files",
    )
    parser.add_argument(
        "--no-bom",
        action="store_true",
        help="Use plain UTF-8 encoding instead of UTF-8 with BOM (default includes BOM for Excel compatibility)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """
    Entry point: scan input for .md files and convert all tables to CSV.
    """
    args = parse_args(argv)

    # Resolve input path
    if args.input:
        input_path = Path(args.input).resolve()
    else:
        input_path = DEFAULT_INPUT_DIR

    # Resolve output directory
    output_dir = Path(args.output).resolve() if args.output else DEFAULT_OUTPUT_DIR

    # Determine encoding
    encoding = "utf-8" if args.no_bom else "utf-8-sig"

    # Collect markdown files
    if input_path.is_file():
        if not input_path.suffix.lower() == ".md":
            print(f"Error: {input_path} is not a .md file.")
            sys.exit(1)
        md_files = [input_path]
    else:
        # It's a directory
        input_path.mkdir(parents=True, exist_ok=True)
        if args.recursive:
            md_files = sorted(input_path.rglob("*.md"))
        else:
            md_files = sorted(input_path.glob("*.md"))

    if not md_files:
        print(f"No .md files found in {input_path}")
        print("Place your .md files in the input directory and run again.")
        sys.exit(1)

    # Prepare output directory and clean stale files
    output_dir.mkdir(parents=True, exist_ok=True)
    removed = _clean_output_dir(output_dir)
    if removed:
        print(f"Cleaned {removed} old CSV file(s) from {output_dir}\n")

    print(f"Scanning {len(md_files)} markdown file(s) in {input_path}\n")

    total_tables = 0
    for md_file in md_files:
        print(f"Processing: {md_file.name}")
        total_tables += convert_file(md_file, output_dir, encoding)

    print(f"\nDone. Converted {total_tables} table(s) from {len(md_files)} file(s).")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
