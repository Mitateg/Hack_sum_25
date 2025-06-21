#!/usr/bin/env python3
"""
Setup script for Telegram Promo Text Generator Bot
Provides easy installation and configuration for hackathon demonstration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class BotSetup:
    """Setup class for easy bot installation and configuration."""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.data_dir = self.project_dir / "data"
        self.env_file = self.project_dir / ".env"
        self.env_example = self.project_dir / ".env.example"
    
    def check_python_version(self):
        """Check if Python version is compatible."""
        print("🐍 Checking Python version...")
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required!")
            print(f"Current version: {sys.version}")
            return False
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True
    
    def install_dependencies(self):
        """Install required dependencies."""
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories."""
        print("📁 Creating directories...")
        directories = [
            self.data_dir,
            self.data_dir / "backups",
            self.project_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            print(f"✅ Created directory: {directory}")
    
    def create_env_file(self):
        """Create environment file from template."""
        print("⚙️ Setting up environment configuration...")
        
        if self.env_file.exists():
            print("⚠️ .env file already exists, skipping creation")
            return True
        
        # Create .env.example if it doesn't exist
        if not self.env_example.exists():
            env_template = """# Required Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Configuration
WEB_DASHBOARD_PORT=8080
WEB_DASHBOARD_HOST=localhost
DATA_DIRECTORY=data
LOG_LEVEL=INFO
MAX_PRODUCTS_PER_USER=5
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
WEB_DASHBOARD_ENABLED=true
DEBUG_MODE=false
"""
            with open(self.env_example, 'w') as f:
                f.write(env_template)
        
        # Copy example to .env
        shutil.copy2(self.env_example, self.env_file)
        print("✅ Created .env file from template")
        print("⚠️ Please edit .env file with your API keys before running the bot!")
        return True
    
    def validate_env_file(self):
        """Validate environment file configuration."""
        print("🔍 Validating environment configuration...")
        
        if not self.env_file.exists():
            print("❌ .env file not found!")
            return False
        
        required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
        missing_vars = []
        
        with open(self.env_file, 'r') as f:
            content = f.read()
            for var in required_vars:
                if f"{var}=your_" in content or f"{var}=" not in content:
                    missing_vars.append(var)
        
        if missing_vars:
            print("❌ Missing or incomplete configuration:")
            for var in missing_vars:
                print(f"   - {var}")
            print("Please edit .env file with your actual API keys")
            return False
        
        print("✅ Environment configuration looks good")
        return True
    
    def test_installation(self):
        """Test if the bot can be imported and basic functionality works."""
        print("🧪 Testing installation...")
        
        try:
            # Test imports
            from config import config
            from translations import TRANSLATIONS
            from utils import sanitize_input
            from storage import storage
            
            print("✅ All modules imported successfully")
            
            # Test basic functionality
            test_text = sanitize_input("Test <script>alert('xss')</script>")
            if test_text == "Test alert('xss')":
                print("✅ Security functions working")
            
            # Test translations
            if len(TRANSLATIONS) >= 3:
                print("✅ Translations loaded")
            
            print("✅ Installation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Installation test failed: {e}")
            return False
    
    def show_next_steps(self):
        """Show next steps after setup."""
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Edit .env file with your API keys:")
        print("   - Get Telegram Bot Token from @BotFather")
        print("   - Get OpenAI API Key from https://platform.openai.com/")
        print("\n2. Run the bot:")
        print("   python main.py")
        print("\n3. Access web dashboard:")
        print("   http://localhost:8080")
        print("\n4. Test the bot in Telegram")
        print("\n🔧 Troubleshooting:")
        print("- Check logs in data/bot.log")
        print("- Verify environment variables in .env")
        print("- Ensure bot has proper permissions in channels")
    
    def run_setup(self):
        """Run the complete setup process."""
        print("🚀 Telegram Promo Bot Setup")
        print("=" * 40)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Setting up environment", self.create_env_file),
            ("Testing installation", self.test_installation),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        self.show_next_steps()
        return True

def main():
    """Main setup function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--validate":
            setup = BotSetup()
            if setup.validate_env_file():
                print("✅ Configuration is valid")
                sys.exit(0)
            else:
                print("❌ Configuration is invalid")
                sys.exit(1)
        elif sys.argv[1] == "--help":
            print("Telegram Promo Bot Setup Script")
            print("\nUsage:")
            print("  python setup.py          # Run full setup")
            print("  python setup.py --validate # Validate configuration")
            print("  python setup.py --help   # Show this help")
            return
    
    setup = BotSetup()
    success = setup.run_setup()
    
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")

if __name__ == "__main__":
    main() 