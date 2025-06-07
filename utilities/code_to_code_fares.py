from datetime import datetime
import urllib.request, json
import os
from dotenv import load_dotenv

load_dotenv()

def get_fares() -> dict:
    """
    Fetches the cost of rides between WMATA stations and returns a dictionary containing the fare information. Note that the API key must be set in the environment variable `WMATA_API_KEY`.
    
    Returns:
        dict: A dictionary where keys are (source station code, destination station code) tuples and values are the fare amounts in dollars. The fare amounts are categorized and stored as follows:
        ```python
        {
            'PeakTime': 2.9,
            'OffPeakTime': 2.5,
            'SeniorDisabled': 1.35
        }
        ```
    Raises:
        Exception: If the API request fails or the response is not as expected.
    """
    try:
        url = "https://api.wmata.com/Rail.svc/json/jSrcStationToDstStationInfo"

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
        
        fares = {}
        for fare in data['StationToStationInfos']:
            src_code = fare['SourceStation']
            dst_code = fare['DestinationStation']
            fare_amount = fare['RailFare']
            fares[(src_code, dst_code)] = fare_amount
        return fares
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Example usage
    fares = get_fares()
    if fares:
        # Save to JSON file with stringified tuple keys
        serializable_fares = {f"{src}-{dst}": fare for (src, dst), fare in fares.items()}
        to_save = {
            "last_updated": datetime.now().isoformat(),
            "fares": serializable_fares
        }
        with open('rail_fares.json', 'w') as f:
            json.dump(to_save, f, indent=4)
    else:
        print("Failed to retrieve fare data.")
