# Metro Pass Analyzer Utilities

These utilities help you generate JSON files with the latest fare and station code data from the WMATA API, which are used by the main Metro Pass Analyzer script.

## Requirements

- [WMATA API](https://developer.wmata.com) key (for station and fare data)
- [UV](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

1. Clone this repository.
2. Create a `.env` file in the project root with your WMATA API key:
   ```env
   WMATA_API_KEY=your_api_key_here
   ```

## Run the Utilities

```console
$ uv run utilities/code_to_code_fares.py
```

This will generate a `rail_fares.json` file containing the latest fare data.

```console
$ uv run utilities/station_names_to_codes.py
```

This will generate a `station_codes.json` file containing the latest station codes and names.
