"""
Marketplace product scraper with multi-layered extraction:
1. URL query parameters / slug fast-path (instant price & title extraction)
2. Fast Direct HTTP extraction (OpenGraph, JSON-LD, microdata)
3. Short URL & redirect resolution (ph.shp.ee, s.lazada.com.ph)
4. Headless Playwright Chromium with anti-detection evasions & container sandbox flags
5. Strict filtering of anti-bot challenge / captcha payloads
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.parse
from typing import Any
from urllib.parse import urlparse

PAGE_TIMEOUT_MS = 25_000
EXTRA_WAIT_MS = 2_000

COMMON_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


# =============================================================================
# Helper: Resolve redirects (for mobile short links like ph.shp.ee or s.lazada)
# =============================================================================

def resolve_redirect_url(url: str, timeout_sec: float = 6.0) -> str:
    """Follow HTTP redirects to get the canonical URL (e.g. ph.shp.ee -> shopee.ph/product...)."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": COMMON_USER_AGENT},
            method="HEAD",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return resp.geturl()
    except Exception:
        pass

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": COMMON_USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return resp.geturl()
    except Exception:
        return url


# =============================================================================
# Helper: URL Query Params Fast Extraction (e.g. Lazada search links with price)
# =============================================================================

def _extract_price_and_title_from_url(url: str) -> dict[str, Any] | None:
    try:
        u = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(u.query)
        price: float | None = None
        title: str = ""

        # Check price param
        if "price" in params:
            try:
                v = float(str(params["price"][0]).replace(",", ""))
                if 1.0 <= v <= 5_000_000.0:
                    price = v
            except Exception:
                pass

        if price is None and "priceCompare" in params:
            pc = urllib.parse.unquote(params["priceCompare"][0])
            m = re.search(r"(?:displayPrice|originPrice|itemPrice)%3A(\d+)|(?:displayPrice|originPrice|itemPrice):(\d+)", pc, re.IGNORECASE)
            if m:
                raw_s = m.group(1) or m.group(2)
                raw_v = float(raw_s)
                if raw_v >= 1000:
                    raw_v = raw_v / 100.0
                if 1.0 <= raw_v <= 5_000_000.0:
                    price = raw_v

        # Check title / query in params or url slug
        if "query" in params:
            title = urllib.parse.unquote_plus(params["query"][0]).strip().title()
        elif "clickTrackInfo" in params:
            cti = urllib.parse.unquote(params["clickTrackInfo"][0])
            m_q = re.search(r"query%3A([^;%]+)", cti, re.IGNORECASE)
            if m_q:
                title = urllib.parse.unquote_plus(m_q.group(1)).strip().title()

        if not title:
            path_slug = u.path.strip("/").split("/")[-1].replace(".html", "")
            path_slug = re.sub(r"-i\d+.*$", "", path_slug).replace("-", " ").strip()
            if path_slug and path_slug.lower() not in ("pdp", "product", "item"):
                title = path_slug.title()

        if price is not None and price > 0:
            return {"title": title or "Marketplace Listing", "price_peso": float(price)}
    except Exception:
        pass
    return None


# =============================================================================
# Helper: Fast Direct HTTP Extraction (JSON-LD, OpenGraph, Meta)
# =============================================================================

