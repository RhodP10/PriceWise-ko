<script lang="ts">
	import { recipeStore, restoreRecipe, permanentlyDeleteRecipe } from '$lib/state/recipes.svelte';

	const { open, onClose }: { open: boolean; onClose: () => void } = $props();

	let backdrop: HTMLDivElement | undefined = $state();
	let pendingPermDelete = $state<string | null>(null);

	const archived = $derived(
		[...recipeStore.deletedRecipes].sort((a, b) => {
			return new Date(b.deletedAt ?? 0).getTime() - new Date(a.deletedAt ?? 0).getTime();
		})
	);

	function formatDate(iso: string | undefined): string {
		if (!iso) return '—';
		return new Intl.DateTimeFormat(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(new Date(iso));
	}

	function onBackdropMouseDown(e: MouseEvent): void {
		if (e.target === backdrop) {
			pendingPermDelete = null;
			onClose();
		}
	}

	function handleRestore(id: string): void {
		restoreRecipe(id);
	}

	function askPermDelete(id: string): void {
		pendingPermDelete = id;
	}

	function confirmPermDelete(): void {
		if (pendingPermDelete) {
			permanentlyDeleteRecipe(pendingPermDelete);
			pendingPermDelete = null;
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		bind:this={backdrop}
		class="fixed inset-0 z-[70] flex items-start justify-center overflow-y-auto bg-zinc-950/50 p-4 pt-16 backdrop-blur-sm"
		onmousedown={onBackdropMouseDown}
		role="dialog"
		aria-modal="true"
		aria-labelledby="archive-title"
		tabindex="-1"
	>
		<div class="w-full max-w-2xl rounded-3xl border border-zinc-200 bg-white shadow-2xl">
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-zinc-100 px-6 py-5">
				<div class="flex items-center gap-3">
					<div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 ring-1 ring-amber-100">
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8M10 12v4m4-4v4"/>
						</svg>
					</div>
					<div>
						<h2 id="archive-title" class="text-lg font-bold text-zinc-900">Recipe Archive</h2>
						<p class="text-xs text-zinc-500">
							{archived.length === 0 ? 'No deleted recipes' : `${archived.length} deleted recipe${archived.length === 1 ? '' : 's'}`}
						</p>
					</div>
				</div>
				<button
					type="button"
					class="flex h-9 w-9 items-center justify-center rounded-xl text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
					onclick={onClose}
					aria-label="Close archive"
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			<!-- Body -->
			<div class="px-6 py-5">
				{#if archived.length === 0}
					<div class="flex flex-col items-center justify-center py-16 text-center">
						<div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-zinc-50 shadow-inner">
							<svg class="h-8 w-8 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8"/>
							</svg>
						</div>
						<p class="font-semibold text-zinc-500">Archive is empty</p>
						<p class="mt-1 text-xs text-zinc-400">Deleted recipes will appear here so you can restore them.</p>
					</div>
				{:else}
					<ul class="space-y-3">
						{#each archived as recipe (recipe.id)}
							<li class="group relative overflow-hidden rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-3.5 transition hover:border-zinc-200 hover:bg-white hover:shadow-sm">
								<div class="flex items-center gap-3">
									<!-- Icon -->
									<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-zinc-200/60 text-zinc-500">
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/>
											<path stroke-linecap="round" stroke-linejoin="round" d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/>
										</svg>
									</div>

									<!-- Info -->
									<div class="min-w-0 flex-1">
										<p class="truncate font-semibold text-zinc-800">{recipe.name}</p>
										<div class="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px] text-zinc-400">
											<span>{recipe.ingredientLines.length} ingredient{recipe.ingredientLines.length !== 1 ? 's' : ''}</span>
											<span>·</span>
											<span>{recipe.otherLines.length} other cost{recipe.otherLines.length !== 1 ? 's' : ''}</span>
											<span>·</span>
											<span>Deleted {formatDate(recipe.deletedAt)}</span>
										</div>
									</div>

									<!-- Actions -->
									<div class="flex shrink-0 items-center gap-2">
										<button
											id="restore-recipe-{recipe.id}"
											type="button"
											class="flex items-center gap-1.5 rounded-xl bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200/60 transition hover:bg-emerald-100 hover:ring-emerald-300 active:scale-95"
											onclick={() => handleRestore(recipe.id)}
											title="Restore recipe"
										>
											<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
												<path stroke-linecap="round" stroke-linejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3"/>
											</svg>
											Restore
										</button>
										<button
											id="perm-delete-recipe-{recipe.id}"
											type="button"
											class="flex h-8 w-8 items-center justify-center rounded-xl text-zinc-400 ring-1 ring-transparent transition hover:bg-red-50 hover:text-red-600 hover:ring-red-100 active:scale-95"
											onclick={() => askPermDelete(recipe.id)}
											title="Permanently delete"
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
											</svg>
										</button>
									</div>
								</div>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			<!-- Footer note -->
			{#if archived.length > 0}
				<div class="border-t border-zinc-100 px-6 py-4">
					<p class="text-center text-[11px] text-zinc-400">
						Restored recipes reappear in your active recipes list. Permanently deleted recipes cannot be recovered.
					</p>
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- Permanent Delete Confirmation -->
{#if pendingPermDelete !== null}
	{@const target = archived.find((r) => r.id === pendingPermDelete)}
	<div
		class="fixed inset-0 z-[80] flex items-center justify-center bg-zinc-950/50 p-4 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
	>
		<div class="w-full max-w-md rounded-3xl border border-white/70 bg-white p-6 shadow-2xl">
			<div class="flex items-center gap-3">
				<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-red-50 text-red-600 ring-1 ring-red-100">
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
					</svg>
				</div>
				<div>
					<h3 class="text-lg font-bold text-zinc-900">Permanently delete?</h3>
					<p class="text-xs text-zinc-500">This action cannot be undone.</p>
				</div>
			</div>
			<p class="mt-4 text-sm leading-relaxed text-zinc-600">
				<strong class="text-zinc-800">"{target?.name}"</strong> will be permanently removed. You will not be able to restore it.
			</p>
			<div class="mt-6 flex justify-end gap-2">
				<button
					type="button"
					class="rounded-xl px-4 py-2.5 text-sm font-semibold text-zinc-600 transition hover:bg-zinc-100 active:scale-95"
					onclick={() => (pendingPermDelete = null)}
				>
					Cancel
				</button>
				<button
					type="button"
					id="confirm-perm-delete-btn"
					class="rounded-xl bg-red-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-red-500 active:scale-95"
					onclick={confirmPermDelete}
				>
					Delete forever
				</button>
			</div>
		</div>
	</div>
{/if}
