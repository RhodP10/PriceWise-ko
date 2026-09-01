import type { ChannelMarketplace } from '$lib/types/recipe';

/** Parsed Shopee listing IDs from a product URL. */
export type ShopeeIds = { shopId: string; itemId: string; origin: string };

/**
 * Extract shop/item IDs from a Shopee product URL (desktop or mobile path).
 */
export function parseShopeeProductUrl(raw: string): ShopeeIds | null {
	const trimmed = raw.trim();
	if (!trimmed) return null;
	let url: URL;
	try {
		url = new URL(trimmed.startsWith('http') ? trimmed : `https://${trimmed}`);
	} catch {
		return null;
	}
	const host = url.hostname.toLowerCase();
	if (!host.includes('shopee.') && !host.includes('shp.ee')) return null;

	const path = url.pathname.replace(/\/$/, '');
	let m = path.match(/[-.]i\.(\d+)\.(\d+)/);
	if (!m) m = path.match(/\/product\/(\d+)\/(\d+)/);
	if (!m) return null;
	const [, shopId, itemId] = m;
	const origin = `${url.protocol}//${url.host}`;
	return { shopId, itemId, origin };
}

/** Public item JSON endpoint used by Shopee web app. */
export function shopeeItemGetApiUrl(ids: ShopeeIds): string {
	const q = new URLSearchParams({ itemid: ids.itemId, shopid: ids.shopId });
	return `${ids.origin}/api/v4/item/get?${q.toString()}`;
}

export function marketplaceGuideTitle(channel: ChannelMarketplace): string {
	return channel === 'shopee'
		? 'Shopee: Instant Sync & Quick Import'
		: 'Lazada: Instant Sync & Quick Import';
}

/**
 * Generates a 1-click PriceWise Grabber bookmarklet code.
 * When run on a Shopee or Lazada product page, it grabs the product title, price, and details
 * and copies the clean JSON to the clipboard for instant 1-click pasting into PriceWise.
 */
export function getPriceWiseBookmarkletCode(): string {
	return `javascript:(function(){
		try {
			var title = (document.querySelector('h1') || {}).innerText || (document.querySelector('meta[property="og:title"]') || {}).content || document.title;
			var price = null;
			var metaP = document.querySelector('meta[property="product:price:amount"]') || document.querySelector('meta[property="og:price:amount"]');
			if (metaP && metaP.content) price = parseFloat(metaP.content.replace(/,/g, ''));
			if (!price) {
				var ld = document.querySelectorAll('script[type="application/ld+json"]');
				for (var i=0; i<ld.length; i++) {
					try {
						var j = JSON.parse(ld[i].textContent);
						var nodes = Array.isArray(j) ? j : [j];
						for (var k=0; k<nodes.length; k++) {
							var n = nodes[k];
							if (n && n.offers) {
								var o = Array.isArray(n.offers) ? n.offers[0] : n.offers;
								if (o && o.price) { price = parseFloat(String(o.price).replace(/,/g, '')); break; }
							}
						}
					} catch(e){}
					if (price) break;
				}
			}
			if (!price) {
				var txt = document.body ? document.body.innerText.slice(0, 10000) : '';
				var m = /(?:₱|PHP|Php)\\s*([\\d,]+(?:\\.\\d{1,2})?)/i.exec(txt);
				if (m) price = parseFloat(m[1].replace(/,/g, ''));
			}
			var payload = {
				title: (title || '').trim(),
				price: price || 0,
				url: window.location.href,
				_pricewise_source: 'bookmarklet'
			};
			var jsonStr = JSON.stringify(payload, null, 2);
			if (navigator.clipboard && navigator.clipboard.writeText) {
				navigator.clipboard.writeText(jsonStr).then(function() {
					alert('✅ Copied PriceWise listing data to clipboard!\\n\\nPaste (Ctrl+V) into PriceWise to import.');
				});
			} else {
				prompt('Copy this PriceWise JSON:', jsonStr);
			}
		} catch(err) {
			alert('Error grabbing data: ' + err.message);
		}
	})();`.replace(/\s+/g, ' ').trim();
}
