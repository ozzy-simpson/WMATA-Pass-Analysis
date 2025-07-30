<script lang="ts">
	import passes from '$lib/passes.json';
	import { calculatePassSavings, type Ride } from '$lib/calculator';
	import stationMapping from '$lib/station_codes.json';

	let step = $state(1);
	let loading = $state(true);
	let files = $state<FileList | null>(null);
	let csvData = $state<string | null>(null);
	let fileValid = $state(true);
	let pass = $state('');
	let breakEven = $state(false);
	let savings = $state(0);
	let spent = $state(0);
	let cost = $state(0);
	let rides = $state<Ride[]>([]);
	let showRides = $state(false);

	const lastUpdate = new Date(stationMapping.last_updated).toLocaleDateString('en-US', {
		year: 'numeric',
		month: 'long',
		day: 'numeric'
	});

	// Check if the file is valid
	$effect(() => {
		fileValid = true;
		// Some simple checks
		if (!files || files.length !== 1 || !files[0].name.endsWith('.csv')) {
			fileValid = false;
			return;
		}

		// Check for required headers
		const headers = [
			'Time',
			'Description',
			'Operator',
			'Entry Location/ Bus Route',
			'Exit Location'
		];
		const reader = new FileReader();
		reader.readAsText(files[0]);
		reader.onload = () => {
			const content = reader.result as string;
			const lines = content.split('\n');
			if (lines.length < 2) {
				fileValid = false;
				return;
			}
			const headerLine = lines[0].split(',');
			fileValid = headers.every((header) => headerLine.includes(header));
			if (fileValid) csvData = content;
		};
	});

	// Check if a pass has been saved in localStorage
	$effect(() => {
		const savedPass = localStorage.getItem('selectedPass');
		if (savedPass) {
			pass = savedPass;
		}
	});

	// Save the selected pass to localStorage when it changes
	$effect(() => {
		if (pass) {
			localStorage.setItem('selectedPass', pass);
		} else {
			localStorage.removeItem('selectedPass');
		}
	});

	// Handle the analysis step
	$effect(() => {
		if (step === 4 && csvData && pass) {
			loading = true;
			// Get pass details
			const selectedPass = passes.find((p) => p.name === pass);
			if (!selectedPass) {
				console.error('Selected pass not found:', pass);
				loading = false;
				return;
			}

			const result = calculatePassSavings(
				csvData,
				selectedPass.price,
				selectedPass.fareLimit || Infinity
			);
			savings = result.savings;
			breakEven = result.brokeEven;
			spent = result.totalCost;
			cost = result.totalSpent;
			rides = result.rides || [];
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>WMATA Pass Analyzer</title>
</svelte:head>

<div class="step-container">
	<div class="step">
		{#if step == 1}
			<h1>🚇🏛️🌸🚍</h1>
			<h1>Welcome to the WMATA Pass Analyzer</h1>
			<p>
				Upload your SmarTrip card usage, select a pass, and see how much money you saved (or lost)
				with the pass!
			</p>
			<button onclick={() => step++}>Start Analysis</button>
		{:else if step == 2}
			<h1>🚇 Where have you been?</h1>
			<p>
				Upload a CSV of your Card Usage history. This can be found in your SmarTrip account, under
				your card's Use History (Export to Excel once you've selected the time period you wish to
				analyze).
			</p>
			<input type="file" accept=".csv" multiple={false} bind:files />
			<button onclick={() => step++} disabled={!files || !fileValid}>Next</button>
			{#if files && !fileValid}
				<p class="error">Please upload a valid card usage CSV file from your SmarTrip account.</p>
			{/if}
		{:else if step == 3}
			<h1>🎟️ Which pass did you purchase?</h1>
			<p>
				You can also select a different pass level than what you purchased to see how much you might
				have saved (or lost).
			</p>
			<select bind:value={pass}>
				<option value="" disabled selected>Select a pass</option>
				{#each passes as p (p.name)}
					<option value={p.name}>{p.name} - ${p.price.toFixed(2)}</option>
				{/each}
			</select>
			<button onclick={() => step++} disabled={!pass}>Next</button>
		{:else if step == 4 && loading}
			<h1>🧮 Calculating...</h1>
			<p>Please wait while we analyze your data.</p>
		{:else if step == 4 && !loading}
			{#if breakEven}
				<h1>
					🤑 You have saved <span class="savings">${savings.toFixed(2)}</span> with your pass!
				</h1>
				<div class="spending-breakdown">
					<div class="calculation-cards">
						<div class="spending-card total-spent">
							<div class="card-label">Total spent (with pass)</div>
							<div class="card-amount">${cost.toFixed(2)}</div>
						</div>
						<div class="calculation-operator">&minus;</div>
						<div class="spending-card without-pass">
							<div class="card-label">Would have spent (without pass)</div>
							<div class="card-amount">${spent.toFixed(2)}</div>
						</div>
						<div class="calculation-operator">=</div>
						<div class="spending-card savings-card">
							<div class="card-label">Your Savings</div>
							<div class="card-amount savings">${savings.toFixed(2)}</div>
						</div>
					</div>
				</div>
				<p>
					Why don't you go for a joy-ride? You could even <a
						href="https://www.reddit.com/r/washingtondc/comments/1kvtcs3/update_is_it_possible_to_swipe_in_and_out_of/"
						rel="noopener"
						target="_blank">visit every station</a
					> for free (just remember to tap in/out at each one)!
				</p>
			{:else}
				<h1>❌ You have not broken even with the pass.</h1>
				<div class="spending-breakdown">
					<div class="calculation-cards">
						<div class="spending-card total-spent">
							<div class="card-label">Total spent (with pass)</div>
							<div class="card-amount">${cost.toFixed(2)}</div>
						</div>
						<div class="calculation-operator">&minus;</div>
						<div class="spending-card without-pass">
							<div class="card-label">Would have spent (without pass)</div>
							<div class="card-amount">${spent.toFixed(2)}</div>
						</div>
						<div class="calculation-operator">=</div>
						<div class="spending-card loss-card">
							<div class="card-label">Additional Cost</div>
							<div class="card-amount break-even">${Math.abs(savings).toFixed(2)}</div>
						</div>
					</div>
				</div>
			{/if}

			{#if rides.length > 0}
				<div class="rides-section">
					<button class="toggle-rides" onclick={() => (showRides = !showRides)}>
						{showRides ? '🔼 Hide' : '🔽 Show'} Ride Details ({rides.length} rides)
					</button>

					{#if showRides}
						<div class="rides-table-container">
							<table class="rides-table">
								<thead class="bg-gray-100">
									<tr>
										<th>Entry Time</th>
										<th>Exit Time</th>
										<th>Type</th>
										<th>From</th>
										<th>To</th>
										<th>Fare</th>
									</tr>
								</thead>
								<tbody>
									{#each rides as ride (ride.entry_time)}
										<tr>
											<td
												>{ride.entry_time
													? ride.entry_time.toLocaleString('en-US', {
															dateStyle: 'short',
															timeStyle: 'short'
														})
													: ''}</td
											>
											<td
												>{ride.type == 'Metrobus'
													? '-'
													: ride.exit_time?.toLocaleString('en-US', {
															dateStyle: 'short',
															timeStyle: 'short'
														})}</td
											>
											<td>{ride.type}</td>
											<td
												>{ride.type == 'Metrobus'
													? '-'
													: stationMapping.codes[
															ride.entry_location as keyof typeof stationMapping.codes
														]}</td
											>
											<td
												>{ride.exit_location
													? stationMapping.codes[
															ride.exit_location as keyof typeof stationMapping.codes
														] || '-'
													: '-'}</td
											>
											<td>
												${ride.regular_cost.toFixed(2)}
												{#if ride.peak}
													<span
														style="background:#fbbf24;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.75em;margin-left:6px;"
														>Peak</span
													>
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>
			{/if}

			<button
				onclick={() => {
					step = 1;
					loading = true;
				}}>Restart</button
			>
		{/if}
	</div>
</div>
<footer class="footer">
	<p>
		Note that this tool is not affiliated with WMATA in any way. Data is processed locally in your
		browser and may not be 100% accurate.
	</p>
	<p>
		<strong>Limitations:</strong> Express Metrobus routes are not supported (the tool assumes all bus
		routes are $2.25). Reduced fares and other Metrobus-to-Metrobus or Metrobus-to-Metrorail/Metrorail-to-Metrobus
		transfers are not supported and thus no fare discounts are applied.
	</p>
	<p>Station, fare, and pass data as of {lastUpdate}.</p>
	<br />
	<p>
		built with ☕️ and ❤️ by <a
			href="https://ozzysimpson.com"
			target="_blank"
			rel="noopener"
			class="footer-link">ozzy simpson</a
		>
	</p>
</footer>

<style lang="postcss">
	@reference "tailwindcss";
	@tailwind base;

	@tailwind components;
	@tailwind utilities;

	.step-container {
		@apply flex min-h-screen flex-col items-center justify-center overflow-hidden bg-gray-100 p-4 sm:p-6 md:p-8 lg:p-10;
	}

	.step {
		@apply mx-auto w-full max-w-[940px] text-center;

		h1 {
			@apply mb-4 text-3xl font-bold;
		}

		p {
			@apply mb-4 text-lg text-gray-700;

			a {
				@apply text-blue-500 underline transition-colors hover:text-blue-600;
			}
		}

		.error {
			@apply text-sm text-red-500;
		}

		.spending-breakdown {
			@apply mb-5;

			.calculation-cards {
				@apply flex flex-col items-center justify-center gap-2 sm:flex-row sm:flex-wrap sm:gap-4 md:flex-nowrap;
			}

			.spending-card {
				@apply flex min-w-[140px] flex-col items-center rounded-lg border bg-white p-4 shadow-md md:min-w-[160px];
			}

			.total-spent {
				@apply border-blue-200 bg-blue-50;
			}

			.without-pass {
				@apply border-gray-200 bg-gray-50;
			}

			.savings-card {
				@apply border-green-200 bg-green-50;
			}

			.loss-card {
				@apply border-red-200 bg-red-50;
			}

			.card-label {
				@apply mb-2 text-center text-xs font-medium text-gray-600;
			}

			.card-amount {
				@apply text-xl font-bold text-gray-800;
			}

			.calculation-operator {
				@apply text-2xl font-bold text-gray-600;
			}

			.savings {
				@apply font-bold text-green-500 underline;
			}

			.break-even {
				@apply font-bold text-red-500 underline;
			}
		}

		.rides-section {
			@apply mt-6 w-full;
		}

		.toggle-rides {
			@apply mb-4 bg-gray-500 px-4 py-2 text-white transition-colors hover:bg-gray-600;
		}

		.rides-table-container {
			@apply mb-4 max-h-96 overflow-auto rounded border border-gray-300;
		}

		.rides-table {
			@apply w-full border-collapse text-left text-sm;

			th {
				@apply sticky top-0 bg-gray-100 px-3 py-2 font-semibold text-gray-700;
				border-bottom: 1px solid #e5e7eb;
			}

			td {
				@apply px-3 py-2 text-gray-600;
				border-bottom: 1px solid #f3f4f6;
			}

			tr:hover {
				@apply bg-gray-50;
			}
		}

		input[type='file'] {
			@apply mb-4 w-full max-w-full cursor-pointer border border-gray-300 bg-white p-2 text-gray-700;
			&::file-selector-button {
				@apply mr-4 cursor-pointer px-4 font-semibold transition-colors;
			}
			&::placeholder {
				@apply text-gray-50;
			}
		}

		select {
			@apply mb-4 w-full max-w-full cursor-pointer border border-gray-300 bg-white p-2 text-gray-700;
			option {
				@apply text-gray-700;
			}
			&:focus {
				@apply border-blue-500 outline-none;
			}
		}

		button {
			@apply bg-blue-500 px-4 py-2 text-white transition-colors disabled:opacity-50;
			&:not(:disabled):hover {
				@apply bg-blue-600;
			}
		}
	}

	footer {
		@apply mt-8 mb-8 w-full px-4 text-center text-xs text-gray-400;

		p {
			@apply mb-2;
		}

		a {
			@apply underline transition-colors hover:text-blue-500;
		}
	}
</style>
