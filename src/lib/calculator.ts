import fares from './rail_fares.json';
import stationMapping from './station_codes.json';
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

	// Get all station names
	const stationNames = Object.keys(stationMapping.stations);

	// Find the closest match using fuzzy search
	const match = search(stationName, stationNames, {
		keySelector: (name) => name,
		threshold: 0.8,
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
		if (hour >= 5 || hour < 21 || (hour === 21 && minute < 30)) return true;
	}
	return false;
}

export interface Ride {
	peak: boolean;
	type: string;
	entry_location: string;
	exit_location: string;
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
	for (let i = 0; i < rows.length; i++) {
		const row = rows[i];
		if (row['Operator'] === 'Metrobus') {
			rides.push({
				peak: isPeak(row['Time']),
				type: 'Metrobus',
				entry_location: fuzzyMatchStation(row['Entry Location/ Bus Route']),
				exit_location: '',
				regular_cost: 2.25
			});
		} else if (row['Operator'] === 'Metrorail' && row['Description'] === 'Exit') {
			// Try to find the previous entry row
			let entryRow = i > 0 ? rows[i - 1] : row;
			if (entryRow['Description'] !== 'Entry') entryRow = row;
			const entryCode = fuzzyMatchStation(row['Entry Location/ Bus Route']);
			const exitCode = fuzzyMatchStation(row['Exit Location']);
			const peak = isPeak(entryRow['Time']);
			rides.push({
				peak,
				type: 'Metrorail',
				entry_location: entryCode,
				exit_location: exitCode,
				regular_cost: getFare(entryCode, exitCode, peak)
			});
		}
	}
	return rides;
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
