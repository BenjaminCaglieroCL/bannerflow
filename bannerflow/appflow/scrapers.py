import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from playwright.sync_api import sync_playwright


HEADERS = {
    'User-Agent': getattr(settings, 'SCRAPER_USER_AGENT',
                          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36'),
    'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
}


def scrape_url(url):
    """Detect store from URL and scrape product data."""
    domain = urlparse(url).netloc.lower()

    # meli.la is a MercadoLibre short-link — follow the redirect first
    if 'meli.la' in domain:
        try:
            resp = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            url = resp.url
        except Exception:
            pass
        return scrape_mercadolibre(url)

    if 'mercadolibre' in domain or 'mercadoli' in domain:
        return scrape_mercadolibre(url)
    elif 'falabella' in domain:
        return scrape_falabella(url)
    elif 'sodimac' in domain or 'homecenter' in domain:
        return scrape_sodimac(url)
    elif 'adidas' in domain:
        return scrape_adidas(url)
    else:
        return scrape_generic(url)


def _get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')


def _get_soup_playwright(url, wait_selector='h1', timeout=15000):
    """Render a JS-heavy page with a headless browser and return its soup."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS['User-Agent'],
            locale='es-CL',
        )
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        try:
            page.wait_for_selector(wait_selector, timeout=timeout)
        except Exception:
            page.wait_for_timeout(5000)
        html = page.content()
        browser.close()
    return BeautifulSoup(html, 'html.parser')


def _clean_price(text):
    """Extract numeric CLP price (Chilean format: dots as thousands separators)."""
    if not text:
        return None
    text = str(text).strip()
    # Handle float strings from JSON-LD (e.g. '23409.0')
    try:
        f = float(text)
        if f == int(f):
            return int(f)
    except (ValueError, TypeError):
        pass
    # Chilean prices use dots as thousands separators — strip them
    m = re.search(r'[\d]+(?:\.[\d]+)*', text)
    if m:
        try:
            return int(m.group(0).replace('.', ''))
        except ValueError:
            pass
    return None


def _max_price_in_section(el):
    """Extract the largest Chilean $-prefixed price from a BS4 element."""
    if not el:
        return None
    text = el.get_text(' ', strip=True)
    prices = []
    for m in re.finditer(r'\$\s*([\d][\d.]*)', text):
        raw = m.group(1).replace('.', '')
        try:
            prices.append(int(raw))
        except ValueError:
            pass
    return max(prices) if prices else None


def _extract_og(soup):
    """Extract Open Graph meta tags as fallback."""
    data = {}
    og_title = soup.find('meta', property='og:title')
    if og_title:
        data['title'] = og_title.get('content', '')
    og_image = soup.find('meta', property='og:image')
    if og_image:
        data['image_url'] = og_image.get('content', '')
    og_site = soup.find('meta', property='og:site_name')
    if og_site:
        data['store_name'] = og_site.get('content', '')
    return data


def _extract_jsonld(soup):
    """Extract JSON-LD Product structured data from the page (most reliable source)."""
    def find_product(obj):
        if isinstance(obj, dict):
            typ = obj.get('@type')
            if isinstance(typ, list) and 'Product' in typ:
                return obj
            if typ == 'Product':
                return obj
            for key in ('@graph', 'mainEntity', 'itemListElement'):
                if key in obj:
                    found = find_product(obj[key])
                    if found:
                        return found
            for value in obj.values():
                found = find_product(value)
                if found:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = find_product(item)
                if found:
                    return found
        return None

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            payload = json.loads(script.string or '')
            found = find_product(payload)
            if found:
                return found
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def _extract_adidas_sku(url):
    """Extract product SKU/code from Adidas product URLs."""
    path = urlparse(url).path
    m = re.search(r'/([A-Za-z0-9]{5,})\.html$', path)
    return m.group(1).upper() if m else ''


def _is_adidas_blocked_page(soup):
    """Detect anti-bot/challenge pages returned by adidas.cl."""
    page_text = soup.get_text(' ', strip=True).lower()
    block_markers = [
        'unfortunately we are unable to give you access',
        'access denied',
        'powered and protected by',
    ]
    return any(marker in page_text for marker in block_markers)


def _scrape_adidas_via_jina(url):
    """Fallback scraper using r.jina.ai mirror when adidas.cl blocks direct requests."""
    mirror_url = 'https://r.jina.ai/http://' + url.replace('https://', '').replace('http://', '')
    resp = requests.get(mirror_url, headers=HEADERS, timeout=40)
    resp.raise_for_status()
    text = resp.text

    sku = _extract_adidas_sku(url)
    data = {
        'store_name': 'Adidas',
        'store_logo': 'adidas',
        'source_url': url,
    }

    # Title (from mirror preamble or markdown H1)
    title_match = re.search(r'^Title:\s*(.+)$', text, flags=re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'\s*\|\s*adidas\s+chile\s*$', '', title, flags=re.I)
        data['title'] = title
    else:
        h1_match = re.search(r'^#\s+(.+)$', text, flags=re.MULTILINE)
        if h1_match:
            data['title'] = h1_match.group(1).strip()

    # Focus extraction around the SKU to avoid grabbing related-product data.
    work_text = text
    if sku:
        idx = text.upper().find(sku)
        if idx != -1:
            work_text = text[max(0, idx - 1000):idx + 5000]

    # Product image URL from assets.adidas.com containing the target SKU.
    image_url = ''
    image_pattern = r'https://assets\.adidas\.com/images/[^\s\)\]]+'
    candidates = re.findall(image_pattern, work_text)
    if not candidates:
        candidates = re.findall(image_pattern, text)

    filtered = []
    for c in candidates:
        cu = c.lower()
        if sku and sku.lower() not in cu:
            continue
        if 'video' in cu:
            continue
        if 'hover' in cu:
            continue
        filtered.append(c)

    if filtered:
        preferred = [c for c in filtered if '_hm1' in c.lower() or '_00_plp_standard' in c.lower()]
        image_url = preferred[0] if preferred else filtered[0]

    if image_url:
        data['image_url'] = image_url

    price_scope_text = text
    if data.get('title'):
        base_title = data['title'].split(' - ')[0].strip()
        if base_title:
            heading_pat = re.compile(r'\n#\s+' + re.escape(base_title) + r'\b', flags=re.I)
            heading_matches = list(heading_pat.finditer(text))
            if heading_matches:
                start_idx = heading_matches[-1].start()
                price_scope_text = text[start_idx:start_idx + 2500]

    m_install = re.search(r'Hasta\s*(\d+)\s*x\s*\*\*\$\s*([\d\.,]+)', price_scope_text, flags=re.I)

    # Prices: parse the main PDP price block close to the installment block.
    if m_install:
        idx = m_install.start()
        window = price_scope_text[max(0, idx - 1400):idx + 200]
        m_main = re.search(
            r'Precio de venta\s*\$\s*([\d\.]+)\s*\$\s*([\d\.]+)\s*Precio\s+original',
            window,
            flags=re.I,
        )
        if m_main:
            data['offer_price'] = _clean_price(m_main.group(1))
            data['original_price'] = _clean_price(m_main.group(2))

    # If the main block wasn't found, infer offer price from installments.
    if not data.get('offer_price') and m_install:
        try:
            n = int(m_install.group(1))
            per_installment = float(m_install.group(2).replace('.', '').replace(',', '.'))
            data['offer_price'] = int(round(n * per_installment))
        except (TypeError, ValueError):
            pass

    # If original wasn't found, try nearest "Precio original" amount around installments.
    if data.get('offer_price') and not data.get('original_price') and m_install:
        idx = m_install.start()
        window = price_scope_text[max(0, idx - 1400):idx + 200]
        m_orig = re.search(r'\$\s*([\d\.]+)\s*Precio\s+original', window, flags=re.I)
        if m_orig:
            data['original_price'] = _clean_price(m_orig.group(1))

    # Prices: additional fallback parsing around SKU context.
    raw_prices = re.findall(r'\$\s*([\d][\d\.]*)', work_text)
    prices = []
    for raw in raw_prices:
        try:
            prices.append(int(raw.replace('.', '')))
        except ValueError:
            continue

    # Keep order while deduplicating
    seen = set()
    ordered = []
    for p in prices:
        if p not in seen:
            seen.add(p)
            ordered.append(p)

    if ordered and not data.get('offer_price'):
        data['offer_price'] = ordered[0]
        data['original_price'] = ordered[1] if len(ordered) > 1 else ordered[0]

    if data.get('offer_price') and not data.get('original_price'):
        data['original_price'] = data['offer_price']

    return data


# --- MercadoLibre ---

def scrape_mercadolibre(url):
    soup = _get_soup_playwright(url, wait_selector='h1.ui-pdp-title')
    data = {
        'store_name': 'MercadoLibre',
        'store_logo': 'mercadolibre',
        'source_url': url,
    }

    # 1. Title
    title_el = soup.find('h1', class_='ui-pdp-title') or soup.find('h1')
    data['title'] = title_el.get_text(strip=True) if title_el else ''

    # 2. Product image — prefer the main gallery figure image (high-res -O.webp)
    img = soup.find('img', class_=re.compile(r'ui-pdp-gallery__figure__image'))
    if not img:
        img = soup.find('img', class_='ui-pdp-image')
    src = ''
    if img:
        src = img.get('src', '') or img.get('data-src', '')
    data['image_url'] = src

    # 3 & 4. Prices
    # Original price: <s> element — try legacy class first, then any <s> with a price fraction
    original_el = soup.find('s', class_=re.compile(r'ui-pdp-price__original-value'))
    if not original_el:
        # New page structure uses andes-money-amount--previous inside a <s>
        for s_tag in soup.find_all('s'):
            if s_tag.find('span', class_='andes-money-amount__fraction'):
                original_el = s_tag
                break
    if original_el:
        frac = original_el.find('span', class_='andes-money-amount__fraction')
        raw = frac.get_text(strip=True) if frac else original_el.get_text(strip=True)
        data['original_price'] = _clean_price(raw)

    # Offer price: first andes-money-amount__fraction NOT inside an <s> ancestor
    for frac in soup.find_all('span', class_='andes-money-amount__fraction'):
        if frac.find_parent('s'):
            continue
        # Also skip installment prices (inside ui-pdp-price__subtitles)
        if frac.find_parent(class_=re.compile(r'subtitles|installment')):
            continue
        data['offer_price'] = _clean_price(frac.get_text())
        break

    # Fallbacks
    if 'original_price' not in data:
        data['original_price'] = data.get('offer_price')
    if 'offer_price' not in data:
        data['offer_price'] = data.get('original_price')

    # 5. Store name is always 'MercadoLibre' (already set)

    # Fallback to OG meta tags
    if not data.get('image_url') or not data.get('title'):
        og = _extract_og(soup)
        data['title'] = data.get('title') or og.get('title', '')
        data['image_url'] = data.get('image_url') or og.get('image_url', '')

    return data



# --- Sodimac ---

def scrape_sodimac(url):
    soup = _get_soup_playwright(url, wait_selector='[class*="prices-0"]', timeout=15000)
    data = {
        'store_name': 'Sodimac',
        'store_logo': 'sodimac',
        'source_url': url,
    }

    # 1. Title
    h1 = soup.find('h1')
    data['title'] = h1.get_text(strip=True) if h1 else ''

    # 2. Image — JSON-LD first, then OG
    jsonld = _extract_jsonld(soup)
    if jsonld:
        images = jsonld.get('image', [])
        data['image_url'] = (images[0] if isinstance(images, list) else images) or ''
    if not data.get('image_url'):
        og = _extract_og(soup)
        data['image_url'] = og.get('image_url', '')

    # 3. Prices — Sodimac renders prices-0 (offer/event) and prices-1 (normal/original)
    #    Each section may contain multiple prices (e.g. per-m² and per-caja); take the max.
    offer_section = soup.find(class_=re.compile(r'\bprices-0\b'))
    orig_section = soup.find(class_=re.compile(r'\bprices-1\b'))

    if offer_section:
        data['offer_price'] = _max_price_in_section(offer_section)
    if orig_section:
        data['original_price'] = _max_price_in_section(orig_section)

    # Fallback to JSON-LD if sections not found
    if not data.get('offer_price') and jsonld:
        offers = jsonld.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get('price') or offers.get('lowPrice')
        if price:
            data['offer_price'] = _clean_price(str(price))

    # If there's no sale, original == offer
    if not data.get('original_price'):
        data['original_price'] = data.get('offer_price')
    if not data.get('offer_price'):
        data['offer_price'] = data.get('original_price')

    return data


# --- Falabella ---

def scrape_falabella(url):
    soup = _get_soup_playwright(url, wait_selector='[class*="prices-0"]', timeout=15000)
    data = {
        'store_name': 'Falabella',
        'store_logo': 'falabella',
        'source_url': url,
    }

    # 1. Title
    h1 = soup.find('h1')
    data['title'] = h1.get_text(strip=True) if h1 else ''

    # 2. Image — prefer large product img tag (w=1200,fit=pad) over JSON-LD /public URL
    jsonld = _extract_jsonld(soup)
    img_el = soup.find('img', src=re.compile(r'media\.falabella\.com.+w=\d+', re.I))
    if img_el:
        src = img_el.get('src', '')
        # Upgrade any size param to 1200 for best quality
        data['image_url'] = re.sub(r'/w=\d+,h=\d+,[^/\s]+', '/w=1200,h=1200,fit=pad', src)
    elif jsonld:
        images = jsonld.get('image', [])
        img_url = (images[0] if isinstance(images, list) else images) or ''
        # Convert bare /public → explicit dimensions (avoids CORS issues)
        if img_url.endswith('/public'):
            img_url = img_url[:-len('/public')] + '/w=1200,h=1200,fit=pad'
        data['image_url'] = img_url
    if not data.get('image_url'):
        og = _extract_og(soup)
        data['image_url'] = og.get('image_url', '')

    # 3. Prices — Falabella renders prices-0 (offer/internet) and prices-1 (normal/original)
    offer_section = soup.find(class_=re.compile(r'\bprices-0\b'))
    orig_section = soup.find(class_=re.compile(r'\bprices-1\b'))

    if offer_section:
        data['offer_price'] = _max_price_in_section(offer_section)
    if orig_section:
        data['original_price'] = _max_price_in_section(orig_section)

    # Fallback to JSON-LD if sections not found
    if not data.get('offer_price') and jsonld:
        offers = jsonld.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get('price') or offers.get('lowPrice')
        if price:
            data['offer_price'] = _clean_price(str(price))

    # If there's no sale, original == offer
    if not data.get('original_price'):
        data['original_price'] = data.get('offer_price')
    if not data.get('offer_price'):
        data['offer_price'] = data.get('original_price')

    return data


# --- Adidas ---

def scrape_adidas(url):
    """Scrape Adidas product pages using JSON-LD schema and DOM selectors."""
    soup = _get_soup_playwright(url, wait_selector='h1', timeout=20000)
    data = {
        'store_name': 'Adidas',
        'store_logo': 'adidas',
        'source_url': url,
    }

    # If adidas challenge page is returned, fallback to mirror extraction.
    if _is_adidas_blocked_page(soup):
        return _scrape_adidas_via_jina(url)

    # 1. Title — prefer h1, fallback to meta title
    h1 = soup.find('h1')
    data['title'] = h1.get_text(strip=True) if h1 else ''

    # 2. Image — prefer JSON-LD first, then look for product image in DOM
    jsonld = _extract_jsonld(soup)
    
    if jsonld:
        images = jsonld.get('image', [])
        img_url = (images[0] if isinstance(images, list) else images) or ''
        # Ensure it's a proper URL (not a relative path)
        if img_url and not img_url.startswith('http'):
            img_url = 'https:' + img_url if img_url.startswith('//') else img_url
        data['image_url'] = img_url
    
    # Fallback: look for product image in DOM (common patterns in Adidas)
    if not data.get('image_url'):
        # Try common Adidas image patterns
        img = soup.find('img', src=re.compile(r'(product|shoe|item)', re.I))
        if not img:
            img = soup.find('img', class_=re.compile(r'(product|main|primary|hero)', re.I))
        if not img:
            # Last resort: any img that's not too small
            for candidate in soup.find_all('img', limit=20):
                src = candidate.get('src', '')
                if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                    img = candidate
                    break
        
        if img:
            src = img.get('src', '')
            if src and not src.startswith('http'):
                src = 'https:' + src if src.startswith('//') else src
            data['image_url'] = src
    
    # Fallback to Open Graph
    if not data.get('image_url'):
        og = _extract_og(soup)
        data['image_url'] = og.get('image_url', '')

    # 3 & 4. Prices — Extract from JSON-LD (most reliable for Adidas)
    if jsonld:
        offers = jsonld.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        
        price = offers.get('price')
        if price:
            data['offer_price'] = _clean_price(str(price))
    
    # Fallback: look for prices in DOM
    if not data.get('offer_price'):
        # Adidas typically uses specific price containers; look for them
        price_patterns = soup.find_all(string=re.compile(r'\$[\d.,\s]+'))
        prices = []
        for p in price_patterns:
            val = _clean_price(p)
            if val and isinstance(val, int):
                prices.append(val)
        
        if prices:
            prices.sort(reverse=True)
            data['offer_price'] = prices[0]
    
    # Adidas doesn't typically show original/discounted prices separately
    # Set original price same as offer price (or keep as fallback)
    if not data.get('original_price'):
        data['original_price'] = data.get('offer_price')
    if not data.get('offer_price'):
        data['offer_price'] = data.get('original_price')

    # Final fallback in case adidas blocks some sessions and critical fields are missing.
    if not data.get('title') or not data.get('image_url') or not data.get('offer_price'):
        try:
            mirror_data = _scrape_adidas_via_jina(url)
            for key in ('title', 'image_url', 'offer_price', 'original_price'):
                if not data.get(key) and mirror_data.get(key):
                    data[key] = mirror_data[key]
        except Exception:
            pass

    return data


# --- Generic / Fallback ---

def scrape_generic(url):
    """Fallback scraper using Open Graph and meta tags."""
    soup = _get_soup(url)
    data = _extract_og(soup)
    data['source_url'] = url
    data['store_logo'] = 'generic'

    if not data.get('store_name'):
        domain = urlparse(url).netloc
        data['store_name'] = domain.replace('www.', '').split('.')[0].title()

    if not data.get('title'):
        title_tag = soup.find('title')
        data['title'] = title_tag.get_text(strip=True) if title_tag else 'Producto'

    if not data.get('image_url'):
        img = soup.find('img', src=True)
        if img:
            data['image_url'] = img['src']

    # Try to find prices
    price_patterns = soup.find_all(string=re.compile(r'\$[\d.,]+'))
    prices = []
    for p in price_patterns[:4]:
        val = _clean_price(p)
        if val and isinstance(val, int):
            prices.append(val)
    
    if len(prices) >= 2:
        prices.sort(reverse=True)
        data['original_price'] = prices[0]
        data['offer_price'] = prices[1]
    elif len(prices) == 1:
        data['offer_price'] = prices[0]
        data['original_price'] = prices[0]
    else:
        data['original_price'] = None
        data['offer_price'] = None

    return data
