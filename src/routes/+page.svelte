<script lang="ts">
	import passes from '$lib/passes.json';
	import { calculatePassSavings } from '$lib/calculator';

	let step = $state(1);
	let loading = $state(true);
	let files = $state<FileList | null>(null);
	let csvData = $state<string | null>(null);
	let fileValid = $state(true);
	let pass = $state('');
	let breakEven = $state(false);
	let savings = $state(0);

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
			loading = false;
		}
	});
</script>

<div class="step-container">
	<div class="step">
		{#if step == 1}
			<h1>🚇🚍🏛️</h1>
			<h1>Welcome to the WMATA Pass Analyzer</h1>
			<p>
				Simply upload your SmarTrip card usage, select a pass, and see how much money you saved (or
				lost) with the pass!
			</p>
			<button onclick={() => step++}>Start Analysis</button>
		{:else if step == 2}
			<h1>🚇 Where have you been?</h1>
			<p>
				This can be found in your SmarTrip account, under your card's Use History (Export to Excel).
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
			{:else}
				<h1>❌ You have not broken even with the pass.</h1>
				<p>
					You need to spend at least <span class="break-even">${savings.toFixed(2)}</span> more to break
					even.
				</p>
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
	<p>Station, fare, and pass data as of June 6, 2025.</p>
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
		@apply flex min-h-screen flex-col items-center justify-center bg-gray-100 p-4;

		@screen sm {
			@apply p-6;
		}

		@screen md {
			@apply p-8;
		}

		@screen lg {
			@apply p-10;
		}

		.step {
			@apply mx-auto text-center;

			h1 {
				@apply mb-4 text-3xl font-bold;
			}

			p {
				@apply mb-4 text-lg text-gray-700;
			}

			.error {
				@apply text-sm text-red-500;
			}

			.savings {
				@apply font-bold text-green-500 underline;
			}

			.break-even {
				@apply font-bold text-red-500 underline;
			}

			input[type='file'] {
				@apply mb-4 cursor-pointer border border-gray-300 bg-white p-2 text-gray-700;
				&::file-selector-button {
					@apply mr-4 cursor-pointer px-4 font-semibold transition-colors;
				}
				&::placeholder {
					@apply text-gray-50;
				}
			}

			select {
				@apply mb-4 cursor-pointer border border-gray-300 bg-white p-2 text-gray-700;
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
	}

	footer {
		@apply mt-8 mb-8 w-full px-4 text-center text-xs text-gray-400;

		a {
			@apply underline transition-colors hover:text-blue-500;
		}
	}
</style>
