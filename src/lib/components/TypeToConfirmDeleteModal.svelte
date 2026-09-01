<script lang="ts">
	const {
		open,
		title,
		description,
		confirmText = 'Delete',
		requireTyped = false,
		confirmPhrase = 'confirm',
		onClose,
		onConfirm
	}: {
		open: boolean;
		title: string;
		description: string;
		confirmText?: string;
		requireTyped?: boolean;
		confirmPhrase?: string;
		onClose: () => void;
		onConfirm: () => void;
	} = $props();

	let backdrop: HTMLDivElement | undefined = $state();
	let typed = $state('');

	$effect(() => {
		if (open) typed = '';
	});

	const canSubmit = $derived(!requireTyped || typed.trim().toLowerCase() === confirmPhrase.trim().toLowerCase());

	function close(): void {
		typed = '';
		onClose();
	}

	function onBackdropMouseDown(e: MouseEvent): void {
		if (e.target === backdrop) close();
	}

	function submit(e: Event): void {
		e.preventDefault();
		if (!canSubmit) return;
		onConfirm();
		close();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		bind:this={backdrop}
		class="fixed inset-0 z-[80] flex items-center justify-center bg-zinc-950/45 p-4 backdrop-blur-sm"
		onmousedown={onBackdropMouseDown}
		role="dialog"
		aria-modal="true"
		aria-labelledby="confirm-del-title"
		tabindex="-1"
	>
		<form
			class="w-full max-w-md rounded-3xl border border-white/70 bg-white p-6 shadow-2xl transition-all"
			onsubmit={submit}
		>
			<div class="flex items-center gap-3">
				<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-red-50 text-red-600 ring-1 ring-red-100">
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
					</svg>
				</div>
				<div>
					<h2 id="confirm-del-title" class="text-lg font-bold text-zinc-900">{title}</h2>
					<p class="text-xs text-zinc-500">This action cannot be undone.</p>
				</div>
			</div>

			<p class="mt-3 text-sm leading-relaxed text-zinc-600">{description}</p>

			{#if requireTyped}
				<p class="mt-4 text-xs font-medium text-zinc-500">
					Type <span class="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-zinc-800">{confirmPhrase}</span> to confirm.
				</p>
				<input
					type="text"
					bind:value={typed}
					autocomplete="off"
					class="mt-2 w-full rounded-xl border border-zinc-200 px-3 py-2.5 text-sm outline-none focus:border-red-400 focus:ring-4 focus:ring-red-500/15"
					placeholder={confirmPhrase}
				/>
			{/if}

			<div class="mt-6 flex justify-end gap-2">
				<button
					type="button"
					class="rounded-xl px-4 py-2.5 text-sm font-semibold text-zinc-600 transition hover:bg-zinc-100 active:scale-95"
					onclick={close}
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={!canSubmit}
					class="rounded-xl bg-red-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-red-500 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
				>
					{confirmText}
				</button>
			</div>
		</form>
	</div>
{/if}
