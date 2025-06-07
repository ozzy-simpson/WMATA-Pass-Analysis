from datetime import datetime
import urllib.request, json
import os
from dotenv import load_dotenv

load_dotenv()

def get_mapping() -> dict:
    """
    Fetches the list of WMATA stations and returns a dictionary mapping station names to their codes. Note that the API key must be set in the environment variable `WMATA_API_KEY`.
    
    Returns:
        dict: A dictionary where keys are station names and values are their corresponding codes.
    Raises:
        Exception: If the API request fails or the response is not as expected.
    """
    try:
        url = "https://api.wmata.com/Rail.svc/json/jStations"

        hdr = {
            # Request headers
            'Cache-Control': 'no-cache',
            'api_key': os.getenv('WMATA_API_KEY'),
        }

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)

        if response.getcode() != 200:
            raise Exception(f"Failed to fetch data: {response.getcode()}")

        data = json.loads(response.read().decode('utf-8'))
        
        # Create a dictionary to map station names to codes
        station_names_to_codes = {station['Name']: station['Code'] for station in data['Stations']}
        
        # Sort the dictionary by station names
        return dict(sorted(station_names_to_codes.items()))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Example usage
    station_dict = get_mapping()
    if station_dict:
        to_save = {
            "last_updated": datetime.now().isoformat(),
            "stations": station_dict
        }
        # Save to JSON file
        with open('station_codes.json', 'w') as f:
            json.dump(to_save, f, indent=4)
    else:
        print("Failed to retrieve station data.")
