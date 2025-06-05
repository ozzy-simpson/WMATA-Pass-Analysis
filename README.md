# Metro Pass Breakeven Calculator

This tool helps you determine if your WMATA monthly pass is saving you money based on your actual card usage. It parses your WMATA card usage CSV and compares your total regular fares to the cost of your pass plus any additional charges.

## Features
- Parses WMATA card usage CSV files
- Fuzzy matches station names to codes
- Calculates regular fares for Metrorail and Metrobus
- Checks if you have broken even on your monthly pass
- What-if analysis for different pass costs/limits

## Requirements
- [WMATA API](https://developer.wmata.com) key (for station and fare data)
- [UV](https://docs.astral.sh/uv/getting-started/installation/)

## Installation
1. Clone this repository.
2. Create a `.env` file in the project root with your WMATA API key:
   ```env
   WMATA_API_KEY=your_api_key_here
   ```

## Basic Usage
1. Export your WMATA card usage as a CSV from the WMATA website (go to your card summary -> Use History (under the History section) -> select the usage data you want to analyze -> click Submit -> download the CSV by clicking Export To Excel).
2. Run the breakeven check:
   ```sh
   uv run main.py --csv={path/to/your_card_usage.csv} --cost={cost_of_your_monthly_pass}
   ```
   - `--csv`: Path to your card usage CSV file
   - `--cost`: The cost of your monthly pass (e.g., 108.00)

### Example
```sh
uv run main.py Card_Usage_06.01.25-06.30.25.csv 80
```

## What-if Analysis
If you want to perform a what-if analysis with different pass costs or limits, you can use the `--limit` flag to specify a different fare limit for the pass:
```sh
uv run main.py --csv={path/to/your_card_usage.csv} --cost={cost_of_your_monthly_pass} --limit={fare_limit}
```
### Example What-if Analysis
```sh
uv run main.py Card_Usage_06.01.25-06.30.25.csv 72 2.25
```

## Notes
- The script uses the WMATA API to fetch up-to-date fare and station information.
- Make sure your `.env` file contains a valid `WMATA_API_KEY`.
- Only Metrorail and Metrobus rides are considered in the calculation, and Metrobus Express fares are not differentiated from regular fares.
