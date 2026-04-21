import json as _json
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


_ALLOWED_DOMAINS = (
    'mercadolibre.',
    'mercadoli.',
    'meli.la',
    'sodimac.',
    'homecenter.',
    'falabella.',
)


def _is_allowed_url(url):
    """Return True only if the URL belongs to a whitelisted e-commerce domain."""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return False
    return any(part in domain for part in _ALLOWED_DOMAINS)


def scrape_url(url):
    """Detect store from URL and scrape product data."""
    if not _is_allowed_url(url):
        raise ValueError(f"Dominio no permitido: {urlparse(url).netloc}")

    domain = urlparse(url).netloc.lower()

    if 'mercadolibre' in domain or 'mercadoli' in domain:
        return scrape_mercadolibre(url)
    elif 'meli.la' in domain:
        return scrape_meli(url)
    elif 'sodimac' in domain or 'homecenter' in domain:
        return scrape_sodimac(url)
    elif 'falabella' in domain:
        return scrape_falabella(url)
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
    """Extract numeric price from text like '$29.990' or 'CLP 29990'."""
    if not text:
        return None
    numbers = re.findall(r'[\d.,]+', text.replace('.', '').replace(',', '.'))
    if numbers:
        try:
            return int(float(numbers[0]))
        except ValueError:
            pass
    return text.strip()


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


def _extract_json_ld(soup):
    """Return the first JSON-LD block whose @type is 'Product', or {}."""
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            raw = script.string or script.get_text()
            parsed = _json.loads(raw)
            items = parsed if isinstance(parsed, list) else [parsed]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get('@type') == 'Product':
                    return item
                for sub in item.get('@graph', []):
                    if isinstance(sub, dict) and sub.get('@type') == 'Product':
                        return sub
        except Exception:
            pass
    return {}


def _fill_prices_from_text(soup, data):
    """Generic fallback: scan page text for $-prefixed numbers and fill missing prices."""
    if 'offer_price' not in data and 'original_price' not in data:
        price_texts = soup.find_all(string=re.compile(r'\$[\d.,]+'))
        prices = []
        for pt in price_texts[:6]:
            val = _clean_price(pt)
            if val and isinstance(val, int) and val > 0:
                prices.append(val)
        prices = sorted(set(prices), reverse=True)
        if len(prices) >= 2:
            data.setdefault('original_price', prices[0])
            data.setdefault('offer_price', prices[1])
        elif len(prices) == 1:
            data.setdefault('offer_price', prices[0])

    data.setdefault('original_price', data.get('offer_price'))
    data.setdefault('offer_price', data.get('original_price'))


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
    # Original price: the fraction inside the strikethrough <s> element
    original_el = soup.find('s', class_=re.compile(r'ui-pdp-price__original-value'))
    if original_el:
        frac = original_el.find('span', class_='andes-money-amount__fraction')
        if frac:
            data['original_price'] = _clean_price(frac.get_text())

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


# --- MELI (meli.la short links → MercadoLibre) ---

def scrape_meli(url):
    """Resolve a meli.la short-link redirect and scrape it as MercadoLibre."""
    resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
    final_url = resp.url
    # Ensure the redirect landed on a trusted MercadoLibre domain
    if not _is_allowed_url(final_url):
        raise ValueError(f"Redirección a dominio no permitido: {urlparse(final_url).netloc}")
    return scrape_mercadolibre(final_url)


# --- Sodimac ---

