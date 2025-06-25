import fares from './rail_fares.json';
import stationMapping from './station_codes.json';
import gateStationMapping from './gate_station.json';
import { search } from 'fast-fuzzy';

// Helper to parse CSV string into array of objects
function parseCSV(csv: string): Record<string, string>[] {
	const lines = csv.trim().split('\n');
	const headers = lines[0].split(',').map((h) => h.trim());
	return lines.slice(1).map((line) => {
		const values = line.split(',').map((v) => v.trim());
		const obj: Record<string, string> = {};
		headers.forEach((h, i) => (obj[h] = values[i] ?? ''));
		return obj;
	});
}

// Fuzzy match using simple string similarity (for browser, no rapidfuzz)
function fuzzyMatchStation(stationName: string): string {
	if (!stationName) return '';

	// If we have a direct mapping for the station name, use it
	if (gateStationMapping[stationName as keyof typeof gateStationMapping]) {
		return (
			stationMapping.stations[
				gateStationMapping[
					stationName as keyof typeof gateStationMapping
				] as keyof typeof stationMapping.stations
			] || ''
		);
	}

	// Get all station names
	const stationNames = Object.keys(stationMapping.stations);

	// Find the closest match using fuzzy search
	const match = search(stationName, stationNames, {
		keySelector: (name) => name,
		threshold: 0.75,
		limit: 1 // Only need the best match
	});

	if (match.length > 0) {
		// Return the station code for the best match
		return stationMapping.stations[match[0] as keyof typeof stationMapping.stations] || '';
	}
	// If no match found, return empty string
	return '';
}

function isPeak(time: string): boolean {
	// Expects MM/DD/YY HH:MM AM/PM
	const d = new Date(time);
	const weekday = d.getDay();
	const hour = d.getHours();
	const minute = d.getMinutes();
	// Peak: Mon-Fri, 5am to 9:30pm
	if (weekday >= 1 && weekday <= 5) {
		if ((hour >= 5 && hour < 21) || (hour === 21 && minute < 30)) return true;
	}
	return false;
}

export interface Ride {
	peak: boolean;
	type: string;
	entry_location: string;
	entry_time?: Date;
	exit_location: string;
	exit_time?: Date;
	regular_cost: number;
}

function getFare(entry: string, exit: string, peak: boolean): number {
	const fareKey = `${entry}-${exit}`;
	const fare = fares.fares[fareKey as keyof typeof fares.fares];
	if (!fare) return 0;
	return peak ? fare.PeakTime : fare.OffPeakTime;
}

function createRides(rows: Record<string, string>[]): Ride[] {
	const rides: Ride[] = [];
	// First, create our rides from the CSV rows
	for (let i = 0; i < rows.length; i++) {
		const row = rows[i];
		if (row['Operator'] === 'Metrobus') {
			rides.push({
				peak: isPeak(row['Time']),
				type: 'Metrobus',
				entry_location: fuzzyMatchStation(row['Entry Location/ Bus Route']),
				entry_time: new Date(row['Time']),
				exit_location: '',
				regular_cost: 2.25
			});
		} else if (row['Operator'] === 'Metrorail' && row['Description'] === 'Exit') {
			// Try to find the previous entry row
			let entryRow = i + 1 < rows.length ? rows[i + 1] : row;
			if (entryRow['Description'] !== 'Entry') entryRow = row;
			const entryCode = fuzzyMatchStation(row['Entry Location/ Bus Route']);
			const exitCode = fuzzyMatchStation(row['Exit Location']);
			const peak = isPeak(entryRow['Time']);
			rides.push({
				peak,
				type: 'Metrorail',
				entry_location: entryCode,
				entry_time: new Date(entryRow['Time']),
				exit_location: exitCode,
				exit_time: new Date(row['Time']),
				regular_cost: getFare(entryCode, exitCode, peak)
			});
		}
	}

	// Apply Farragut Crossing discount
	const newRides: Ride[] = [];
	for (let i = 0; i < rides.length; i++) {
		const ride = rides[i];
		// Deal with entry rides at a Farragut station
		if (
			ride.type === 'Metrorail' &&
			isFarragutStation(ride.entry_location) &&
			ride.entry_time !== undefined
		) {
			let foundTransfer = false;
			const oppositeFarragutStation = ride.entry_location === 'A02' ? 'C03' : 'A02';

			// Look for a previous ride that had an exit at the opposite Farragut station within 30 minutes
			for (let j = i + 1; j < rides.length; j++) {
				const prevRide = rides[j];

				if (
					prevRide.type !== 'Metrorail' ||
					!isFarragutStation(prevRide.exit_location) ||
					prevRide.exit_time === undefined
				)
					continue; // Skip non-rail, non-Farragut, or rides without exit time

				const timeDiff = (ride.entry_time.getTime() - prevRide.exit_time.getTime()) / (1000 * 60); // minutes

				if (timeDiff > 30) break; // Transfer was too long ago

				if (prevRide.exit_location === oppositeFarragutStation) {
					foundTransfer = true;
					newRides.push({
						...ride,
						peak: prevRide.peak,
						entry_location: prevRide.entry_location,
						entry_time: prevRide.entry_time,
						regular_cost: getFare(prevRide.entry_location, ride.exit_location, prevRide.peak)
					});

					// Remove the previous ride since it was used for the transfer
					rides.splice(j, 1);
					break;
				}
			}

			if (!foundTransfer) newRides.push(ride); // If no transfer found, keep the original ride
		} else newRides.push(ride); // For all other rides, just add them as is
	}
	return newRides;
}

function isFarragutStation(station: string): boolean {
	// Get all station codes that start with 'Farragut'
	const farragutCodes = ['A02', 'C03'];
	return farragutCodes.includes(station);
}

export function calculatePassSavings(
	csv: string,
	passCost: number,
	passLimit: number
): { totalCost: number; totalSpent: number; savings: number; brokeEven: boolean } {
	const rows = parseCSV(csv);
	const rides = createRides(rows);

	const totalCost = rides.reduce((sum, r) => sum + r.regular_cost, 0);
	const totalSpent = rides.reduce(
		(sum, r) => sum + (r.regular_cost > passLimit ? r.regular_cost - passLimit : 0),
		passCost
	);
	const savings = totalCost - totalSpent;
	return {
		totalCost,
		totalSpent,
		savings: Math.abs(savings),
		brokeEven: totalCost >= totalSpent
	};
}
