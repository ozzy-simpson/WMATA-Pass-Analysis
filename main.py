from datetime import datetime
import fire
import pandas as pd
from rapidfuzz import fuzz, process
from utilities.code_to_code_fares import get_fares
from utilities.station_names_to_codes import get_mapping

NAMES_TO_CODES = get_mapping()
FARES = get_fares()

def fuzzy_match_station(station_name: str) -> str:
    """
    Fuzzy matches a station name to its most similar station code

    Args:
        station_name (str): The name of the station to match.
    Returns:
        str: The code of the matched station, or an empty string if no match is found.
    """
    if not station_name:
        return ""
    # Get all station names
    station_names = list(NAMES_TO_CODES.keys())

    # Find the best match using fuzzy matching
    best_match, score, *_ = process.extractOne(station_name, station_names, scorer=fuzz.ratio)
    
    if score > 80:
        return NAMES_TO_CODES[best_match]
    return station_name # if it doesn't match well, return the original name (just may fail later)

def is_peak(time: str) -> bool:
    """
    Determines if the ride is during peak hours (weekday between opening and 9:30pm).

    Args:
        time (str): Time in MM/DD/YY HH:MM am/pm format.
    Returns:
        bool: True if during peak hours, False otherwise.
    """
    time_obj = datetime.strptime(time, '%m/%d/%y %I:%M %p')
    
    # Peak hours: weekdays from open to 9:30 PM
    if time_obj.weekday() < 5:
        if time_obj.hour < 21 or (time_obj.hour == 21 and time_obj.minute < 30):
            return True
    return False

class Ride:
    def __init__(self, time, operator, entry_location, exit_location="", change=0.0):
        self.peak = is_peak(time)
        self.type = operator
        self.entry_location = fuzzy_match_station(entry_location)
        self.exit_location = fuzzy_match_station(exit_location)
        self.additional_cost = change
        self.regular_cost = self.calculate_regular_cost()
    
    def calculate_regular_cost(self) -> float:
        """
        Calculates the regular cost of the ride based on the type and peak status.
        
        Returns:
            float: Regular cost of the ride.
        """
        if self.type == 'Metrobus':
            return 2.25
        elif self.type == 'Metrorail':
            if not self.entry_location or not self.exit_location:
                return 0.0
            
            # Get fare based on entry and exit locations and peak status
            fare_key = (self.entry_location, self.exit_location)
            fare = FARES.get(fare_key, None)
            if fare is None:
                raise ValueError(f"No fare found for ride from {self.entry_location} to {self.exit_location}")
            if self.peak:
                return fare['PeakTime']
            return fare['OffPeakTime']
        
        return 0.0
            
    def __repr__(self):
        return f"Ride(type={self.type}, entry_location={self.entry_location}, exit_location={self.exit_location}, normal_cost={self.regular_cost}, additional_cost={self.additional_cost})"
    
    def __str__(self):
        return self.__repr__()

def parse_csv(path: str, limit: float) -> list[Ride]:
    """
    Parses the CSV file, checks for required columns, and creates Ride class instances.

    Args:
        path (str): Path to the CSV file.
        limit (float): Limit for the cost of rides, if applicable.
    Returns:
        rides (list[Ride]): List of Ride class instances.
    """
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except pd.errors.EmptyDataError:
        raise ValueError("The file is empty. Please provide a valid CSV file.")
    except pd.errors.ParserError:
        raise ValueError("Error parsing the CSV file. Please ensure it is formatted correctly.")
    
    # Check if the required columns are present
    required_columns = ['Time', 'Description', 'Operator', 'Entry Location/ Bus Route', 'Exit Location', 'Change (+/-)']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        
    # Reverse row order (ensures that we have an entry before an exit)
    df = df.iloc[::-1].reset_index(drop=True)

    # Filter out rows where Description is not 'Entry'/'Exit' and Operator is not 'Metrorail' or 'Metrobus' (we only care about these)
    df = df[(df['Description'].isin(['Entry', 'Exit'])) & (df['Operator'].isin(['Metrorail', 'Metrobus']))]

    rides = []
    for index, row in df.iterrows():
        if row['Operator'] == 'Metrobus':
            # Normalize cost
            cost = 0.0
            if row['Change (+/-)'].startswith('('):
                cost = float(row['Change (+/-)'].strip('($)'))
            elif row['Change (+/-)'].startswith('$') and row['Change (+/-)'] != '$0.00':
                cost = -float(row['Change (+/-)'].strip('$'))

            ride = Ride(
                time=row['Time'],
                operator='Metrobus',
                entry_location=row['Entry Location/ Bus Route'],
                exit_location="",
                change=cost
            )
        elif row['Operator'] == 'Metrorail' and row['Description'] == 'Exit':
            # Get the previous row for entry if available
            entry_row = df.iloc[index - 1] if index - 1 < len(df) and index - 1 >= 0 else None
            if entry_row is not None and entry_row['Description'] != 'Entry' and entry_row['Entry Location/ Bus Route'] != row['Entry Location/ Bus Route']:
                # If the previous row is not an entry, we just use the information from the current (exit) row
                entry_row = row

            # Normalize cost
            cost = 0.0
            if row['Change (+/-)'].startswith('('):
                cost = float(row['Change (+/-)'].strip('($)'))
            elif row['Change (+/-)'].startswith('$') and row['Change (+/-)'] != '$0.00':
                cost = -float(row['Change (+/-)'].strip('$'))

            ride = Ride(
                time=entry_row['Time'],
                operator='Metrorail',
                entry_location=row['Entry Location/ Bus Route'],
                exit_location=row['Exit Location'],
                change=cost
            )
        else:
            continue
        rides.append(ride)
        
    return rides

def check_pass(csv: str, cost: float, limit: float = None):
    """
    Checks if you've broken even on a WMATA monthly pass.

    Args:
        csv (str): Path to the card usage CSV.
        cost (float): Pass cost.
    Returns:
        None: Prints whether you've broken even or not.
    """

    rides = parse_csv(csv, limit)
    total_cost = sum(ride.regular_cost for ride in rides)

    if limit is None:
        # If no limit is provided, we just check if the total additional cost of rides is greater than or equal to the pass cost
        total_spent = sum(ride.additional_cost for ride in rides) + cost

        if total_cost >= total_spent:
            print(f"🤑 You have saved ${abs(total_spent - total_cost):.2f} with your pass!")
        else:
            print(f"❌ You have not broken even with the pass. You need to spend at least ${total_spent - total_cost:.2f} more to break even.")
    else:
        # If limit is set, we essentially perform a what-if analysis to see how much additional you would spend if you had a pass with a different limit
        total_spent = cost + sum((ride.regular_cost - limit) for ride in rides if ride.regular_cost > limit)

        if total_cost >= total_spent:
            print(f"🤑 You would save ${abs(total_spent - total_cost):.2f} with that pass!")
        else:
            print(f"❌ You would not break even with that pass. You'd need to spend at least ${total_spent - total_cost:.2f} more to break even.")

if __name__ == "__main__":
    fire.Fire(check_pass)
