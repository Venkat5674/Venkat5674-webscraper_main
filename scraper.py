import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def is_valid_url(url):
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def clean_text(text):
    """Clean and normalize text content."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def scrape_website(url):
    """
    Scrape website content.
    
    Args:
        url (str): URL to scrape
        
    Returns:
        dict: Scraped data including title, metadata, links, text, images, and raw HTML
    """
    # Validate URL
    if not is_valid_url(url):
        raise ValueError("Invalid URL format")
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Make request to the URL
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # Raise exception for HTTP errors
    
    # Get the HTML content
    html_content = response.text
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Extract page title
    title = soup.title.string if soup.title else "No title found"
    
    # Extract metadata
    meta_data = {}
    for meta in soup.find_all('meta'):
        if meta.get('name'):
            meta_data[meta.get('name')] = meta.get('content', '')
        elif meta.get('property'):
            meta_data[meta.get('property')] = meta.get('content', '')
    
    # Extract links
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convert relative URLs to absolute URLs
        if not bool(urlparse(href).netloc):
            href = urljoin(url, href)
        if is_valid_url(href):
            links.append(href)
    
    # Extract text content
    text_content = clean_text(soup.get_text())
    
    # Extract images
    images = []
    for img in soup.find_all('img', src=True):
        src = img['src']
        # Convert relative URLs to absolute URLs
        if not bool(urlparse(src).netloc):
            src = urljoin(url, src)
        if is_valid_url(src):
            images.append(src)
    
    # Prepare the result
    result = {
        'title': title,
        'metaData': meta_data,
        'links': links[:100],  # Limit to first 100 links to avoid overwhelming frontend
        'textContent': text_content[:10000],  # Limit text content length
        'images': images[:20],  # Limit to first 20 images
        'rawHtml': html_content[:50000]  # Limit raw HTML length
    }
    
    return result

def extract_specific_data(soup, selectors):
    """
    Extract data using specific CSS selectors.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        selectors (dict): Dictionary mapping data types to CSS selectors
        
    Returns:
        dict: Extracted data
    """
    results = {}
    
    for data_type, selector in selectors.items():
        elements = soup.select(selector)
        if elements:
            if isinstance(elements, list):
                results[data_type] = [clean_text(el.get_text()) for el in elements]
            else:
                results[data_type] = clean_text(elements.get_text())
        else:
            results[data_type] = []
            
    return results

# Additional function to extract specific data types, like product information
def scrape_product_info(url):
    """
    Specialized scraper for product pages.
    
    Args:
        url (str): URL to product page
        
    Returns:
        dict: Product information
    """
    # Basic scraping
    data = scrape_website(url)
    soup = BeautifulSoup(data['rawHtml'], 'lxml')
    
    # Common selectors for product information
    selectors = {
        'productName': 'h1.product-title, .product-name, #productTitle',
        'price': '.price, .product-price, #priceblock_ourprice',
        'description': '.product-description, #productDescription, .description',
        'reviews': '.review, .comment, .user-review'
    }
    
    # Extract product-specific data
    product_data = extract_specific_data(soup, selectors)
    
    # Merge with basic data
    data.update({
        'productInfo': product_data
    })
    
    return data