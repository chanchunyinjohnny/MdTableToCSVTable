"""
Markdown Table to CSV Converter
================================

Reads all .md files from the ./input/ directory, extracts every Markdown table
found in each file, and writes each table as a separate CSV file in ./output/.

Usage:
    python md_table_to_csv.py

Output naming convention:
    {original_filename}_table1.csv, {original_filename}_table2.csv, ...

Supports two table formats:

1. Standard Markdown pipe tables:

    | Name  | Age | City     |
    |-------|-----|----------|
    | Alice | 30  | New York |

2. Unicode box-drawing tables:

    ┌───────┬─────┬──────────┐
    │ Name  │ Age │ City     │
    ├───────┼─────┼──────────┤
    │ Alice │ 30  │ New York │
    └───────┴─────┴──────────┘

Separator/border rows are detected and excluded from the CSV output.
"""

import csv
import re
import sys
from pathlib import Path

# Directories are relative to the script's location
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"

# Characters that mark the start of a table line:
#   - '|'  for standard Markdown pipe tables
#   - '│'  for box-drawing data rows
#   - '┌'  for box-drawing top border
#   - '├'  for box-drawing mid separator
#   - '└'  for box-drawing bottom border
TABLE_LINE_STARTS = ("|", "│", "┌", "├", "└")

# Box-drawing characters used in borders and separators (no text content)
BOX_BORDER_CHARS = set("┌┐└┘├┤┬┴┼─│")


def find_tables(text: str) -> list[list[str]]:
    """
    Scan markdown text and group consecutive table lines into blocks.

    A table line is any line whose stripped form starts with a pipe '|' or
    a Unicode box-drawing character ('│', '┌', '├', '└').  Consecutive table
    lines are grouped into one block.  Non-table lines (blank lines, prose,
    headings) act as block boundaries.

    Args:
        text: The full markdown file content as a string.

    Returns:
        A list of table blocks. Each block is a list of raw line strings.
    """
    tables = []
    current_block = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped and stripped[0] in TABLE_LINE_STARTS:
            current_block.append(stripped)
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
    (box-drawing) as the cell delimiter.

    Leading and trailing empty strings (from the outer delimiters) are removed.
    Examples:
        "| Alice | 30 |"   →  ["Alice", "30"]
        "│ Alice │ 30 │"   →  ["Alice", "30"]
    """
    # Choose delimiter based on which character is present
    delimiter = "│" if "│" in line else "|"
    cells = line.split(delimiter)

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


def convert_file(input_path: Path, output_dir: Path) -> int:
    """
    Read a single Markdown file, extract all tables, and write each as CSV.

    Each table is written to a separate file named:
        {stem}_table{n}.csv   (n starts at 1)

    If the file contains no tables, nothing is written.

    Args:
        input_path: Path to the .md file.
        output_dir:  Directory where CSV files will be created.

    Returns:
        The number of tables successfully converted.
    """
    text = input_path.read_text(encoding="utf-8")
    raw_tables = find_tables(text)

    if not raw_tables:
        print(f"  No tables found in {input_path.name}")
        return 0

    tables_written = 0
    for idx, raw_table in enumerate(raw_tables, start=1):
        rows = parse_table(raw_table)
        if not rows:
            continue

        output_name = f"{input_path.stem}_table{idx}.csv"
        output_path = output_dir / output_name

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        tables_written += 1
        print(f"  Wrote {output_path.name}  ({len(rows)} rows, {len(rows[0])} columns)")

    return tables_written


def main() -> None:
    """
    Entry point: scan ./input/ for .md files and convert all tables to CSV.
    """
    # Create input and output directories if they don't exist
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted(INPUT_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {INPUT_DIR}")
        print("Place your .md files in the ./input/ directory and run again.")
        sys.exit(1)

    print(f"Scanning {len(md_files)} markdown file(s) in {INPUT_DIR}\n")

    total_tables = 0
    for md_file in md_files:
        print(f"Processing: {md_file.name}")
        total_tables += convert_file(md_file, OUTPUT_DIR)

    print(f"\nDone. Converted {total_tables} table(s) from {len(md_files)} file(s).")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
