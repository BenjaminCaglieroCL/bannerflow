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

    if 'mercadolibre' in domain or 'mercadoli' in domain:
        return scrape_mercadolibre(url)
    elif 'amazon' in domain:
        return scrape_amazon(url)
    elif 'sodimac' in domain or 'homecenter' in domain:
        return scrape_sodimac(url)
    elif 'lider' in domain or 'walmart' in domain:
        return scrape_lider(url)
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