def _extract_from_html_meta(html: str) -> dict[str, Any] | None:
    """Extract product title and landed price in PHP from raw HTML text."""
    title = ""
    price: float | None = None

    # 1. JSON-LD Schema
    ld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    for ld_text in ld_matches:
        try:
            data = json.loads(ld_text.strip())
            nodes = data if isinstance(data, list) else [data]
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if not title and isinstance(node.get("name"), str):
                    title = node["name"].strip()
                offers = node.get("offers")
                if offers:
                    off_list = offers if isinstance(offers, list) else [offers]
                    for off in off_list:
                        if isinstance(off, dict):
                            p = off.get("price") or off.get("lowPrice") or off.get("highPrice")
                            if p is not None:
                                try:
                                    v = float(str(p).replace(",", ""))
                                    if v > 0 and (price is None or v < price):
                                        price = v
                                except (ValueError, TypeError):
                                    pass
                if price is None and node.get("price") is not None:
                    try:
                        v = float(str(node["price"]).replace(",", ""))
                        if v > 0:
                            price = v
                    except (ValueError, TypeError):
                        pass
        except Exception:
            continue

    # 2. OpenGraph & Meta Tags
    if not title:
        og_t = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not og_t:
            og_t = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if og_t:
            title = og_t.group(1).strip()

    if price is None:
        og_p = re.search(r'<meta[^>]*property=["\'](?:product|og):price:amount["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not og_p:
            og_p = re.search(r'<meta[^>]*name=["\'](?:twitter:data1|price)["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og_p:
            try:
                v = float(str(og_p.group(1)).replace(",", "").replace("₱", "").replace("PHP", "").strip())
                if v > 0:
                    price = v
            except (ValueError, TypeError):
                pass

    # 3. Regex fallback in visible HTML
    if price is None:
        price_matches = re.findall(r'(?:₱|&#8369;|PHP|Php)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', html[:35000])
        valid_prices = []
        for pm in price_matches:
            try:
                v = float(pm.replace(",", ""))
                if 1.0 <= v <= 5_000_000.0:
                    valid_prices.append(v)
            except Exception:
                continue
        if valid_prices:
            valid_prices.sort()
            price = valid_prices[0]

    if price is not None and price > 0:
        return {"title": title or "Marketplace Listing", "price_peso": float(price)}
    return None


def _try_fast_http_scrape(url: str) -> dict[str, Any] | None:
    """Attempt direct lightweight HTTP GET before launching heavyweight Chromium."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": COMMON_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "text/html" in content_type or "json" in content_type:
                raw_bytes = resp.read(150_000)
                html = raw_bytes.decode("utf-8", errors="ignore")
                return _extract_from_html_meta(html)
    except Exception:
        pass
    return None


# =============================================================================
# Shopee URL & Payload Parsing
# =============================================================================

def _parse_shopee_listing_ids(url: str) -> tuple[str | None, str | None, str | None]:
    try:
        u = urlparse(url.strip())
        host = u.netloc.lower()
        if "shopee." not in host and "shp.ee" not in host:
            return None, None, None

        path = u.path.rstrip("/")
        m = re.search(r"[-.]i\.(\d+)\.(\d+)", path)
        if m:
            shop_id, item_id = m.group(1), m.group(2)
            origin = f"{u.scheme}://{u.netloc}"
            return shop_id, item_id, origin

        m2 = re.search(r"/product/(\d+)/(\d+)", path)
        if m2:
            shop_id, item_id = m2.group(1), m2.group(2)
            origin = f"{u.scheme}://{u.netloc}"
            return shop_id, item_id, origin

        return None, None, None
    except Exception:
        return None, None, None


def _is_shopee_bot_challenge(d: dict[str, Any]) -> bool:
    """Detect Shopee bot challenge / captcha / rate-limit responses."""
    err = d.get("error")
    if err in (90309999, 90309998, 90309997, "90309999", 403, 500):
        return True
    if d.get("redirect_to_error_page") is True:
        return True
    if d.get("action_type") == 2 and "tracking_id" in d:
        return True
    return False


def _dict_looks_like_shopee_item(d: dict[str, Any]) -> bool:
    """Check if dictionary has Shopee item fields and is NOT an error challenge."""
    if _is_shopee_bot_challenge(d):
        return False

    raw_id = d.get("itemid") if d.get("itemid") is not None else d.get("item_id")
    has_id = isinstance(raw_id, (int, float)) or (isinstance(raw_id, str) and raw_id.isdigit())
    if not has_id:
        return False

    return (
        isinstance(d.get("name"), str)
        or isinstance(d.get("price_min"), (int, float))
        or isinstance(d.get("price_max"), (int, float))
        or isinstance(d.get("price"), (int, float))
        or isinstance(d.get("tier_variations"), list)
        or d.get("price_info") is not None
    )


def _walk_find_shopee_item(obj: Any, depth: int = 0) -> dict[str, Any] | None:
    if depth > 18:
        return None
    if isinstance(obj, dict):
        if _is_shopee_bot_challenge(obj):
            return None
        if _dict_looks_like_shopee_item(obj):
            return obj
        nested = obj.get("item")
        if isinstance(nested, dict) and _dict_looks_like_shopee_item(nested):
            return nested
        for v in obj.values():
            hit = _walk_find_shopee_item(v, depth + 1)
            if hit:
                return hit
    elif isinstance(obj, list):
        for el in obj:
            hit = _walk_find_shopee_item(el, depth + 1)
            if hit:
                return hit
    return None


def _synthetic_shopee_payload(shop_id: str | None, item_id: str | None, title: str, price_peso: float) -> dict[str, Any]:
    raw_price = int(round(price_peso * 100_000))
    iid = int(item_id) if item_id and str(item_id).isdigit() else 1
    sid = int(shop_id) if shop_id and str(shop_id).isdigit() else 1
    return {
        "data": {
            "item": {
                "itemid": iid,
                "shopid": sid,
                "name": title or "Shopee Listing",
                "price_min": raw_price,
                "price_max": raw_price,
            }
        },
        "_pricewise_source": "dom_or_meta_fallback",
    }


def _shopee_xhr_looks_like_product_api(rurl: str) -> bool:
    if "shopee" not in rurl and "api/v4" not in rurl and "api/v2" not in rurl:
        return False
    return any(
        m in rurl
        for m in (
            "item/get",
            "pdp/get",
            "get_pc",
            "get_pc_item",
            "item/detail",
            "get_item",
        )
    )


# =============================================================================
# Playwright Stealth Browser Launcher
# =============================================================================

PLAYWRIGHT_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-zygote",
    "--disable-extensions",
    "--disable-software-rasterizer",
]

STEALTH_INIT_SCRIPT = """
(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = window.chrome || {
        app: { isInstalled: false },
        runtime: { PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' } },
    };
    Object.defineProperty(navigator, 'languages', { get: () => ['en-PH', 'en-US', 'en'] });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }
        ]
    });
})();
"""


# =============================================================================
# Shopee Scraper
# =============================================================================

def scrape_shopee_sync(url: str) -> tuple[bool, str | None, str | None]:
    # Step 1: Follow redirects (for short links)
    resolved_url = resolve_redirect_url(url)
    shop_id, item_id, origin = _parse_shopee_listing_ids(resolved_url)

    # Step 2: Try URL params / query hints first
    url_meta = _extract_price_and_title_from_url(resolved_url) or _extract_price_and_title_from_url(url)
    if url_meta and url_meta.get("price_peso"):
        synthetic = _synthetic_shopee_payload(
            shop_id, item_id, url_meta.get("title") or "", url_meta["price_peso"]
        )
        return True, json.dumps(synthetic), None

    # Step 3: Try fast direct HTTP extraction
    fast_meta = _try_fast_http_scrape(resolved_url)
    if fast_meta and fast_meta.get("price_peso"):
        synthetic = _synthetic_shopee_payload(
            shop_id, item_id, fast_meta.get("title") or "", fast_meta["price_peso"]
        )
        return True, json.dumps(synthetic), None

    # Step 4: Browser session with Playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, None, "Playwright is not installed. Run: pip install playwright && playwright install chromium"

    captured: list[Any] = []
    has_bot_challenge = False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=PLAYWRIGHT_LAUNCH_ARGS,
        )
        try:
            context = browser.new_context(
                user_agent=COMMON_USER_AGENT,
                locale="en-PH",
                timezone_id="Asia/Manila",
                viewport={"width": 1365, "height": 900},
            )
            context.add_init_script(STEALTH_INIT_SCRIPT)
            page = context.new_page()

            def on_response(response) -> None:
                nonlocal has_bot_challenge
                try:
                    rurl = response.url.lower()
                    if response.status != 200 or not _shopee_xhr_looks_like_product_api(rurl):
                        return
                    ct = (response.headers.get("content-type") or "").lower()
                    if "json" not in ct:
                        return
                    payload = response.json()
                    if isinstance(payload, dict):
                        if _is_shopee_bot_challenge(payload):
                            has_bot_challenge = True
                            return
                        captured.append(payload)
                except Exception:
                    pass

            page.on("response", on_response)

            try:
                page.goto(resolved_url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
                page.wait_for_timeout(EXTRA_WAIT_MS)
            except Exception:
                pass

            # In-page fetch if listing IDs are known
            if shop_id and item_id and origin and not captured:
                try:
                    inpage_res = page.evaluate(
                        """async ([origin, itemId, shopId]) => {
                            try {
                                const u = new URL(origin + '/api/v4/item/get');
                                u.searchParams.set('itemid', String(itemId));
                                u.searchParams.set('shopid', String(shopId));
                                const r = await fetch(u.toString(), {
                                    credentials: 'include',
                                    headers: { accept: 'application/json', 'x-requested-with': 'XMLHttpRequest' }
                                });
                                return await r.json();
                            } catch (e) { return null; }
                        }""",
                        [origin, item_id, shop_id],
                    )
                    if isinstance(inpage_res, dict) and not _is_shopee_bot_challenge(inpage_res):
                        captured.append(inpage_res)
                except Exception:
                    pass

            # DOM / JSON-LD / Meta extraction from rendered page
            dom_extract = page.evaluate(
                """() => {
                    let title = '';
                    let pricePeso = null;
                    const h1 = document.querySelector('h1');
                    if (h1 && h1.innerText) title = h1.innerText.trim();
                    if (!title) {
                        const og = document.querySelector('meta[property="og:title"]');
                        if (og) title = (og.getAttribute('content') || '').trim();
                    }
                    const metaPrice = document.querySelector('meta[property="product:price:amount"]') ||
                                      document.querySelector('meta[property="og:price:amount"]');
                    if (metaPrice) {
                        const s = metaPrice.getAttribute('content');
                        const v = parseFloat(String(s || '').replace(/,/g, ''));
                        if (!isNaN(v) && v > 0) pricePeso = v;
                    }
                    if (pricePeso == null) {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const sc of scripts) {
                            try {
                                const j = JSON.parse(sc.textContent || '{}');
                                const nodes = Array.isArray(j) ? j : [j];
                                for (const n of nodes) {
                                    if (!n || typeof n !== 'object') continue;
                                    const off = Array.isArray(n.offers) ? n.offers[0] : n.offers;
                                    let p = off && off.price != null ? off.price : n.price;
                                    if (typeof p === 'string') p = parseFloat(p.replace(/,/g, ''));
                                    if (typeof p === 'number' && !isNaN(p) && p > 0) {
                                        pricePeso = p;
                                        break;
                                    }
                                }
                                if (pricePeso != null) break;
                            } catch (e) {}
                        }
                    }
                    return { title, pricePeso };
                }"""
            )
            if isinstance(dom_extract, dict) and dom_extract.get("pricePeso"):
                captured.append(
                    _synthetic_shopee_payload(
                        shop_id, item_id, dom_extract.get("title") or "", dom_extract["pricePeso"]
                    )
                )
        finally:
            browser.close()

    # Find first valid item payload
    for c in reversed(captured):
        if _walk_find_shopee_item(c):
            return True, json.dumps(c), None

    if has_bot_challenge:
        return (
            False,
            None,
            "Shopee security check triggered on cloud server. Please use the Quick Grabber bookmarklet or paste the product JSON.",
        )

    return (
        False,
        None,
        "Could not capture Shopee listing data. Confirm the product link or paste product details manually.",
    )


# =============================================================================
# Lazada Scraper
# =============================================================================

def _lazada_xhr_looks_useful(rurl: str) -> bool:
    if "lazada" not in rurl:
        return False
    return any(
        m in rurl
        for m in (
            "product",
            "pdp",
            "mtop",
            "sku",
            "price",
            "item",
            "detail",
            "offer",
            "promotion",
            "gw/",
            "h5api",
            "acs-m",
            "acs.",
        )
    )


def scrape_lazada_sync(url: str) -> tuple[bool, str | None, str | None]:
    # Step 1: Resolve redirects (for mobile s.lazada links)
    resolved_url = resolve_redirect_url(url)
    if "lazada." not in urlparse(resolved_url).netloc.lower():
        return False, None, "URL does not look like a Lazada storefront link."

    # Step 2: Try URL parameters / search link hints first (e.g. price=138, displayPrice:13800)
    url_meta = _extract_price_and_title_from_url(resolved_url) or _extract_price_and_title_from_url(url)
    if url_meta and url_meta.get("price_peso"):
        synthetic = {
            "price": url_meta["price_peso"],
            "title": url_meta.get("title") or "",
            "_pricewise_source": "url_params_fallback",
            "_pricewisePageUrl": resolved_url,
        }
        return True, json.dumps(synthetic), None

    # Step 3: Try fast direct HTTP extraction
    fast_meta = _try_fast_http_scrape(resolved_url)
    if fast_meta and fast_meta.get("price_peso"):
        synthetic = {
            "price": fast_meta["price_peso"],
            "title": fast_meta.get("title") or "",
            "_pricewise_source": "dom_or_meta_fallback",
            "_pricewisePageUrl": resolved_url,
        }
        return True, json.dumps(synthetic), None

    # Step 4: Browser session with Playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, None, "Playwright is not installed. Run: pip install playwright && playwright install chromium"

    captured: list[Any] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=PLAYWRIGHT_LAUNCH_ARGS,
        )
        try:
            context = browser.new_context(
                user_agent=COMMON_USER_AGENT,
                locale="en-PH",
                timezone_id="Asia/Manila",
                viewport={"width": 1365, "height": 900},
            )
            context.add_init_script(STEALTH_INIT_SCRIPT)
            page = context.new_page()

            def on_response(response) -> None:
                try:
                    if response.status != 200 or not _lazada_xhr_looks_useful(response.url.lower()):
                        return
                    ct = (response.headers.get("content-type") or "").lower()
                    if "json" not in ct:
                        return
                    payload = response.json()
                    if isinstance(payload, dict) and payload:
                        captured.append(payload)
                except Exception:
                    pass

            page.on("response", on_response)

            try:
                page.goto(resolved_url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
                page.wait_for_timeout(EXTRA_WAIT_MS)
            except Exception:
                pass

            # Extract bootstrap state
            try:
                bootstrap = page.evaluate(
                    """() => {
                        try {
                            return {
                                __moduleData__: typeof window.__moduleData__ !== 'undefined' ? window.__moduleData__ : null,
                                pageData: typeof window.pageData !== 'undefined' ? window.pageData : null,
                                __INIT_DATA__: typeof window.__INIT_DATA__ !== 'undefined' ? window.__INIT_DATA__ : null,
                            };
                        } catch (e) { return null; }
                    }"""
                )
                if bootstrap and any(bootstrap.get(k) for k in ("__moduleData__", "pageData", "__INIT_DATA__")):
                    captured.append({"_lazadaPageBootstrap": bootstrap})
            except Exception:
                pass

            # DOM fallback
            dom_extract = page.evaluate(
                """() => {
                    let title = '';
                    let pricePeso = null;
                    const h1 = document.querySelector('h1') || document.querySelector('.pdp-mod-product-badge-title');
                    if (h1 && h1.innerText) title = h1.innerText.trim();
                    if (!title) {
                        const og = document.querySelector('meta[property="og:title"]');
                        if (og) title = (og.getAttribute('content') || '').trim();
                    }
                    const metaPrice = document.querySelector('meta[property="product:price:amount"]') ||
                                      document.querySelector('meta[property="og:price:amount"]');
                    if (metaPrice) {
                        const s = metaPrice.getAttribute('content');
                        const v = parseFloat(String(s || '').replace(/,/g, ''));
                        if (!isNaN(v) && v > 0) pricePeso = v;
                    }
                    if (pricePeso == null) {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const sc of scripts) {
                            try {
                                const j = JSON.parse(sc.textContent || '{}');
                                const nodes = Array.isArray(j) ? j : [j];
                                for (const n of nodes) {
                                    if (!n || typeof n !== 'object') continue;
                                    const off = Array.isArray(n.offers) ? n.offers[0] : n.offers;
                                    let p = off && off.price != null ? off.price : n.price;
                                    if (typeof p === 'string') p = parseFloat(p.replace(/,/g, ''));
                                    if (typeof p === 'number' && !isNaN(p) && p > 0) {
                                        pricePeso = p;
                                        break;
                                    }
                                }
                                if (pricePeso != null) break;
                            } catch (e) {}
                        }
                    }
                    return { title, pricePeso };
                }"""
            )
            if isinstance(dom_extract, dict) and dom_extract.get("pricePeso"):
                captured.append(
                    {
                        "price": dom_extract["pricePeso"],
                        "title": dom_extract.get("title") or "",
                        "_pricewise_source": "dom_fallback",
                    }
                )
        finally:
            browser.close()

    if not captured:
        return (
            False,
            None,
            "Could not capture Lazada product data. Try using the Quick Grabber bookmarklet or paste JSON.",
        )

    payload = captured[-1]
    if isinstance(payload, dict):
        payload["_pricewisePageUrl"] = resolved_url

    try:
        return True, json.dumps(payload), None
    except Exception as exc:
        return False, None, str(exc)