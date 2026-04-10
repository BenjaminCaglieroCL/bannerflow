import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from django.conf import settings


HEADERS = {
    'User-Agent': getattr(settings, 'SCRAPER_USER_AGENT', 'Mozilla/5.0'),
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
    soup = _get_soup(url)
    data = {
        'store_name': 'MercadoLibre',
        'store_logo': 'mercadolibre',
        'source_url': url,
    }

    # Title
    title_el = soup.find('h1', class_='ui-pdp-title')
    if not title_el:
        title_el = soup.find('h1')
    data['title'] = title_el.get_text(strip=True) if title_el else ''

    # Image
    img = soup.find('img', class_='ui-pdp-image')
    if not img:
        img = soup.find('figure', class_='ui-pdp-gallery__figure')
        if img:
            img = img.find('img')
    data['image_url'] = img.get('src', '') or img.get('data-src', '') if img else ''

    # Prices
    price_el = soup.find('span', class_='andes-money-amount__fraction')
    if price_el:
        data['offer_price'] = _clean_price(price_el.get_text())

    original = soup.find('s', class_='andes-money-amount')
    if original:
        frac = original.find('span', class_='andes-money-amount__fraction')
        if frac:
            data['original_price'] = _clean_price(frac.get_text())
    
    if 'original_price' not in data:
        data['original_price'] = data.get('offer_price')

    # Fallback to OG
    if not data.get('image_url') or not data.get('title'):
        og = _extract_og(soup)
        data['title'] = data.get('title') or og.get('title', '')
        data['image_url'] = data.get('image_url') or og.get('image_url', '')

    return data


# --- Amazon ---

def scrape_amazon(url):
    soup = _get_soup(url)
    data = {
        'store_name': 'Amazon',
        'store_logo': 'amazon',
        'source_url': url,
    }

    title_el = soup.find('span', id='productTitle')
    data['title'] = title_el.get_text(strip=True) if title_el else ''

    img = soup.find('img', id='landingImage')
    if not img:
        img = soup.find('img', id='imgBlkFront')
    data['image_url'] = img.get('src', '') if img else ''

    price_whole = soup.find('span', class_='a-price-whole')
    price_frac = soup.find('span', class_='a-price-fraction')
    if price_whole:
        price_str = price_whole.get_text(strip=True).rstrip('.')
        if price_frac:
            price_str += '.' + price_frac.get_text(strip=True)
        data['offer_price'] = _clean_price(price_str)

    original = soup.find('span', class_='a-text-price')
    if original:
        off_screen = original.find('span', class_='a-offscreen')
        if off_screen:
            data['original_price'] = _clean_price(off_screen.get_text())

    if 'original_price' not in data:
        data['original_price'] = data.get('offer_price')

    if not data.get('image_url') or not data.get('title'):
        og = _extract_og(soup)
        data['title'] = data.get('title') or og.get('title', '')
        data['image_url'] = data.get('image_url') or og.get('image_url', '')

    return data


# --- Sodimac ---

def scrape_sodimac(url):
    soup = _get_soup(url)
    data = {
        'store_name': 'Sodimac',
        'store_logo': 'sodimac',
        'source_url': url,
    }

    title_el = soup.find('h1', class_='product-title') or soup.find('h1')
    data['title'] = title_el.get_text(strip=True) if title_el else ''

    img = soup.find('img', class_='product-image') or soup.find('img', id='product-image')
    data['image_url'] = img.get('src', '') if img else ''

    prices = soup.find_all('span', class_=re.compile(r'price|Price'))
    if len(prices) >= 2:
        data['original_price'] = _clean_price(prices[0].get_text())
        data['offer_price'] = _clean_price(prices[1].get_text())
    elif len(prices) == 1:
        data['offer_price'] = _clean_price(prices[0].get_text())
        data['original_price'] = data['offer_price']

    if not data.get('image_url') or not data.get('title'):
        og = _extract_og(soup)
        data['title'] = data.get('title') or og.get('title', '')
        data['image_url'] = data.get('image_url') or og.get('image_url', '')

    return data


# --- Líder / Walmart ---

def scrape_lider(url):
    soup = _get_soup(url)
    data = {
        'store_name': 'Líder',
        'store_logo': 'lider',
        'source_url': url,
    }

    title_el = soup.find('h1') or soup.find('span', class_=re.compile(r'product.*name', re.I))
    data['title'] = title_el.get_text(strip=True) if title_el else ''

    og = _extract_og(soup)
    data['image_url'] = og.get('image_url', '')
    data['title'] = data.get('title') or og.get('title', '')

    prices = soup.find_all('span', class_=re.compile(r'price|Price'))
    if len(prices) >= 2:
        data['original_price'] = _clean_price(prices[0].get_text())
        data['offer_price'] = _clean_price(prices[1].get_text())
    elif len(prices) == 1:
        data['offer_price'] = _clean_price(prices[0].get_text())
        data['original_price'] = data['offer_price']
    else:
        data['original_price'] = None
        data['offer_price'] = None

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
