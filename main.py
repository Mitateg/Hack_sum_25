#!/usr/bin/env python3
"""
Main entry point for the Telegram Promo Text Generator Bot
Modular architecture with security and error handling
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from bot import PromoBot

def setup_logging():
    """Setup logging configuration."""
    log_config = config.get_log_config()
    logging.basicConfig(**log_config)
    
    # Reduce noise from external libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def main():
    """Main function to start the bot."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("🚀 Starting Telegram Promo Bot...")
        logger.info(f"📁 Data directory: {config.data_directory}")
        logger.info(f"🌐 Web dashboard: {'Enabled' if config.web_dashboard_enabled else 'Disabled'}")
        
        # Create and run bot
        bot = PromoBot()
        
        # Note: Web dashboard temporarily disabled for testing
        # TODO: Implement proper async web dashboard integration
        
        # Run the bot
        logger.info("🤖 Bot is starting up...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 