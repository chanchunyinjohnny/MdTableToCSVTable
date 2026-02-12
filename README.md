# MdTableToCSVTable

A Python command-line tool that converts Markdown tables into CSV files.

## Requirements

- Python 3.11+
- No third-party dependencies (uses only the Python standard library)

## Quick Start

1. Place your `.md` files in the `./input/` directory.
2. Run the script:

```bash
python md_table_to_csv.py
```

3. Find the generated CSV files in the `./output/` directory.

## How It Works

The script scans every `.md` file in `./input/`, detects all Markdown tables, and writes each table as a separate CSV file to `./output/`.

### Supported Table Format

Standard Markdown tables with pipe (`|`) delimiters and a separator row:

```markdown
| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | New York |
| Bob   | 25  | London   |
```

Alignment syntax in separator rows (`:---`, `:---:`, `---:`) is also handled correctly.

### Output Naming

Each table gets its own CSV file, named after the source file and table order:

```
{filename}_table1.csv
{filename}_table2.csv
...
```

For example, a file called `report.md` containing 2 tables produces:

```
output/report_table1.csv
output/report_table2.csv
```

## Example

Given `input/sample.md`:

```markdown
## Employee Directory

| Name       | Department  | Location  | Start Date |
|------------|-------------|-----------|------------|
| Alice Wong | Engineering | New York  | 2023-01-15 |
| Bob Smith  | Marketing   | London    | 2022-06-01 |

## Quarterly Revenue

| Quarter | Revenue ($M) | Growth (%) |
|---------|--------------|------------|
| Q1 2024 | 12.5         | 3.2        |
| Q2 2024 | 14.1         | 12.8       |
```

Running the script:

```
$ python md_table_to_csv.py
Scanning 1 markdown file(s) in ./input

Processing: sample.md
  Wrote sample_table1.csv  (3 rows, 4 columns)
  Wrote sample_table2.csv  (3 rows, 3 columns)

Done. Converted 2 table(s) from 1 file(s).
Output directory: ./output
```

Output `output/sample_table1.csv`:

```csv
Name,Department,Location,Start Date
Alice Wong,Engineering,New York,2023-01-15
Bob Smith,Marketing,London,2022-06-01
```

## Project Structure

```
MdTableToCSVTable/
├── md_table_to_csv.py   # Main converter script
├── input/               # Place .md files here
├── output/              # Generated CSV files appear here
├── LICENSE              # MIT License
└── README.md
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
