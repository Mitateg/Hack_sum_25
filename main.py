#!/usr/bin/env python3
"""
Main entry point for the Telegram Promo Text Generator Bot
Enhanced with security monitoring and structured logging
"""

import logging
import logging.handlers
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import signal
import atexit

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from bot import PromoBot

class SecurityLogFilter(logging.Filter):
    """Filter to identify and flag security-related log events."""
    
    def filter(self, record):
        # Flag security-related events
        security_keywords = [
            'security', 'blocked', 'suspicious', 'violation', 'attack',
            'unauthorized', 'invalid', 'malicious', 'injection', 'exploit'
        ]
        
        message = record.getMessage().lower()
        record.is_security = any(keyword in message for keyword in security_keywords)
        
        # Add structured data
        record.timestamp_iso = datetime.now().isoformat()
        record.bot_version = "2.0"
        
        return True

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for better log analysis."""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': record.timestamp_iso,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'bot_version': record.bot_version
        }
        
        # Add security flag if present
        if hasattr(record, 'is_security') and record.is_security:
            log_entry['security_event'] = True
            log_entry['priority'] = 'HIGH'
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'action'):
            log_entry['action'] = record.action
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_enhanced_logging():
    """Setup enhanced logging with security monitoring and structured output."""
    try:
        # Create logs directory
        log_dir = os.path.join(config.data_directory, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set restrictive permissions
        if os.name != 'nt':  # Not Windows
            os.chmod(log_dir, 0o750)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(SecurityLogFilter())
        
        # Main log file handler with rotation
        main_log_file = os.path.join(log_dir, 'bot.log')
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(StructuredFormatter())
        file_handler.addFilter(SecurityLogFilter())
        
        # Security log file handler
        security_log_file = os.path.join(log_dir, 'security.log')
        security_handler = logging.handlers.RotatingFileHandler(
            security_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(StructuredFormatter())
        
        # Security filter to only log security events
        class SecurityOnlyFilter(logging.Filter):
            def filter(self, record):
                return hasattr(record, 'is_security') and record.is_security
        
        security_handler.addFilter(SecurityOnlyFilter())
        
        # Error log file handler
        error_log_file = os.path.join(log_dir, 'errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        error_handler.addFilter(SecurityLogFilter())
        
        # Add all handlers to root logger
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(security_handler)
        root_logger.addHandler(error_handler)
        
        # Set restrictive permissions on log files
        if os.name != 'nt':  # Not Windows
            for log_file in [main_log_file, security_log_file, error_log_file]:
                if os.path.exists(log_file):
                    os.chmod(log_file, 0o640)
        
        # Reduce noise from external libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        
        # Create performance logger
        perf_logger = logging.getLogger('performance')
        perf_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'performance.log'),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setFormatter(StructuredFormatter())
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        
        return True
        
    except Exception as e:
        print(f"Failed to setup enhanced logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return False

def log_system_info():
    """Log system information for debugging and monitoring."""
    logger = logging.getLogger(__name__)
    
    try:
        import platform
        
        # Basic system information that's always available
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor() or 'Unknown'
        }
        
        # Try to add psutil information if available
        try:
            import psutil
            system_info.update({
                'memory_total': f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
                'memory_available': f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
                'cpu_count': psutil.cpu_count(),
                'psutil_available': True
            })
            
            # Try disk usage (handle different OS paths)
            try:
                if platform.system() == 'Windows':
                    disk_usage = psutil.disk_usage('C:\\')
                else:
                    disk_usage = psutil.disk_usage('/')
                system_info['disk_usage'] = f"{disk_usage.percent}%"
            except Exception:
                system_info['disk_usage'] = 'N/A'
                
        except ImportError:
            system_info['psutil_available'] = False
            logger.info("psutil not available - basic monitoring only")
        
        logger.info(f"System Info: {json.dumps(system_info)}")
        
    except Exception as e:
        logger.warning(f"Failed to collect system info: {e}")

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # Log shutdown event
        logger.info("Bot shutdown initiated by signal")
        
        # Cleanup and exit
        sys.exit(0)
    
    # Handle SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)

def setup_cleanup_handlers():
    """Setup cleanup handlers for application exit."""
    def cleanup():
        logger = logging.getLogger(__name__)
        logger.info("Application cleanup initiated")
        
        try:
            # Cleanup storage backups
            from storage import storage
            storage.cleanup_old_backups_secure(7)
            
            # Log final statistics
            stats = storage.get_stats_secure()
            logger.info(f"Final statistics: {json.dumps(stats)}")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        logger.info("Application cleanup completed")
    
    atexit.register(cleanup)

def monitor_bot_health(bot_instance):
    """Monitor bot health and log performance metrics."""
    logger = logging.getLogger('performance')
    
    try:
        import time
        start_time = time.time()
        
        # Basic metrics that are always available
        metrics = {
            'uptime_seconds': time.time() - start_time,
            'monitoring_available': False
        }
        
        # Try to add psutil metrics if available
        try:
            import psutil
            process = psutil.Process()
            
            metrics.update({
                'memory_usage_mb': process.memory_info().rss / (1024 * 1024),
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'monitoring_available': True
            })
            
            # Try to get open files count (may not work on all systems)
            try:
                metrics['open_files'] = len(process.open_files())
            except (psutil.AccessDenied, AttributeError):
                metrics['open_files'] = 'N/A'
                
        except ImportError:
            logger.info("psutil not available - basic health monitoring only")
        except Exception as e:
            logger.warning(f"Error collecting process metrics: {e}")
        
        logger.info(f"Bot health metrics: {json.dumps(metrics)}")
        
    except Exception as e:
        logger.warning(f"Health monitoring error: {e}")

def main():
    """Enhanced main function with comprehensive error handling and monitoring."""
    bot_instance = None
    logger = None
    
    try:
        # Setup enhanced logging first
        logging_success = setup_enhanced_logging()
        logger = logging.getLogger(__name__)
        
        if logging_success:
            logger.info("✅ Enhanced logging system initialized")
        else:
            logger.warning("⚠️ Fallback to basic logging")
        
        # Setup signal and cleanup handlers
        setup_signal_handlers()
        setup_cleanup_handlers()
        
        # Log startup information
        logger.info("🚀 Starting Telegram Promo Bot v2.0...")
        logger.info(f"📁 Data directory: {config.data_directory}")
        logger.info(f"🔒 Security level: Enhanced")
        
        # Log system information
        log_system_info()
        
        # Validate configuration
        if not config.telegram_token:
            raise ValueError("Telegram token not configured")
        
        if not config.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        logger.info("✅ Configuration validated")
        
        # Create and initialize bot
        logger.info("🤖 Initializing bot...")
        bot_instance = PromoBot()
        
        # Log security features
        security_features = [
            "Advanced rate limiting",
            "Input sanitization",
            "URL security validation", 
            "File integrity checking",
            "Audit logging",
            "Automatic backups",
            "Error monitoring"
        ]
        
        logger.info(f"🔐 Security features enabled: {', '.join(security_features)}")
        
        # Start health monitoring
        monitor_bot_health(bot_instance)
        
        # Run the bot
        logger.info("🟢 Bot is starting up...")
        logger.info("📊 Monitoring: Logs, Security, Performance")
        
        # Log successful startup
        logger.info("✅ Bot startup completed successfully")
        
        # Start the bot
        bot_instance.run()
        
    except KeyboardInterrupt:
        if logger:
            logger.info("🛑 Bot stopped by user (Ctrl+C)")
        else:
            print("🛑 Bot stopped by user")
        
    except ValueError as e:
        if logger:
            logger.error(f"❌ Configuration error: {e}")
        else:
            print(f"❌ Configuration error: {e}")
        sys.exit(1)
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
            logger.error("💥 Bot crashed - check logs for details")
        else:
            print(f"❌ Fatal error: {e}")
        sys.exit(1)
        
    finally:
        # Final cleanup and logging
        if logger:
            logger.info("🔄 Bot shutdown process completed")
            
            # Log final health metrics
            if bot_instance:
                monitor_bot_health(bot_instance)

if __name__ == "__main__":
    main() 