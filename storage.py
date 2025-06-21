import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    # fcntl is not available on Windows
    HAS_FCNTL = False
from config import config
from utils import sanitize_input

logger = logging.getLogger(__name__)

class SecureStorage:
    """Secure file-based storage for bot data with proper validation and error handling."""
    
    def __init__(self):
        self.data_dir = config.data_directory
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self.stats_file = os.path.join(self.data_dir, 'stats.json')
        self.backup_dir = os.path.join(self.data_dir, 'backups')
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize storage files with default data."""
        if not os.path.exists(self.users_file):
            self._write_json_file(self.users_file, {})
        
        if not os.path.exists(self.stats_file):
            default_stats = {
                'total_users': 0,
                'total_messages': 0,
                'total_promos_generated': 0,
                'total_posts_to_channels': 0,
                'start_time': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self._write_json_file(self.stats_file, default_stats)
    
    def _read_json_file(self, filepath: str) -> Dict[str, Any]:
        """Safely read JSON file with file locking (if available)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # File locking for concurrent access (Unix/Linux only)
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return data
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filepath}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return {}
    
    def _write_json_file(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Safely write JSON file with file locking (if available) and backup."""
        try:
            # Create backup first
            if os.path.exists(filepath):
                backup_path = os.path.join(
                    self.backup_dir, 
                    f"{os.path.basename(filepath)}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                )
                try:
                    with open(filepath, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
                except Exception:
                    pass  # Backup failed, but continue
            
            # Write new data
            with open(filepath, 'w', encoding='utf-8') as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(data, f, indent=2, ensure_ascii=False)
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            return True
        except Exception as e:
            logger.error(f"Error writing {filepath}: {e}")
            return False
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get user data with validation.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User data dictionary
        """
        if not isinstance(user_id, int) or user_id <= 0:
            return {}
        
        users_data = self._read_json_file(self.users_file)
        user_data = users_data.get(str(user_id), {})
        
        # Validate and sanitize user data
        return self._validate_user_data(user_data)
    
    def save_user_data(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Save user data with validation.
        
        Args:
            user_id: Telegram user ID
            user_data: User data to save
            
        Returns:
            True if saved successfully
        """
        if not isinstance(user_id, int) or user_id <= 0:
            return False
        
        # Validate and sanitize user data
        clean_data = self._validate_user_data(user_data)
        
        # Load existing data
        users_data = self._read_json_file(self.users_file)
        
        # Update user data
        users_data[str(user_id)] = clean_data
        users_data[str(user_id)]['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        return self._write_json_file(self.users_file, users_data)
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize user data for security."""
        if not isinstance(user_data, dict):
            return {}
        
        clean_data = {}
        
        # Validate language
        language = user_data.get('language', 'en')
        if language in ['en', 'ru', 'ro']:
            clean_data['language'] = language
        else:
            clean_data['language'] = 'en'
        
        # Validate products list
        products = user_data.get('products', [])
        if isinstance(products, list):
            clean_products = []
            for product in products[:config.max_products_per_user]:  # Limit products
                if isinstance(product, dict):
                    clean_product = self._validate_product(product)
                    if clean_product:
                        clean_products.append(clean_product)
            clean_data['products'] = clean_products
        else:
            clean_data['products'] = []
        
        # Validate channel info
        channel_info = user_data.get('channel_info', {})
        if isinstance(channel_info, dict):
            clean_channel = {}
            if 'channel_id' in channel_info:
                channel_id = sanitize_input(str(channel_info['channel_id']), 100)
                if channel_id:
                    clean_channel['channel_id'] = channel_id
            
            clean_channel['auto_post'] = bool(channel_info.get('auto_post', False))
            clean_data['channel_info'] = clean_channel
        
        # Validate post history
        post_history = user_data.get('post_history', [])
        if isinstance(post_history, list):
            clean_history = []
            for post in post_history[-50:]:  # Keep only last 50 posts
                if isinstance(post, dict) and 'product' in post:
                    clean_post = {
                        'product': sanitize_input(str(post.get('product', '')), 200),
                        'timestamp': str(post.get('timestamp', '')),
                        'status': sanitize_input(str(post.get('status', '')), 100)
                    }
                    clean_history.append(clean_post)
            clean_data['post_history'] = clean_history
        else:
            clean_data['post_history'] = []
        
        return clean_data
    
    def _validate_product(self, product: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Validate and sanitize product data."""
        if not isinstance(product, dict):
            return None
        
        required_fields = ['name', 'price', 'brand', 'category', 'features']
        clean_product = {}
        
        for field in required_fields:
            value = product.get(field, '')
            if isinstance(value, str) and value.strip():
                clean_product[field] = sanitize_input(value, 500)
            else:
                clean_product[field] = f"{field.title()} Not Found"
        
        # Validate URL if present
        url = product.get('url', '')
        if isinstance(url, str) and url.strip():
            clean_product['url'] = sanitize_input(url, 2000)
        
        return clean_product
    
    def update_stats(self, stat_type: str, increment: int = 1):
        """
        Update bot statistics.
        
        Args:
            stat_type: Type of statistic to update
            increment: Amount to increment by
        """
        valid_stats = [
            'total_users', 'total_messages', 'total_promos_generated', 
            'total_posts_to_channels'
        ]
        
        if stat_type not in valid_stats:
            return
        
        stats = self._read_json_file(self.stats_file)
        stats[stat_type] = stats.get(stat_type, 0) + increment
        stats['last_updated'] = datetime.now().isoformat()
        
        self._write_json_file(self.stats_file, stats)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return self._read_json_file(self.stats_file)
    
    def get_all_users_count(self) -> int:
        """Get total number of users."""
        users_data = self._read_json_file(self.users_file)
        return len(users_data)
    
    def cleanup_old_backups(self, days_to_keep: int = 7):
        """Clean up old backup files."""
        try:
            import time
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            for filename in os.listdir(self.backup_dir):
                filepath = os.path.join(self.backup_dir, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
                    logger.info(f"Removed old backup: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

# Global storage instance
storage = SecureStorage() 