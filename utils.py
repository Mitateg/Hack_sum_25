import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging
from typing import Optional, Dict, Any, Tuple
import time
from functools import wraps

logger = logging.getLogger(__name__)

# Security: Rate limiting decorator
def rate_limit(max_calls: int = 10, window: int = 60):
    """Rate limiting decorator to prevent abuse."""
    calls = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            user_id = kwargs.get('user_id') or (args[1].effective_user.id if len(args) > 1 else 'unknown')
            
            # Clean old entries
            calls[user_id] = [call_time for call_time in calls.get(user_id, []) if now - call_time < window]
            
            # Check rate limit
            if len(calls.get(user_id, [])) >= max_calls:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return None
            
            # Record this call
            calls.setdefault(user_id, []).append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for security.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove potential harmful characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    text = text[:max_length]
    
    # Strip whitespace
    text = text.strip()
    
    return text

def is_valid_url(url: str) -> bool:
    """
    Validate URL with security checks.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and safe
    """
    if not isinstance(url, str):
        return False
    
    try:
        # Basic URL validation
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        
        # Security: Only allow HTTP/HTTPS
        if result.scheme not in ['http', 'https']:
            return False
        
        # Security: Block localhost and private IPs
        if any(blocked in result.netloc.lower() for blocked in ['localhost', '127.0.0.1', '192.168.', '10.', '172.']):
            return False
        
        return True
        
    except Exception:
        return False

def extract_domain(url: str) -> str:
    """
    Safely extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name or empty string
    """
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

class SecureWebScraper:
    """Secure web scraping with proper error handling and limits."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        self.max_content_length = 5 * 1024 * 1024  # 5MB limit
    
    def scrape_product_info(self, url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Securely scrape product information from URL.
        
        Args:
            url: Product URL to scrape
            
        Returns:
            Tuple of (product_data, error_message)
        """
        if not is_valid_url(url):
            return None, "Invalid or unsafe URL"
        
        try:
            # Make request with security limits
            response = self.session.get(
                url, 
                timeout=self.timeout,
                stream=True,
                allow_redirects=True
            )
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_length:
                return None, "Content too large"
            
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content[:self.max_content_length], 'html.parser')
            
            # Extract product information
            raw_data = {
                'url': url,
                'title': self._extract_title(soup),
                'price': self._extract_price(soup),
                'description': self._extract_description(soup),
                'image_url': self._extract_image(soup, url),
                'brand': self._extract_brand(soup),
                'domain': extract_domain(url)
            }
            
            return raw_data, None
            
        except requests.exceptions.Timeout:
            return None, "Connection timeout - website took too long to respond"
        except requests.exceptions.ConnectionError:
            return None, "Connection failed - unable to reach website"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                return None, "Access denied - website blocked automated access"
            elif e.response.status_code == 404:
                return None, "Page not found - invalid product link"
            else:
                return None, f"HTTP error {e.response.status_code}"
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return None, f"Scraping failed: {str(e)}"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title safely."""
        selectors = [
            'h1[data-automation-id="product-title"]',
            'h1.product-title',
            'h1#product-title', 
            '.product-name h1',
            '.product-title',
            'h1[class*="title"]',
            'h1[class*="product"]',
            'title',
            'h1'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    title = sanitize_input(element.get_text().strip(), 200)
                    if title:
                        return title
            except Exception:
                continue
        
        return "Product Title Not Found"
    
    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract product price safely."""
        selectors = [
            '.price-current',
            '.price',
            '.product-price',
            '[class*="price"]',
            '[data-testid*="price"]',
            '.cost',
            '.amount'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    # Look for price patterns
                    price_match = re.search(r'[\$€£¥₽]\s*[\d,]+\.?\d*|\d+[,.]?\d*\s*[\$€£¥₽]', text)
                    if price_match:
                        return sanitize_input(price_match.group(), 50)
            except Exception:
                continue
        
        return "Price Not Found"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description safely."""
        selectors = [
            '.product-description',
            '.description',
            '[class*="description"]',
            '.product-details',
            '.product-info',
            'meta[name="description"]'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        desc = element.get('content', '').strip()
                    else:
                        desc = element.get_text().strip()
                    
                    if desc and len(desc) > 20:
                        return sanitize_input(desc, 500)
            except Exception:
                continue
        
        return "Description Not Found"
    
    def _extract_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract product image URL safely."""
        selectors = [
            '.product-image img',
            '.main-image img',
            '[class*="product"] img',
            'img[alt*="product"]',
            'img[class*="product"]'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    src = element.get('src') or element.get('data-src')
                    if src:
                        full_url = urljoin(base_url, src)
                        if is_valid_url(full_url):
                            return full_url
            except Exception:
                continue
        
        return None
    
    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract product brand safely."""
        selectors = [
            '.brand',
            '.product-brand',
            '[class*="brand"]',
            'meta[property="product:brand"]',
            'span[itemprop="brand"]'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        brand = element.get('content', '').strip()
                    else:
                        brand = element.get_text().strip()
                    
                    if brand and len(brand) < 50:
                        return sanitize_input(brand, 50)
            except Exception:
                continue
        
        return "Brand Not Found"

def generate_hashtags(product_name: str, max_hashtags: int = 6) -> str:
    """
    Generate relevant hashtags for the product safely.
    
    Args:
        product_name: Product name to generate hashtags from
        max_hashtags: Maximum number of hashtags to generate
        
    Returns:
        String of hashtags
    """
    if not isinstance(product_name, str):
        return ""
    
    # Sanitize input
    product_name = sanitize_input(product_name, 200)
    
    # Basic hashtag generation
    words = re.sub(r'[^\w\s]', ' ', product_name.lower()).split()
    hashtags = []
    
    # Add product-specific hashtags
    for word in words:
        if len(word) > 2 and word.isalpha():  # Only alphabetic words > 2 chars
            hashtags.append(f"#{word}")
    
    # Add general marketing hashtags
    hashtags.extend(["#promo", "#sale", "#newproduct", "#shopping"])
    
    # Limit and return
    return " ".join(hashtags[:max_hashtags])

# Global scraper instance
scraper = SecureWebScraper() 