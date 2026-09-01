<script lang="ts">
	import type { ChannelMarketplace } from '$lib/types/recipe';
	import type {
		CatalogRowForImport,
		MarketplaceImportPatch,
		MarketplaceListingSubmitResult,
		ShopeeVariantOption
	} from '$lib/utils/marketplaceJsonImport';
	import {
		parseLazadaProductJson,
		parseShopeeItemGetJson
	} from '$lib/utils/marketplaceJsonImport';
	import {
		getPriceWiseBookmarkletCode,
		marketplaceGuideTitle,
		parseShopeeProductUrl,
		shopeeItemGetApiUrl
	} from '$lib/utils/marketplaceUrlHints';
	import { formatPhp } from '$lib/utils/numberFormat';

	const {
		open,
		initialUrl,
		marketplace,
		channelLabel,
		localRow,
		onSubmitListing,
		onApplyImport,
		onClose
	}: {
		open: boolean;
		initialUrl: string;
		marketplace: ChannelMarketplace;
		channelLabel: string;
		localRow: CatalogRowForImport | null;
		/** Save URL + run Playwright scrape via backend, then fill landed pricing */
		onSubmitListing: (url: string) => Promise<MarketplaceListingSubmitResult>;
		onApplyImport: (patch: MarketplaceImportPatch, listingUrl: string) => void;
		onClose: () => void;
	} = $props();

	let backdrop: HTMLDivElement | undefined = $state();
	let draftUrl = $state('');
	let copyFeedback = $state('');
	let pasteJson = $state('');
	let importError = $state('');
	let importOk = $state('');
	let syncSubmitting = $state(false);
	let syncError = $state('');
	/** Shopee multi-SKU: same JSON, user must pick Ceremonial / Culinary / etc. */
	let shopeeVariantBody = $state<{ bodyJson: string; variants: ShopeeVariantOption[] } | null>(null);

	const bookmarkletHref = $derived(getPriceWiseBookmarkletCode());

	$effect(() => {
		if (open) {
			draftUrl = initialUrl;
			pasteJson = '';
			importError = '';
			importOk = '';
			syncError = '';
			syncSubmitting = false;
			shopeeVariantBody = null;
		}
	});

	const shopeeParsed = $derived(marketplace === 'shopee' ? parseShopeeProductUrl(draftUrl) : null);
	const shopeeApiUrl = $derived(shopeeParsed ? shopeeItemGetApiUrl(shopeeParsed) : null);

	function close(): void {
		copyFeedback = '';
		importError = '';
		importOk = '';
		syncError = '';
		shopeeVariantBody = null;
		onClose();
	}

	function onBackdropMouseDown(e: MouseEvent): void {
		if (e.target === backdrop) close();
	}

	async function submit(e: Event): Promise<void> {
		e.preventDefault();
		syncError = '';
		shopeeVariantBody = null;
		syncSubmitting = true;
		try {
			const result = await onSubmitListing(draftUrl.trim());
			if (result.kind === 'shopee_variants') {
				shopeeVariantBody = {
					bodyJson: result.bodyJson,
					variants: result.variants
				};
				return;
			}
			if (result.kind === 'error') {
				syncError = result.message ?? 'Sync failed.';
				return;
			}
			close();
		} finally {
			syncSubmitting = false;
		}
	}

	function applyShopeeVariantChoice(v: ShopeeVariantOption): void {
		importError = '';
		importOk = '';
		if (!localRow || !shopeeVariantBody) return;
		const parsed = parseShopeeItemGetJson(shopeeVariantBody.bodyJson, localRow, {
			by: 'index',
			index: v.index
		});
		if (!parsed.ok) {
			importError = parsed.error;
			return;
		}
		onApplyImport(parsed.patch, draftUrl.trim());
		shopeeVariantBody = null;
		importOk = parsed.productName ? `Imported · ${parsed.productName}` : 'Imported marketplace pricing into this row.';
		pasteJson = '';
		close();
	}

	function applyJsonImport(): void {
		importError = '';
		importOk = '';
		shopeeVariantBody = null;
		if (!localRow) {
			importError = 'Missing catalog row.';
			return;
		}
		const trimmed = pasteJson.trim();
		if (!trimmed) {
			importError = 'Paste JSON first (or use the Quick Grabber bookmarklet).';
			return;
		}

		// Try Shopee parser
		if (marketplace === 'shopee') {
			const sp = parseShopeeItemGetJson(trimmed, localRow);
			if (sp.ok) {
				onApplyImport(sp.patch, draftUrl.trim());
				importOk = sp.productName ? `Imported · ${sp.productName}` : 'Imported marketplace pricing into this row.';
				pasteJson = '';
				return;
			}
			if (sp.needVariant === true) {
				shopeeVariantBody = {
					bodyJson: trimmed,
					variants: sp.variants
				};
				importError = '';
				return;
			}
			// Fallback check if it's general payload
			const lp = parseLazadaProductJson(trimmed, localRow);
			if (lp.ok) {
				onApplyImport(lp.patch, draftUrl.trim());
				importOk = lp.productName ? `Imported · ${lp.productName}` : 'Imported marketplace pricing into this row.';
				pasteJson = '';
				return;
			}
			importError = sp.error;
			return;
		}

		// Lazada parser
		const lp = parseLazadaProductJson(trimmed, localRow);
		if (!lp.ok) {
			// Fallback check if it's Shopee format
			const sp = parseShopeeItemGetJson(trimmed, localRow);
			if (sp.ok) {
				onApplyImport(sp.patch, draftUrl.trim());
				importOk = sp.productName ? `Imported · ${sp.productName}` : 'Imported marketplace pricing into this row.';
				pasteJson = '';
				return;
			}
			importError = lp.error;
			return;
		}
		onApplyImport(lp.patch, draftUrl.trim());
		importOk = lp.productName ? `Imported · ${lp.productName}` : 'Imported marketplace pricing into this row.';
		pasteJson = '';
	}

	async function copyText(kind: string, text: string): Promise<void> {
		try {
			await navigator.clipboard.writeText(text);
			copyFeedback = kind;
			setTimeout(() => {
				copyFeedback = '';
			}, 2200);
		} catch {
			copyFeedback = 'copy_failed';
			setTimeout(() => {
				copyFeedback = '';
			}, 3200);
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		bind:this={backdrop}
		class="fixed inset-0 z-[70] flex items-center justify-center bg-zinc-950/40 p-4 backdrop-blur-sm"
		onmousedown={onBackdropMouseDown}
		role="dialog"
		aria-modal="true"
		aria-labelledby="scrape-help-title"
		tabindex="-1"
	>
		<form
			class="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-3xl border border-white/60 bg-white/95 p-6 shadow-2xl shadow-zinc-900/10 backdrop-blur-xl"
			onsubmit={submit}
		>
			<div class="flex items-start justify-between gap-3">
				<div>
					<h2 id="scrape-help-title" class="text-lg font-semibold tracking-tight text-zinc-900">
						Sync listing ({channelLabel})
					</h2>
					<p class="mt-1 text-sm text-zinc-500">
						Paste the product link and click <strong class="font-medium text-zinc-700">Save &amp; sync</strong>. PriceWise
						will extract live landed prices and package specs.
					</p>
				</div>
				<button type="button" class="rounded-xl p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700" onclick={close} aria-label="Close">
					×
				</button>
			</div>

			<div
				class="mt-4 rounded-2xl border px-4 py-3 text-sm {marketplace === 'shopee'
					? 'border-orange-200 bg-orange-50/80 text-orange-950'
					: 'border-sky-200 bg-sky-50/80 text-sky-950'}"
			>
				<p class="font-semibold">{marketplaceGuideTitle(marketplace)}</p>
				<p class="mt-1 text-xs opacity-90">
					Supports desktop product links, mobile links (e.g. <code class="rounded bg-white/70 px-1 py-0.5 text-xs">ph.shp.ee</code>, <code class="rounded bg-white/70 px-1 py-0.5 text-xs">s.lazada</code>), and direct URL imports.
				</p>
			</div>

			<!-- 1-Click Bookmarklet Helper Callout -->
			<div class="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/60 p-3.5 text-xs text-emerald-950">
				<div class="flex items-center justify-between gap-2">
					<div class="flex items-center gap-2 font-bold text-emerald-900">
						<span class="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600 text-[10px] text-white">✨</span>
						<span>1-Click PriceWise Quick Grabber</span>
					</div>
					<a
						href={bookmarkletHref}
						class="rounded-xl bg-emerald-600 px-3 py-1 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-500 active:scale-95"
						title="Drag this button to your Bookmarks Bar"
						onclick={(e) => {
							// If clicked on desktop, show drag hint or copy
							if (!e.defaultPrevented) {
								void copyText('bookmarklet', bookmarkletHref);
							}
						}}
					>
						⚡ Grabber Bookmarklet
					</a>
				</div>
				<p class="mt-1.5 text-[11px] leading-relaxed text-emerald-800">
					Drag the button above to your browser&apos;s Bookmarks bar. When viewing any product on Shopee or Lazada, click it to instantly copy product data, then paste it below. 100% bypasses cloud captchas!
				</p>
			</div>

			{#if copyFeedback}
				<p class="mt-3 text-center text-xs font-medium text-emerald-700" role="status">
					{copyFeedback === 'copy_failed'
						? 'Clipboard unavailable — copy manually.'
						: copyFeedback === 'bookmarklet'
							? 'Bookmarklet code copied to clipboard!'
							: copyFeedback === 'api'
								? 'API URL copied.'
								: copyFeedback === 'listing'
									? 'Listing URL copied.'
									: 'Copied.'}
				</p>
			{/if}

			<label class="mt-4 block">
				<span class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Product / listing URL</span>
				<input
					type="url"
					bind:value={draftUrl}
					placeholder="https://…"
					class="mt-1.5 w-full rounded-2xl border border-zinc-200 bg-white/80 px-4 py-3 text-sm outline-none ring-emerald-500/0 transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/15"
				/>
			</label>

			{#if syncError}
				<div class="mt-3 rounded-2xl bg-rose-50 p-3.5 text-sm text-rose-800 ring-1 ring-rose-200" role="alert">
					<p class="font-semibold">{syncError}</p>
					<p class="mt-1 text-xs text-rose-700">
						Tip: If the marketplace blocked cloud scraping, paste the product data into <strong>Quick Paste</strong> below or use the <strong>Quick Grabber Bookmarklet</strong>.
					</p>
				</div>
			{/if}

			{#if marketplace === 'shopee' && shopeeVariantBody}
				<div
					class="mt-4 rounded-2xl border border-violet-200 bg-violet-50/95 px-4 py-3 text-sm text-violet-950 shadow-sm"
					role="region"
					aria-label="Choose Shopee variant"
				>
					<p class="font-semibold text-violet-950">Choose which option to price</p>
					<p class="mt-1 text-[13px] leading-snug text-violet-900/85">
						For example <strong>Ceremonial</strong> vs <strong>Culinary</strong> use different list prices. We add the
						listing&apos;s shipping from the same data after you pick.
					</p>
					<div class="mt-3 flex flex-wrap gap-2">
						{#each shopeeVariantBody.variants as v}
							<button
								type="button"
								class="rounded-xl bg-white px-4 py-2.5 text-left text-sm font-semibold text-violet-950 shadow-sm ring-1 ring-violet-300 transition hover:bg-violet-100"
								onclick={() => applyShopeeVariantChoice(v)}
							>
								{v.name}
								<span class="block text-[13px] font-medium text-violet-700">List {formatPhp(v.pricePeso)}</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}

			<div class="mt-6 flex flex-wrap justify-end gap-2">
				<button
					type="button"
					class="rounded-2xl px-4 py-2.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100"
					onclick={close}
					disabled={syncSubmitting}
				>
					Cancel
				</button>
				<button
					type="submit"
					class="inline-flex items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
					disabled={syncSubmitting}
				>
					{#if syncSubmitting}
						<span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" aria-hidden="true"></span>
						Syncing…
					{:else}
						Save &amp; sync listing
					{/if}
				</button>
			</div>

			<details class="mt-6 rounded-2xl border border-dashed border-zinc-300 bg-zinc-50/90 px-4 py-3">
				<summary class="cursor-pointer text-sm font-semibold text-zinc-700">Quick Paste &amp; Manual Import</summary>
				<p class="mt-2 text-xs leading-snug text-zinc-600">
					Paste JSON copied from the Quick Grabber bookmarklet, DevTools Network tab, or raw product specs.
				</p>

				<label class="mt-3 block">
					<span class="sr-only">Raw JSON</span>
					<textarea
						bind:value={pasteJson}
						rows="4"
						placeholder="Paste copied JSON here..."
						class="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 font-mono text-[11px] leading-relaxed text-zinc-800 outline-none focus:border-zinc-400 focus:ring-2 focus:ring-zinc-400/20"
					></textarea>
				</label>
				{#if importError}
					<p class="mt-2 text-sm text-rose-700" role="alert">{importError}</p>
				{/if}
				{#if importOk}
					<p class="mt-2 text-sm font-medium text-emerald-800" role="status">{importOk}</p>
				{/if}
				<button
					type="button"
					class="mt-3 rounded-xl bg-zinc-800 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
					disabled={!localRow}
					onclick={applyJsonImport}
				>
					Apply pasted data
				</button>
			</details>
		</form>
	</div>
{/if}
