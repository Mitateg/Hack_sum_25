import os
import logging
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Secure configuration management for the Telegram bot."""
    
    def __init__(self):
        self.telegram_token = self._get_required_env('TELEGRAM_BOT_TOKEN')
        self.openai_api_key = self._get_required_env('OPENAI_API_KEY')
        self.web_dashboard_port = int(os.getenv('WEB_DASHBOARD_PORT', '8080'))
        self.web_dashboard_host = os.getenv('WEB_DASHBOARD_HOST', 'localhost')
        self.data_directory = os.getenv('DATA_DIRECTORY', 'data')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.max_products_per_user = int(os.getenv('MAX_PRODUCTS_PER_USER', '5'))
        self.rate_limit_requests = int(os.getenv('RATE_LIMIT_REQUESTS', '10'))
        self.rate_limit_window = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
        
        # Mastodon configuration (optional)
        self.mastodon_instance = os.getenv('MASTODON_INSTANCE', '')
        self.mastodon_access_token = os.getenv('MASTODON_ACCESS_TOKEN', '')
        
        # Security settings
        self.web_dashboard_enabled = os.getenv('WEB_DASHBOARD_ENABLED', 'true').lower() == 'true'
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        # Validate configuration
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable with validation."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not found")
        return value
    
    def _validate_config(self):
        """Validate configuration values for security."""
        # Validate tokens are not empty or default values
        if len(self.telegram_token) < 10:
            raise ValueError("Invalid Telegram bot token")
        
        if len(self.openai_api_key) < 10:
            raise ValueError("Invalid OpenAI API key")
        
        # Validate port range
        if not 1024 <= self.web_dashboard_port <= 65535:
            raise ValueError("Web dashboard port must be between 1024-65535")
        
        # Validate Mastodon configuration if provided
        if self.mastodon_instance and not self.mastodon_instance.startswith(('http://', 'https://')):
            raise ValueError("Mastodon instance must include protocol (http:// or https://)")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_directory, exist_ok=True)
    
    def has_mastodon_config(self) -> bool:
        """Check if Mastodon is properly configured."""
        return bool(self.mastodon_instance and self.mastodon_access_token)
    
    def get_log_config(self) -> dict:
        """Get logging configuration."""
        return {
            'level': getattr(logging, self.log_level.upper()),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'filename': os.path.join(self.data_directory, 'bot.log'),
            'filemode': 'a'
        }

# Global config instance
config = Config() 