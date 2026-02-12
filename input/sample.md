# Sample Markdown with Tables

This file demonstrates various Markdown tables for testing the converter.

## Employee Directory

| Name       | Department  | Location  | Start Date |
|------------|-------------|-----------|------------|
| Alice Wong | Engineering | New York  | 2023-01-15 |
| Bob Smith  | Marketing   | London    | 2022-06-01 |
| Carol Liu  | Engineering | Singapore | 2024-03-20 |
| Dave Park  | Sales       | Tokyo     | 2023-11-08 |

Some text between the tables to ensure they are detected as separate blocks.

## Quarterly Revenue

| Quarter | Revenue ($M) | Growth (%) | Region        |
|---------|--------------|------------|---------------|
| Q1 2024 | 12.5         | 3.2        | North America |
| Q2 2024 | 14.1         | 12.8       | North America |
| Q3 2024 | 13.8         | -2.1       | North America |
| Q4 2024 | 16.0         | 15.9       | North America |

## Notes

- This is not a table, just a list.
- The converter should ignore this section.

## Edge Cases Table

| Item | Value | Notes              |
|------|-------|--------------------|
| A    |       | empty value cell   |
| B    | 100   | normal row         |
| C    | 3.14  | decimal number     |
| D    | yes   | boolean-like value |
