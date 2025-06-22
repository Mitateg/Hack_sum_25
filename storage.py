import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import shutil
import hashlib
import tempfile
import re
import time
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    # fcntl is not available on Windows
    HAS_FCNTL = False
from config import config
from utils import advanced_sanitize_input, create_security_hash, verify_data_integrity

logger = logging.getLogger(__name__)

class SecureStorage:
    """Enhanced secure file-based storage with comprehensive security measures."""
    
    def __init__(self):
        self.data_dir = config.data_directory
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self.stats_file = os.path.join(self.data_dir, 'stats.json')
        self.backup_dir = os.path.join(self.data_dir, 'backups')
        self.audit_log = os.path.join(self.data_dir, 'audit.log')
        
        # Security settings
        self.max_file_size = 50 * 1024 * 1024  # 50MB max file size
        self.max_backup_age_days = 30
        self.max_backups_per_file = 100
        self.integrity_check_interval = 3600  # 1 hour
        self.last_integrity_check = 0
        
        # Ensure directories exist with proper permissions
        self._setup_directories()
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        # Setup audit logging
        self._setup_audit_logging()
    
    def _setup_directories(self):
        """Setup directories with proper permissions."""
        try:
            os.makedirs(self.data_dir, mode=0o750, exist_ok=True)
            os.makedirs(self.backup_dir, mode=0o750, exist_ok=True)
            
            # Set restrictive permissions on data directory
            if os.name != 'nt':  # Not Windows
                os.chmod(self.data_dir, 0o750)
                os.chmod(self.backup_dir, 0o750)
                
        except Exception as e:
            logger.error(f"Failed to setup directories: {e}")
            raise
    
    def _setup_audit_logging(self):
        """Setup audit logging for security events."""
        try:
            # Create audit logger
            audit_logger = logging.getLogger('audit')
            audit_logger.setLevel(logging.INFO)
            
            # Create file handler for audit log
            if not audit_logger.handlers:
                handler = logging.FileHandler(self.audit_log)
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                audit_logger.addHandler(handler)
                
        except Exception as e:
            logger.error(f"Failed to setup audit logging: {e}")
    
    def _log_audit_event(self, event_type: str, user_id: str = None, details: str = None):
        """Log security audit events."""
        try:
            audit_logger = logging.getLogger('audit')
            message = f"EVENT:{event_type}"
            if user_id:
                message += f" USER:{user_id}"
            if details:
                message += f" DETAILS:{details}"
            audit_logger.info(message)
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _initialize_files(self):
        """Initialize storage files with default data and integrity hashes."""
        if not os.path.exists(self.users_file):
            default_users = {}
            self._write_json_file_secure(self.users_file, default_users)
            self._log_audit_event("FILE_CREATED", details="users.json")
        
        if not os.path.exists(self.stats_file):
            default_stats = {
                'total_users': 0,
                'total_messages': 0,
                'total_promos_generated': 0,
                'total_posts_to_channels': 0,
                'start_time': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'security_version': '2.0'
            }
            self._write_json_file_secure(self.stats_file, default_stats)
            self._log_audit_event("FILE_CREATED", details="stats.json")
    
    def _check_file_integrity(self, filepath: str) -> bool:
        """Check file integrity using stored hash."""
        try:
            if not os.path.exists(filepath):
                return False
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > self.max_file_size:
                logger.error(f"File {filepath} exceeds maximum size limit")
                self._log_audit_event("INTEGRITY_VIOLATION", details=f"File too large: {filepath}")
                return False
            
            # Check if file is readable
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Validate JSON structure
            try:
                json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"File {filepath} contains invalid JSON")
                self._log_audit_event("INTEGRITY_VIOLATION", details=f"Invalid JSON: {filepath}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Integrity check failed for {filepath}: {e}")
            self._log_audit_event("INTEGRITY_CHECK_FAILED", details=f"{filepath}: {str(e)}")
            return False
    
    def _periodic_integrity_check(self):
        """Perform periodic integrity checks on data files."""
        current_time = time.time()
        if current_time - self.last_integrity_check < self.integrity_check_interval:
            return
        
        files_to_check = [self.users_file, self.stats_file]
        for filepath in files_to_check:
            if os.path.exists(filepath):
                if not self._check_file_integrity(filepath):
                    logger.error(f"Integrity check failed for {filepath}")
                    # Attempt to restore from backup
                    self._restore_from_backup(filepath)
        
        self.last_integrity_check = current_time
    
    def _restore_from_backup(self, filepath: str):
        """Restore file from most recent valid backup."""
        try:
            filename = os.path.basename(filepath)
            backup_pattern = f"{filename}."
            
            # Find all backups for this file
            backups = []
            for backup_file in os.listdir(self.backup_dir):
                if backup_file.startswith(backup_pattern):
                    backup_path = os.path.join(self.backup_dir, backup_file)
                    if self._check_file_integrity(backup_path):
                        backups.append((backup_path, os.path.getmtime(backup_path)))
            
            if backups:
                # Sort by modification time (newest first)
                backups.sort(key=lambda x: x[1], reverse=True)
                latest_backup = backups[0][0]
                
                # Restore from backup
                shutil.copy2(latest_backup, filepath)
                logger.info(f"Restored {filepath} from backup {latest_backup}")
                self._log_audit_event("FILE_RESTORED", details=f"From {latest_backup} to {filepath}")
            else:
                logger.error(f"No valid backups found for {filepath}")
                self._log_audit_event("RESTORE_FAILED", details=f"No valid backups for {filepath}")
                
        except Exception as e:
            logger.error(f"Failed to restore {filepath} from backup: {e}")
            self._log_audit_event("RESTORE_ERROR", details=f"{filepath}: {str(e)}")
    
    def _read_json_file_secure(self, filepath: str) -> Dict[str, Any]:
        """Safely read JSON file with enhanced security checks."""
        try:
            # Perform periodic integrity check
            self._periodic_integrity_check()
            
            # Check file integrity before reading
            if not self._check_file_integrity(filepath):
                logger.error(f"Integrity check failed for {filepath}")
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                # File locking for concurrent access (Unix/Linux only)
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                
                content = f.read()
                
                # Additional size check
                if len(content) > self.max_file_size:
                    logger.error(f"File content too large: {filepath}")
                    return {}
                
                data = json.loads(content)
                
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                # Validate data structure
                if not isinstance(data, dict):
                    logger.error(f"Invalid data structure in {filepath}")
                    return {}
                
                return data
                
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")
            self._log_audit_event("FILE_NOT_FOUND", details=filepath)
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filepath}: {e}")
            self._log_audit_event("JSON_DECODE_ERROR", details=f"{filepath}: {str(e)}")
            # Try to restore from backup
            self._restore_from_backup(filepath)
            return {}
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            self._log_audit_event("READ_ERROR", details=f"{filepath}: {str(e)}")
            return {}
    
    def _write_json_file_secure(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Safely write JSON file with enhanced security and atomic operations."""
        try:
            # Validate input data
            if not isinstance(data, dict):
                logger.error("Invalid data type for JSON file")
                return False
            
            # Serialize data to check size
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            if len(json_content.encode('utf-8')) > self.max_file_size:
                logger.error(f"Data too large for {filepath}")
                return False
            
            # Create backup first (if file exists)
            if os.path.exists(filepath):
                backup_success = self._create_backup(filepath)
                if not backup_success:
                    logger.warning(f"Backup creation failed for {filepath}, proceeding anyway")
            
            # Atomic write using temporary file
            temp_file = None
            try:
                # Create temporary file in the same directory
                temp_fd, temp_file = tempfile.mkstemp(
                    dir=os.path.dirname(filepath),
                    prefix=f".{os.path.basename(filepath)}_tmp_"
                )
                
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    
                    # Add metadata
                    data['_metadata'] = {
                        'last_modified': datetime.now().isoformat(),
                        'security_hash': create_security_hash(json_content),
                        'version': '2.0'
                    }
                    
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                    
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                # Atomic move
                if os.name == 'nt':  # Windows
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    os.rename(temp_file, filepath)
                else:  # Unix/Linux
                    os.rename(temp_file, filepath)
                    # Set restrictive permissions
                    os.chmod(filepath, 0o640)
                
                temp_file = None  # Successfully moved
                
                # Verify write
                if not self._check_file_integrity(filepath):
                    logger.error(f"Integrity check failed after writing {filepath}")
                    return False
                
                self._log_audit_event("FILE_WRITTEN", details=filepath)
                return True
                
            finally:
                # Clean up temporary file if it still exists
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Error writing {filepath}: {e}")
            self._log_audit_event("WRITE_ERROR", details=f"{filepath}: {str(e)}")
            return False
    
    def _create_backup(self, filepath: str) -> bool:
        """Create a backup of the file with enhanced reliability."""
        try:
            if not os.path.exists(filepath):
                return False
            
            filename = os.path.basename(filepath)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Include milliseconds
            backup_filename = f"{filename}.{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy with metadata preservation
            shutil.copy2(filepath, backup_path)
            
            # Verify backup integrity
            if not self._check_file_integrity(backup_path):
                os.remove(backup_path)
                logger.error(f"Backup integrity check failed for {backup_path}")
                return False
            
            # Set restrictive permissions
            if os.name != 'nt':  # Not Windows
                os.chmod(backup_path, 0o640)
            
            self._log_audit_event("BACKUP_CREATED", details=backup_path)
            
            # Clean up old backups
            self._cleanup_old_backups(filename)
            
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed for {filepath}: {e}")
            self._log_audit_event("BACKUP_FAILED", details=f"{filepath}: {str(e)}")
            return False
    
    def _cleanup_old_backups(self, filename: str):
        """Clean up old backups based on age and count limits."""
        try:
            backup_pattern = f"{filename}."
            backups = []
            
            for backup_file in os.listdir(self.backup_dir):
                if backup_file.startswith(backup_pattern) and backup_file.endswith('.bak'):
                    backup_path = os.path.join(self.backup_dir, backup_file)
                    mtime = os.path.getmtime(backup_path)
                    backups.append((backup_path, mtime))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Remove backups exceeding count limit
            if len(backups) > self.max_backups_per_file:
                for backup_path, _ in backups[self.max_backups_per_file:]:
                    os.remove(backup_path)
                    self._log_audit_event("BACKUP_REMOVED", details=f"Count limit: {backup_path}")
            
            # Remove backups exceeding age limit
            cutoff_time = time.time() - (self.max_backup_age_days * 24 * 3600)
            for backup_path, mtime in backups:
                if mtime < cutoff_time:
                    os.remove(backup_path)
                    self._log_audit_event("BACKUP_REMOVED", details=f"Age limit: {backup_path}")
                    
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data with enhanced validation and security."""
        if not isinstance(user_id, int) or user_id <= 0:
            self._log_audit_event("INVALID_USER_ID", details=str(user_id))
            return {}
        
        users_data = self._read_json_file_secure(self.users_file)
        user_data = users_data.get(str(user_id), {})
        
        # Enhanced validation and sanitization
        validated_data = self._validate_user_data_secure(user_data)
        
        self._log_audit_event("USER_DATA_READ", user_id=str(user_id))
        return validated_data
    
    def save_user_data(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Save user data with enhanced validation and security."""
        if not isinstance(user_id, int) or user_id <= 0:
            self._log_audit_event("INVALID_USER_ID", details=str(user_id))
            return False
        
        # Enhanced validation and sanitization
        clean_data = self._validate_user_data_secure(user_data)
        
        # Load existing data
        users_data = self._read_json_file_secure(self.users_file)
        
        # Update user data with timestamp and security info
        clean_data['last_updated'] = datetime.now().isoformat()
        clean_data['user_id'] = user_id
        clean_data['data_version'] = '2.0'
        
        users_data[str(user_id)] = clean_data
        
        # Save to file
        success = self._write_json_file_secure(self.users_file, users_data)
        
        if success:
            self._log_audit_event("USER_DATA_SAVED", user_id=str(user_id))
        else:
            self._log_audit_event("USER_DATA_SAVE_FAILED", user_id=str(user_id))
        
        return success
    
    def _validate_user_data_secure(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced validation and sanitization of user data."""
        if not isinstance(user_data, dict):
            return {}
        
        clean_data = {}
        
        # Validate language with whitelist
        language = user_data.get('language', 'en')
        if language in ['en', 'ru', 'ro']:
            clean_data['language'] = language
        else:
            clean_data['language'] = 'en'
            logger.warning(f"Invalid language detected: {language}")
        
        # Validate products list with enhanced checks
        products = user_data.get('products', [])
        if isinstance(products, list):
            clean_products = []
            for product in products[:config.max_products_per_user]:
                if isinstance(product, dict):
                    clean_product = self._validate_product_secure(product)
                    if clean_product:
                        clean_products.append(clean_product)
            clean_data['products'] = clean_products
        else:
            clean_data['products'] = []
        
        # Validate channel info with enhanced security
        channel_info = user_data.get('channel_info', {})
        if isinstance(channel_info, dict):
            clean_channel = {}
            
            # Validate channel ID
            if 'channel_id' in channel_info:
                channel_id = str(channel_info['channel_id'])
                # Enhanced channel ID validation
                if re.match(r'^@?[a-zA-Z0-9_]{1,32}$', channel_id) or re.match(r'^-?\d{10,}$', channel_id):
                    clean_channel['channel_id'] = advanced_sanitize_input(channel_id, 100)
                else:
                    logger.warning(f"Invalid channel ID format: {channel_id}")
            
            # Validate auto_post setting
            clean_channel['auto_post'] = bool(channel_info.get('auto_post', False))
            
            # Add security metadata
            clean_channel['last_verified'] = datetime.now().isoformat()
            
            clean_data['channel_info'] = clean_channel
        
        # Validate post history with size limits
        post_history = user_data.get('post_history', [])
        if isinstance(post_history, list):
            clean_history = []
            for post in post_history[-50:]:  # Keep only last 50 posts
                if isinstance(post, dict) and 'product' in post:
                    clean_post = {
                        'product': advanced_sanitize_input(str(post.get('product', '')), 200),
                        'timestamp': str(post.get('timestamp', '')),
                        'status': advanced_sanitize_input(str(post.get('status', '')), 100),
                        'hash': create_security_hash(str(post))  # Add integrity hash
                    }
                    clean_history.append(clean_post)
            clean_data['post_history'] = clean_history
        else:
            clean_data['post_history'] = []
        
        # Add security metadata
        clean_data['security_level'] = 'enhanced'
        clean_data['validation_timestamp'] = datetime.now().isoformat()
        
        return clean_data
    
    def _validate_product_secure(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced validation of product data with security checks."""
        if not isinstance(product, dict):
            return None
        
        clean_product = {}
        
        # Required fields with enhanced validation
        required_fields = ['name', 'price', 'url']
        for field in required_fields:
            if field not in product:
                return None
        
        # Validate and sanitize each field
        name = advanced_sanitize_input(str(product.get('name', '')), 200)
        if not name or len(name) < 2:
            return None
        clean_product['name'] = name
        
        price = advanced_sanitize_input(str(product.get('price', '')), 50)
        clean_product['price'] = price
        
        # Enhanced URL validation
        url = str(product.get('url', ''))
        from utils import validate_url_security
        is_valid, error_msg = validate_url_security(url)
        if not is_valid:
            logger.warning(f"Invalid product URL: {error_msg}")
            return None
        clean_product['url'] = url
        
        # Optional fields
        for field in ['brand', 'description', 'image_url']:
            if field in product:
                value = advanced_sanitize_input(str(product.get(field, '')), 500)
                if value:
                    clean_product[field] = value
        
        # Add security metadata
        clean_product['added_timestamp'] = product.get('added_timestamp', datetime.now().isoformat())
        clean_product['security_hash'] = create_security_hash(str(clean_product))
        
        return clean_product
    
    def update_stats_secure(self, stat_type: str, increment: int = 1):
        """Update statistics with enhanced security and validation."""
        if not isinstance(stat_type, str) or not isinstance(increment, int):
            self._log_audit_event("INVALID_STATS_UPDATE", details=f"Type: {stat_type}, Inc: {increment}")
            return
        
        # Whitelist of allowed stat types
        allowed_stats = [
            'total_users', 'total_messages', 'total_promos_generated', 
            'total_posts_to_channels', 'total_errors', 'total_security_violations'
        ]
        
        if stat_type not in allowed_stats:
            self._log_audit_event("INVALID_STAT_TYPE", details=stat_type)
            return
        
        stats = self._read_json_file_secure(self.stats_file)
        
        # Initialize stat if it doesn't exist
        if stat_type not in stats:
            stats[stat_type] = 0
        
        # Validate current value
        if not isinstance(stats[stat_type], (int, float)):
            stats[stat_type] = 0
        
        # Update with bounds checking
        old_value = stats[stat_type]
        new_value = max(0, old_value + increment)  # Prevent negative values
        
        # Sanity check for unrealistic increments
        if increment > 1000:
            logger.warning(f"Large stats increment detected: {stat_type} += {increment}")
            self._log_audit_event("LARGE_STATS_INCREMENT", details=f"{stat_type}: {increment}")
        
        stats[stat_type] = new_value
        stats['last_updated'] = datetime.now().isoformat()
        
        success = self._write_json_file_secure(self.stats_file, stats)
        
        if success:
            self._log_audit_event("STATS_UPDATED", details=f"{stat_type}: {old_value} -> {new_value}")
        else:
            self._log_audit_event("STATS_UPDATE_FAILED", details=stat_type)
    
    def get_stats_secure(self) -> Dict[str, Any]:
        """Get statistics with security validation."""
        stats = self._read_json_file_secure(self.stats_file)
        
        # Ensure all required stats exist
        required_stats = {
            'total_users': 0,
            'total_messages': 0,
            'total_promos_generated': 0,
            'total_posts_to_channels': 0,
            'start_time': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        for key, default_value in required_stats.items():
            if key not in stats:
                stats[key] = default_value
        
        self._log_audit_event("STATS_READ")
        return stats
    
    def get_all_users_count_secure(self) -> int:
        """Get total users count with validation."""
        users_data = self._read_json_file_secure(self.users_file)
        count = len(users_data)
        
        # Sanity check
        if count > 1000000:  # More than 1M users seems unrealistic
            logger.warning(f"Unusually high user count: {count}")
            self._log_audit_event("HIGH_USER_COUNT", details=str(count))
        
        return count
    
    def cleanup_old_backups_secure(self, days_to_keep: int = 7):
        """Enhanced cleanup of old backups with audit logging."""
        if not isinstance(days_to_keep, int) or days_to_keep < 1:
            days_to_keep = 7
        
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 3600)
            removed_count = 0
            
            for backup_file in os.listdir(self.backup_dir):
                if backup_file.endswith('.bak'):
                    backup_path = os.path.join(self.backup_dir, backup_file)
                    if os.path.getmtime(backup_path) < cutoff_time:
                        os.remove(backup_path)
                        removed_count += 1
            
            self._log_audit_event("BACKUP_CLEANUP", details=f"Removed {removed_count} old backups")
            logger.info(f"Cleaned up {removed_count} old backup files")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            self._log_audit_event("BACKUP_CLEANUP_FAILED", details=str(e))

# Global storage instance with enhanced security
storage = SecureStorage()

# Backwards compatibility
update_stats = storage.update_stats_secure
get_stats = storage.get_stats_secure
get_all_users_count = storage.get_all_users_count_secure
cleanup_old_backups = storage.cleanup_old_backups_secure 