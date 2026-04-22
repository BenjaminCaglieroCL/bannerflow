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
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            payload = json.loads(script.string or '')
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        return item
            elif isinstance(payload, dict) and payload.get('@type') == 'Product':
                return payload
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


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
    # Original price: <s> element with 'ui-pdp-price__original-value' class
    original_el = soup.find('s', class_=re.compile(r'ui-pdp-price__original-value'))
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
    soup = _get_soup_playwright(url, wait_selector='h1', timeout=15000)
    data = {
        'store_name': 'Falabella',
        'store_logo': 'falabella',
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
        img = (
            soup.find('img', attrs={'id': re.compile(r'product', re.I)}) or
            soup.find('img', attrs={'class': re.compile(r'product.*image|gallery.*image', re.I)})
        )
        if img:
            data['image_url'] = img.get('src', '') or img.get('data-src', '')
        else:
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
