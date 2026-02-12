# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MdTableToCSVTable is a single-script Python tool that reads Markdown files from `./input/`, extracts all tables, and writes each table as a separate CSV file to `./output/`.

## Running

```bash
/opt/anaconda3/envs/bochk/bin/python md_table_to_csv.py
```

## Architecture

Everything lives in `md_table_to_csv.py` with a clear pipeline:

1. **`find_tables(text)`** — groups consecutive `|`-prefixed lines into table blocks
2. **`parse_table(lines)`** — splits cells on `|`, strips whitespace, skips separator rows
3. **`convert_file(input_path, output_dir)`** — orchestrates read → parse → CSV write for one file
4. **`main()`** — scans `./input/*.md`, calls `convert_file` for each, prints summary

Output naming: `{original_filename}_table{n}.csv` (1-indexed per source file).