def scrape_sodimac(url):
    """Scrape a Sodimac product page (sodimac.cl / homecenter.com.co)."""
    soup = _get_soup_playwright(url, wait_selector='h1')
    data = {
        'store_name': 'Sodimac',
        'store_logo': 'sodimac',
        'source_url': url,
    }

    # 1. Title — prefer JSON-LD, fall back to h1 / OG
    ld = _extract_json_ld(soup)
    if ld.get('name'):
        data['title'] = ld['name']
    else:
        h1 = soup.find('h1')
        data['title'] = h1.get_text(strip=True) if h1 else ''

    # 2. Product image — JSON-LD → OG → first large img
    if ld.get('image'):
        img_val = ld['image']
        data['image_url'] = img_val[0] if isinstance(img_val, list) else img_val
    else:
        og = _extract_og(soup)
        data['image_url'] = og.get('image_url', '')
    if not data.get('image_url'):
        img_el = soup.find('img', class_=re.compile(r'product|gallery|principal', re.I))
        if img_el:
            data['image_url'] = img_el.get('src', '') or img_el.get('data-src', '')

    # 3 & 4. Prices
    # Try JSON-LD offers first
    offers = ld.get('offers', {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if offers:
        offer_price = offers.get('price')
        if offer_price is not None:
            data['offer_price'] = _clean_price(str(offer_price))
        high_price = offers.get('highPrice')
        if high_price is not None:
            data['original_price'] = _clean_price(str(high_price))

    # Try page elements (Sodimac uses data-price / class names)
    if 'offer_price' not in data:
        # Sodimac "precio oferta" is usually inside an element with class containing
        # "priceBox", "price-offer", "special-price", or data-id="offerPrice"
        offer_el = soup.find(
            class_=re.compile(r'oferta|offer|special|promo', re.I),
            string=re.compile(r'\d')
        )
        if not offer_el:
            offer_el = soup.find(attrs={'data-id': re.compile(r'offer|sale', re.I)})
        if offer_el:
            data['offer_price'] = _clean_price(offer_el.get_text())

        original_el = soup.find(
            class_=re.compile(r'normal|original|before|tachado', re.I),
            string=re.compile(r'\d')
        )
        if not original_el:
            original_el = soup.find(
                attrs={'data-id': re.compile(r'normal|original', re.I)}
            )
        if original_el:
            data['original_price'] = _clean_price(original_el.get_text())

    # Generic price fallback and mutual default
    _fill_prices_from_text(soup, data)

    return data


# --- Falabella ---

def scrape_falabella(url):
    """Scrape a Falabella product page (falabella.com)."""
    soup = _get_soup_playwright(url, wait_selector='h1')
    data = {
        'store_name': 'Falabella',
        'store_logo': 'falabella',
        'source_url': url,
    }

    # 1. Try __NEXT_DATA__ (most complete source)
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    next_product = {}
    if next_data_script:
        try:
            next_raw = _json.loads(next_data_script.string or '')
            # Navigate to product data inside Next.js page props
            props = next_raw.get('props', {}).get('pageProps', {})
            # Falabella stores product under different keys depending on page version
            product_obj = (
                props.get('product')
                or props.get('initialState', {}).get('product', {}).get('product')
                or {}
            )
            if not product_obj:
                # Try deeper: initialState.product.currentProduct
                initial = props.get('initialState', {})
                product_obj = (
                    initial.get('product', {}).get('currentProduct')
                    or initial.get('pdp', {}).get('product')
                    or {}
                )
            next_product = product_obj or {}
        except Exception:
            pass

    # 2. Title
    if next_product.get('name') or next_product.get('displayName'):
        data['title'] = next_product.get('displayName') or next_product.get('name', '')
    else:
        ld = _extract_json_ld(soup)
        if ld.get('name'):
            data['title'] = ld['name']
        else:
            h1 = soup.find('h1')
            data['title'] = h1.get_text(strip=True) if h1 else ''

    # 3. Product image
    # __NEXT_DATA__ images
    images = next_product.get('images') or next_product.get('medias') or []
    if images and isinstance(images, list):
        first_img = images[0]
        img_url = (
            first_img.get('url') or first_img.get('id') or ''
            if isinstance(first_img, dict) else str(first_img)
        )
        data['image_url'] = img_url
    if not data.get('image_url'):
        ld = _extract_json_ld(soup)
        img_val = ld.get('image', '')
        data['image_url'] = img_val[0] if isinstance(img_val, list) else img_val
    if not data.get('image_url'):
        og = _extract_og(soup)
        data['image_url'] = og.get('image_url', '')
    if not data.get('image_url'):
        img_el = soup.find('img', class_=re.compile(r'product|gallery|main', re.I))
        if img_el:
            data['image_url'] = img_el.get('src', '') or img_el.get('data-src', '')

    # 4 & 5. Prices
    # __NEXT_DATA__ prices
    prices_node = next_product.get('prices') or next_product.get('price') or {}
    if isinstance(prices_node, dict):
        # Falabella typically has 'originalPrice' and 'offerPrice' / 'eventPrice'
        original = (
            prices_node.get('originalPrice')
            or prices_node.get('normalPrice')
            or prices_node.get('regularPrice')
        )
        offer = (
            prices_node.get('offerPrice')
            or prices_node.get('eventPrice')
            or prices_node.get('internetPrice')
            or prices_node.get('salePrice')
        )
        if original is not None:
            data['original_price'] = _clean_price(str(original))
        if offer is not None:
            data['offer_price'] = _clean_price(str(offer))

    # JSON-LD offers fallback
    if 'offer_price' not in data:
        ld = _extract_json_ld(soup)
        offers = ld.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if offers:
            offer_price = offers.get('price')
            if offer_price is not None:
                data['offer_price'] = _clean_price(str(offer_price))
            high_price = offers.get('highPrice')
            if high_price is not None:
                data['original_price'] = _clean_price(str(high_price))

    # CSS selector fallback for Falabella prices
    if 'offer_price' not in data:
        # Falabella renders prices in <li> with class "prices-N" or "copy20"
        price_els = soup.find_all(class_=re.compile(r'prices-\d|internet|oferta|sale', re.I))
        prices = []
        for el in price_els[:4]:
            val = _clean_price(el.get_text())
            if val and isinstance(val, int) and val > 0:
                prices.append(val)
        prices = sorted(set(prices), reverse=True)
        if len(prices) >= 2:
            data.setdefault('original_price', prices[0])
            data.setdefault('offer_price', prices[1])
        elif len(prices) == 1:
            data.setdefault('offer_price', prices[0])

    # Generic price fallback and mutual default
    _fill_prices_from_text(soup, data)

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
