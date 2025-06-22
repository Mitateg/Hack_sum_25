import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging
from typing import Optional, Dict, Any, Tuple, List
import time
from functools import wraps
import hashlib
import ipaddress
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Enhanced rate limiting with multiple strategies
class AdvancedRateLimit:
    """Advanced rate limiting with multiple strategies and persistent storage."""
    
    def __init__(self):
        self.calls = {}
        self.blocked_users = {}
        self.suspicious_patterns = {}
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is temporarily blocked."""
        if user_id in self.blocked_users:
            if time.time() > self.blocked_users[user_id]:
                del self.blocked_users[user_id]
                return False
            return True
        return False
    
    def block_user(self, user_id: str, duration: int = 60):
        """Block user for specified duration (seconds) - much shorter now."""
        self.blocked_users[user_id] = time.time() + duration
        logger.warning(f"User {user_id} blocked for {duration} seconds due to rate limit violation")
    
    def check_suspicious_pattern(self, user_id: str, action: str) -> bool:
        """Check for suspicious usage patterns - much more lenient."""
        now = time.time()
        key = f"{user_id}:{action}"
        
        if key not in self.suspicious_patterns:
            self.suspicious_patterns[key] = []
        
        # Clean old entries
        self.suspicious_patterns[key] = [
            t for t in self.suspicious_patterns[key] 
            if now - t < 3600  # Keep last hour
        ]
        
        # Check for rapid repeated actions - increased threshold
        if len(self.suspicious_patterns[key]) > 50:  # More than 50 same actions per hour (was 10)
            return True
        
        self.suspicious_patterns[key].append(now)
        return False

# Global rate limiter instance
rate_limiter = AdvancedRateLimit()

def rate_limit(max_calls: int = 50, window: int = 60, action: str = "general"):
    """Enhanced rate limiting decorator with blocking and pattern detection - much more lenient."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user ID
            user_id = 'unknown'
            if len(args) > 1 and hasattr(args[1], 'effective_user'):
                user_id = str(args[1].effective_user.id)
            elif 'user_id' in kwargs:
                user_id = str(kwargs['user_id'])
            
            # Check if user is blocked
            if rate_limiter.is_user_blocked(user_id):
                logger.warning(f"Blocked user {user_id} attempted {action}")
                return None
            
            # Check suspicious patterns - more lenient
            if rate_limiter.check_suspicious_pattern(user_id, action):
                rate_limiter.block_user(user_id, 60)  # Block for only 1 minute (was 10)
                logger.error(f"Suspicious pattern detected for user {user_id}, action: {action}")
                return None
            
            now = time.time()
            
            # Clean old entries
            if user_id not in rate_limiter.calls:
                rate_limiter.calls[user_id] = []
            
            rate_limiter.calls[user_id] = [
                call_time for call_time in rate_limiter.calls[user_id] 
                if now - call_time < window
            ]
            
            # Check rate limit - much more lenient
            if len(rate_limiter.calls[user_id]) >= max_calls:
                logger.warning(f"Rate limit exceeded for user {user_id}, action: {action}")
                # Much shorter blocking: 30 seconds max
                rate_limiter.block_user(user_id, 30)
                return None
            
            # Record this call
            rate_limiter.calls[user_id].append(now)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in rate-limited function {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator

def advanced_sanitize_input(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Advanced input sanitization with multiple security layers.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow basic HTML tags
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes and control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Remove potential script injections
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'on\w+\s*=',  # Event handlers
        r'expression\s*\(',  # CSS expressions
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    if not allow_html:
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove potential harmful characters
        text = re.sub(r'[<>"\'\`]', '', text)
    else:
        # Allow only safe HTML tags
        allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'br', 'p']
        text = re.sub(r'<(?!/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]+>', '', text)
    
    # Limit length
    text = text[:max_length]
    
    # Strip whitespace
    text = text.strip()
    
    return text

def validate_url_security(url: str) -> Tuple[bool, str]:
    """
    Comprehensive URL security validation.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(url, str):
        return False, "URL must be a string"
    
    # Length check
    if len(url) > 2048:
        return False, "URL too long"
    
    try:
        result = urlparse(url)
        
        # Basic structure validation
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL structure"
        
        # Protocol validation
        if result.scheme not in ['http', 'https']:
            return False, "Only HTTP/HTTPS protocols allowed"
        
        # Hostname validation
        hostname = result.netloc.split(':')[0].lower()
        
        # Block localhost and private networks
        private_patterns = [
            'localhost', '127.', '192.168.', '10.', '172.16.', '172.17.',
            '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
            '172.30.', '172.31.', '169.254.', '::1', 'fe80:'
        ]
        
        if any(pattern in hostname for pattern in private_patterns):
            return False, "Private/local network addresses not allowed"
        
        # Try to resolve IP and check if it's private
        try:
            import socket
            ip = socket.gethostbyname(hostname)
            if ipaddress.ip_address(ip).is_private:
                return False, "Resolved to private IP address"
        except:
            pass  # DNS resolution failed, but continue
        
        # Block suspicious domains
        suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'short.link', 't.co',  # URL shorteners
            'ngrok.io', 'localtunnel.me',  # Tunneling services
        ]
        
        if any(domain in hostname for domain in suspicious_domains):
            return False, "Suspicious domain detected"
        
        # Check for suspicious patterns in URL
        suspicious_patterns = [
            r'\.exe(\?|$)', r'\.bat(\?|$)', r'\.scr(\?|$)', r'\.msi(\?|$)',  # Executable files
            r'javascript:', r'data:', r'file:',  # Dangerous protocols
            r'[<>"\']',  # HTML injection attempts
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False, "Suspicious URL pattern detected"
        
        return True, ""
        
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

def create_security_hash(data: str) -> str:
    """Create a security hash for data integrity verification."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def verify_data_integrity(data: str, expected_hash: str) -> bool:
    """Verify data integrity using hash comparison."""
    return create_security_hash(data) == expected_hash

class SecureWebScraper:
    """Enhanced secure web scraping with comprehensive security measures."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.timeout = 15
        self.max_content_length = 10 * 1024 * 1024  # 10MB limit
        self.max_redirects = 5
        self.allowed_content_types = ['text/html', 'application/xhtml+xml']
        self.request_count = 0
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
    
    def _rate_limit_request(self):
        """Implement rate limiting for requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    @rate_limit(max_calls=5, window=60, action="web_scraping")
    async def scrape_product_info(self, url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Securely scrape product information with enhanced security.
        
        Args:
            url: Product URL to scrape
            
        Returns:
            Tuple of (product_data, error_message)
        """
        # Enhanced URL validation
        is_valid, error_msg = validate_url_security(url)
        if not is_valid:
            logger.warning(f"URL security validation failed: {error_msg}")
            return None, f"Security check failed: {error_msg}"
        
        # Rate limit requests
        self._rate_limit_request()
        
        try:
            # Make request with enhanced security
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
                verify=True  # Verify SSL certificates
            )
            
            # Check redirect count
            if len(response.history) > self.max_redirects:
                return None, "Too many redirects"
            
            # Validate final URL after redirects
            final_url = response.url
            is_valid, error_msg = validate_url_security(final_url)
            if not is_valid:
                return None, f"Redirect security check failed: {error_msg}"
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(allowed in content_type for allowed in self.allowed_content_types):
                return None, f"Unsupported content type: {content_type}"
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_length:
                return None, "Content too large"
            
            response.raise_for_status()
            
            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_content_length:
                    return None, "Content size exceeded limit"
            
            # Parse content safely
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove potentially dangerous elements
            for tag in soup(['script', 'style', 'iframe', 'object', 'embed']):
                tag.decompose()
            
            # Extract product information with enhanced validation
            raw_data = {
                'url': final_url,
                'title': self._extract_title_secure(soup),
                'price': self._extract_price_secure(soup),
                'description': self._extract_description_secure(soup),
                'image_url': self._extract_image_secure(soup, final_url),
                'brand': self._extract_brand_secure(soup),
                'domain': urlparse(final_url).netloc.lower(),
                'scraped_at': datetime.now().isoformat(),
                'security_hash': create_security_hash(str(soup))
            }
            
            # Validate all extracted data
            for key, value in raw_data.items():
                if isinstance(value, str):
                    raw_data[key] = advanced_sanitize_input(value, 500)
            
            logger.info(f"Successfully scraped product from {urlparse(final_url).netloc}")
            return raw_data, None
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout scraping {url}")
            return None, "Connection timeout - website took too long to respond"
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error scraping {url}")
            return None, "Connection failed - unable to reach website"
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error scraping {url}: {e}")
            if e.response.status_code == 403:
                return None, "Access denied - website blocked automated access"
            elif e.response.status_code == 404:
                return None, "Page not found - invalid product link"
            elif e.response.status_code == 429:
                return None, "Rate limited - too many requests to this website"
            else:
                return None, f"HTTP error {e.response.status_code}"
        except Exception as e:
            logger.error(f"Unexpected scraping error for {url}: {e}")
            return None, f"Scraping failed: {str(e)[:100]}"
    
    def _extract_title_secure(self, soup: BeautifulSoup) -> str:
        """Extract product title with enhanced security."""
        selectors = [
            'h1[data-automation-id="product-title"]',
            'h1.product-title',
            'h1#product-title', 
            '.product-name h1',
            '.product-title',
            'h1[class*="title"]',
            'h1[class*="product"]',
            '[data-testid*="title"]',
            '.pdp-product-name',
            'title',
            'h1'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    title = advanced_sanitize_input(element.get_text().strip(), 200)
                    if title and len(title) > 3:  # Minimum length check
                        return title
            except Exception:
                continue
        
        return "Product"
    
    def _extract_price_secure(self, soup: BeautifulSoup) -> str:
        """Extract price with enhanced security and validation."""
        price_selectors = [
            '[data-automation-id*="price"]',
            '.price',
            '.product-price',
            '[class*="price"]',
            '[id*="price"]',
            '.cost',
            '.amount',
            '[data-testid*="price"]'
        ]
        
        for selector in price_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    # Look for price patterns
                    price_match = re.search(r'[\d,]+\.?\d*\s*(?:lei|ron|eur|usd|\$|€|₽)', text, re.IGNORECASE)
                    if price_match:
                        price = advanced_sanitize_input(price_match.group(), 50)
                        if price:
                            return price
            except Exception:
                continue
        
        return "Price not available"
    
    def _extract_description_secure(self, soup: BeautifulSoup) -> str:
        """Extract description with enhanced security."""
        desc_selectors = [
            '[data-automation-id*="description"]',
            '.product-description',
            '.description',
            '[class*="description"]',
            '.product-details',
            '.product-info',
            '[data-testid*="description"]'
        ]
        
        for selector in desc_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Remove nested script/style tags
                    for tag in element(['script', 'style']):
                        tag.decompose()
                    
                    text = element.get_text().strip()
                    if text and len(text) > 20:  # Minimum meaningful length
                        desc = advanced_sanitize_input(text, 500)
                        if desc:
                            return desc
            except Exception:
                continue
        
        return "No description available"
    
    def _extract_image_secure(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract image URL with enhanced security validation."""
        img_selectors = [
            'img[data-automation-id*="product"]',
            '.product-image img',
            '.main-image img',
            '[class*="product"] img',
            'img[alt*="product"]',
            'img'
        ]
        
        for selector in img_selectors:
            try:
                elements = soup.select(selector)
                for img in elements:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(base_url, src)
                        
                        # Validate image URL
                        is_valid, _ = validate_url_security(src)
                        if is_valid and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            return src
            except Exception:
                continue
        
        return None
    
    def _extract_brand_secure(self, soup: BeautifulSoup) -> str:
        """Extract brand with enhanced security."""
        brand_selectors = [
            '[data-automation-id*="brand"]',
            '.brand',
            '.manufacturer',
            '[class*="brand"]',
            '[data-testid*="brand"]',
            'meta[property="product:brand"]'
        ]
        
        for selector in brand_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        brand = element.get('content', '').strip()
                    else:
                        brand = element.get_text().strip()
                    
                    if brand:
                        brand = advanced_sanitize_input(brand, 100)
                        if brand and len(brand) > 1:
                            return brand
            except Exception:
                continue
        
        return "Unknown brand"

def generate_secure_hashtags(product_name: str, max_hashtags: int = 6) -> str:
    """Generate hashtags with enhanced security validation."""
    if not isinstance(product_name, str):
        return ""
    
    # Sanitize input
    product_name = advanced_sanitize_input(product_name, 200)
    
    if not product_name:
        return ""
    
    # Extract meaningful words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', product_name)
    
    hashtags = []
    for word in words[:max_hashtags]:
        # Additional validation for hashtag content
        if re.match(r'^[a-zA-Z0-9_]+$', word) and len(word) >= 3:
            hashtags.append(f"#{word.capitalize()}")
    
    return " ".join(hashtags)

# Global secure scraper instance
scraper = SecureWebScraper()

# Backwards compatibility
sanitize_input = advanced_sanitize_input
is_valid_url = lambda url: validate_url_security(url)[0] 