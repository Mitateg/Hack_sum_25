import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

# Language translations
TRANSLATIONS = {
    'en': {
        'welcome_title': '🚀 **Welcome to the Promo Text Generator Bot!** 🚀',
        'welcome_message': 'I can help you create amazing promotional posts for your products!\n\nChoose your language first:',
        'language_selected': '✅ Language set to English!\n\nChoose an option below to get started:',
        'main_menu_title': '🚀 **Promo Text Generator Bot - Main Menu**',
        'main_menu_subtitle': 'Choose an option to continue:',
        'generate_promo': '🎯 Generate Promo Text',
        'categories': '📝 Product Categories',
        'examples': '💡 Examples',
        'help': '❓ Help',
        'language': '🌍 Language',
        'back_menu': '⬅️ Back to Main Menu',
        'generate_title': '🎯 **Generate Promotional Text**',
        'generate_instructions': 'Ready to create amazing promotional content!\n\n**How to proceed:**\n1. Simply type the name of your product in the chat\n2. I\'ll generate compelling promotional text for you\n3. You can then copy and use it for your marketing!\n\n**Examples of what to send:**\n• "Wireless Bluetooth Headphones"\n• "Organic Green Tea"\n• "Gaming Mechanical Keyboard"\n• "Women\'s Running Shoes"\n\nJust type your product name below! 👇',
        'categories_title': '📝 **Product Categories**',
        'categories_subtitle': 'Select a category to get tips and inspiration for your promotional text:',
        'electronics': '📱 Electronics',
        'fashion': '👕 Fashion',
        'home': '🏠 Home & Garden',
        'beauty': '💄 Beauty',
        'gaming': '🎮 Gaming',
        'books': '📚 Books',
        'examples_title': '💡 **Example Promotional Texts**',
        'examples_content': 'Here are some examples of what I can generate:\n\n**🎧 Wireless Headphones:**\n*"Experience freedom with our premium wireless headphones! 🎵 Crystal-clear sound, 30-hour battery life, and noise cancellation technology. Perfect for work, travel, and workouts. Order now and get FREE shipping! 🚚"*\n\n**👟 Running Shoes:**\n*"Step up your game with our lightweight running shoes! 🏃‍♀️ Advanced cushioning, breathable mesh, and durable design. Whether you\'re training for a marathon or daily jogs, these shoes will keep you comfortable. Get yours today! 💪"*\n\n**📱 Smartphone:**\n*"Capture life in stunning detail with our latest smartphone! 📸 Professional-grade camera, all-day battery, and lightning-fast performance. Stay connected, create memories, and experience technology at its finest. Available now! ✨"*\n\nReady to create your own? Just type any product name!',
        'help_title': '❓ **Help & Support**',
        'help_content': '**🔧 How to use this bot:**\n\n1. **Generate Promo Text** - Click the button and send a product name\n2. **Browse Categories** - Get inspiration from different product types\n3. **View Examples** - See sample promotional texts I can create\n4. **Direct Input** - Type any product name anytime for instant results!\n\n**💡 Tips for better results:**\n• Be specific (e.g., "Noise-cancelling wireless headphones")\n• Include key features ("Waterproof fitness tracker")\n• Mention target audience ("Gaming headset for professionals")\n\n**🎯 What I create for you:**\n• Engaging promotional text (50-150 words)\n• Social media ready content\n• Professional marketing copy\n• Call-to-action phrases\n• Appropriate emojis\n\n**Commands:**\n/start - Show main menu\n/help - Show this help message\n\nNeed more help? Just start typing your product name! 🚀',
        'promo_result': '🎯 **Promotional Text for: {}**',
        'promo_footer': '💡 *Feel free to customize this text for your specific needs!*',
        'generate_another': '🔄 Generate Another',
        'rate_limit': '⚠️ Rate limit exceeded. Please try again in a moment.',
        'request_error': '❌ There was an issue with the request. Please try again.',
        'general_error': '❌ Sorry, I encountered an error while generating the promotional text. Please try again.',
        'empty_product': 'Please provide a product name to generate promotional text.',
        'language_title': '🌍 **Choose Your Language**',
        'language_subtitle': 'Select your preferred language:',
        'openai_prompt': 'Create a compelling promotional post for the following product: {}\n\nThe promotional text should:\n- Be engaging and attention-grabbing\n- Highlight key benefits and features\n- Include a strong call-to-action\n- Be suitable for social media posting\n- Use emojis appropriately\n- Be between 50-150 words\n- Sound persuasive and professional\n- BE WRITTEN IN ENGLISH\n\nProduct: {}',
        'system_prompt': 'You are a professional marketing copywriter specializing in creating compelling promotional content for products. Your writing style is engaging, persuasive, and modern. Write in English.'
    },
    'ru': {
        'welcome_title': '🚀 **Добро пожаловать в бот генератора рекламных текстов!** 🚀',
        'welcome_message': 'Я помогу вам создать потрясающие рекламные посты для ваших товаров!\n\nСначала выберите язык:',
        'language_selected': '✅ Язык установлен на русский!\n\nВыберите опцию ниже, чтобы начать:',
        'main_menu_title': '🚀 **Бот генератора рекламных текстов - Главное меню**',
        'main_menu_subtitle': 'Выберите опцию для продолжения:',
        'generate_promo': '🎯 Создать рекламный текст',
        'categories': '📝 Категории товаров',
        'examples': '💡 Примеры', 
        'help': '❓ Помощь',
        'language': '🌍 Язык',
        'back_menu': '⬅️ Назад в главное меню',
        'generate_title': '🎯 **Создание рекламного текста**',
        'generate_instructions': 'Готов создать потрясающий рекламный контент!\n\n**Как продолжить:**\n1. Просто напишите название вашего товара в чате\n2. Я создам убедительный рекламный текст для вас\n3. Вы сможете скопировать и использовать его для маркетинга!\n\n**Примеры того, что отправить:**\n• "Беспроводные Bluetooth наушники"\n• "Органический зеленый чай"\n• "Игровая механическая клавиатура"\n• "Женские кроссовки для бега"\n\nПросто введите название товара ниже! 👇',
        'categories_title': '📝 **Категории товаров**',
        'categories_subtitle': 'Выберите категорию для получения советов и вдохновения для рекламного текста:',
        'electronics': '📱 Электроника',
        'fashion': '👕 Мода',
        'home': '🏠 Дом и сад',
        'beauty': '💄 Красота',
        'gaming': '🎮 Игры',
        'books': '📚 Книги',
        'examples_title': '💡 **Примеры рекламных текстов**',
        'examples_content': 'Вот несколько примеров того, что я могу создать:\n\n**🎧 Беспроводные наушники:**\n*"Почувствуйте свободу с нашими премиальными беспроводными наушниками! 🎵 Кристально чистый звук, 30-часовая батарея и технология шумоподавления. Идеально для работы, путешествий и тренировок. Заказывайте сейчас и получите БЕСПЛАТНУЮ доставку! 🚚"*\n\n**👟 Кроссовки для бега:**\n*"Поднимите свою игру с нашими легкими кроссовками для бега! 🏃‍♀️ Продвинутая амортизация, дышащий материал и прочный дизайн. Готовитесь к марафону или ежедневным пробежкам - эти кроссовки обеспечат комфорт. Получите свои уже сегодня! 💪"*\n\n**📱 Смартфон:**\n*"Запечатлейте жизнь в потрясающих деталях с нашим новейшим смартфоном! 📸 Профессиональная камера, батарея на весь день и молниеносная производительность. Оставайтесь на связи, создавайте воспоминания и наслаждайтесь технологиями. Доступно сейчас! ✨"*\n\nГотовы создать свой? Просто введите любое название товара!',
        'help_title': '❓ **Помощь и поддержка**',
        'help_content': '**🔧 Как использовать этот бот:**\n\n1. **Создать рекламный текст** - Нажмите кнопку и отправьте название товара\n2. **Просмотр категорий** - Получите вдохновение от разных типов товаров\n3. **Просмотр примеров** - Посмотрите образцы рекламных текстов\n4. **Прямой ввод** - Вводите название товара в любое время!\n\n**💡 Советы для лучших результатов:**\n• Будьте конкретны (например, "Шумоподавляющие беспроводные наушники")\n• Включайте ключевые особенности ("Водонепроницаемый фитнес-трекер")\n• Упоминайте целевую аудиторию ("Игровая гарнитура для профессионалов")\n\n**🎯 Что я создаю для вас:**\n• Увлекательный рекламный текст (50-150 слов)\n• Контент готовый для соцсетей\n• Профессиональные маркетинговые тексты\n• Призывы к действию\n• Подходящие эмодзи\n\n**Команды:**\n/start - Показать главное меню\n/help - Показать это сообщение помощи\n\nНужна дополнительная помощь? Просто начните вводить название товара! 🚀',
        'promo_result': '🎯 **Рекламный текст для: {}**',
        'promo_footer': '💡 *Не стесняйтесь адаптировать этот текст для ваших конкретных нужд!*',
        'generate_another': '🔄 Создать еще один',
        'rate_limit': '⚠️ Превышен лимит запросов. Попробуйте еще раз через момент.',
        'request_error': '❌ Возникла проблема с запросом. Попробуйте еще раз.',
        'general_error': '❌ Извините, произошла ошибка при создании рекламного текста. Попробуйте еще раз.',
        'empty_product': 'Пожалуйста, укажите название товара для создания рекламного текста.',
        'language_title': '🌍 **Выберите ваш язык**',
        'language_subtitle': 'Выберите предпочитаемый язык:',
        'openai_prompt': 'Создай убедительный рекламный пост для следующего товара: {}\n\nРекламный текст должен:\n- Быть привлекательным и захватывающим внимание\n- Подчеркивать ключевые преимущества и особенности\n- Включать сильный призыв к действию\n- Подходить для публикации в социальных сетях\n- Уместно использовать эмодзи\n- Быть длиной 50-150 слов\n- Звучать убедительно и профессионально\n- БЫТЬ НАПИСАННЫМ НА РУССКОМ ЯЗЫКЕ\n\nТовар: {}',
        'system_prompt': 'Ты профессиональный маркетинговый копирайтер, специализирующийся на создании убедительного рекламного контента для товаров. Твой стиль письма привлекательный, убедительный и современный. Пиши на русском языке.'
    },
    'ro': {
        'welcome_title': '🚀 **Bun venit la botul generator de texte promoționale!** 🚀',
        'welcome_message': 'Te pot ajuta să creezi postări promoționale uimitoare pentru produsele tale!\n\nAlege mai întâi limba:',
        'language_selected': '✅ Limba setată în română!\n\nAlege o opțiune de mai jos pentru a începe:',
        'main_menu_title': '🚀 **Bot generator de texte promoționale - Meniul principal**',
        'main_menu_subtitle': 'Alege o opțiune pentru a continua:',
        'generate_promo': '🎯 Generează text promoțional',
        'categories': '📝 Categorii de produse',
        'examples': '💡 Exemple',
        'help': '❓ Ajutor',
        'language': '🌍 Limba',
        'back_menu': '⬅️ Înapoi la meniul principal',
        'generate_title': '🎯 **Generare text promoțional**',
        'generate_instructions': 'Gata să creez conținut promoțional uimitor!\n\n**Cum să continui:**\n1. Pur și simplu scrie numele produsului tău în chat\n2. Voi genera un text promoțional convingător pentru tine\n3. Apoi îl poți copia și folosi pentru marketing!\n\n**Exemple de ce să trimiți:**\n• "Căști Bluetooth wireless"\n• "Ceai verde organic"\n• "Tastatură mecanică pentru gaming"\n• "Pantofi de alergare pentru femei"\n\nScrie numele produsului mai jos! 👇',
        'categories_title': '📝 **Categorii de produse**',
        'categories_subtitle': 'Selectează o categorie pentru sfaturi și inspirație pentru textul promoțional:',
        'electronics': '📱 Electronice',
        'fashion': '👕 Modă',
        'home': '🏠 Casă și grădină',
        'beauty': '💄 Frumusețe',
        'gaming': '🎮 Gaming',
        'books': '📚 Cărți',
        'examples_title': '💡 **Exemple de texte promoționale**',
        'examples_content': 'Iată câteva exemple de ce pot genera:\n\n**🎧 Căști wireless:**\n*"Simte libertatea cu căștile noastre premium wireless! 🎵 Sunet cristalin, baterie de 30 de ore și tehnologie de anulare a zgomotului. Perfect pentru muncă, călătorii și antrenamente. Comandă acum și beneficiezi de livrare GRATUITĂ! 🚚"*\n\n**👟 Pantofi de alergare:**\n*"Ridică-ți nivelul cu pantofii noștri ușori de alergare! 🏃‍♀️ Amortizare avansată, material respirabil și design durabil. Fie că te antrenezi pentru maraton sau pentru alergări zilnice, acești pantofi te vor menține confortabil. Obține-i astăzi! 💪"*\n\n**📱 Smartphone:**\n*"Surprinde viața în detalii uimitoare cu cel mai nou smartphone! 📸 Cameră de nivel profesional, baterie pentru toată ziua și performanță fulgerătoare. Rămâi conectat, creează amintiri și experimentează tehnologia la cel mai înalt nivel. Disponibil acum! ✨"*\n\nGata să creezi propriul tău? Scrie orice nume de produs!',
        'help_title': '❓ **Ajutor și suport**',
        'help_content': '**🔧 Cum să folosești acest bot:**\n\n1. **Generează text promoțional** - Apasă butonul și trimite numele produsului\n2. **Răsfoiește categoriile** - Obține inspirație de la diferite tipuri de produse\n3. **Vezi exemple** - Privește exemple de texte promoționale\n4. **Introducere directă** - Scrie orice nume de produs oricând!\n\n**💡 Sfaturi pentru rezultate mai bune:**\n• Fii specific (ex: "Căști wireless cu anulare zgomot")\n• Include caracteristici cheie ("Tracker fitness rezistent la apă")\n• Menționează publicul țintă ("Căști gaming pentru profesioniști")\n\n**🎯 Ce creez pentru tine:**\n• Text promoțional captivant (50-150 cuvinte)\n• Conținut gata pentru rețelele sociale\n• Texte de marketing profesionale\n• Chemări la acțiune\n• Emoji-uri potrivite\n\n**Comenzi:**\n/start - Arată meniul principal\n/help - Arată acest mesaj de ajutor\n\nAi nevoie de mai mult ajutor? Doar începe să scrii numele produsului! 🚀',
        'promo_result': '🎯 **Text promoțional pentru: {}**',
        'promo_footer': '💡 *Simte-te liber să personalizezi acest text pentru nevoile tale specifice!*',
        'generate_another': '🔄 Generează altul',
        'rate_limit': '⚠️ Limita de cereri depășită. Te rog să încerci din nou într-un moment.',
        'request_error': '❌ A fost o problemă cu cererea. Te rog să încerci din nou.',
        'general_error': '❌ Îmi pare rău, am întâmpinat o eroare la generarea textului promoțional. Te rog să încerci din nou.',
        'empty_product': 'Te rog să furnizezi numele unui produs pentru a genera text promoțional.',
        'language_title': '🌍 **Alege limba ta**',
        'language_subtitle': 'Selectează limba preferată:',
        'openai_prompt': 'Creează un post promoțional convingător pentru următorul produs: {}\n\nTextul promoțional trebuie să:\n- Fie captivant și să atragă atenția\n- Să evidențieze beneficiile și caracteristicile cheie\n- Să includă o chemare puternică la acțiune\n- Să fie potrivit pentru postarea pe rețelele sociale\n- Să folosească emoji-uri în mod corespunzător\n- Să aibă între 50-150 cuvinte\n- Să sune convingător și profesional\n- SĂ FIE SCRIS ÎN LIMBA ROMÂNĂ\n\nProdus: {}',
        'system_prompt': 'Ești un copywriter de marketing profesional specializat în crearea de conținut promoțional convingător pentru produse. Stilul tău de scriere este captivant, convingător și modern. Scrie în limba română.'
    }
}

class PromoBot:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def get_user_language(self, context):
        """Get user's selected language, default to English."""
        return context.user_data.get('language', 'en')

    def get_text(self, key, context, *args):
        """Get translated text for user's language."""
        lang = self.get_user_language(context)
        text = TRANSLATIONS[lang].get(key, TRANSLATIONS['en'][key])
        if args:
            return text.format(*args)
        return text

    def get_language_selection_keyboard(self):
        """Create language selection keyboard in grid format."""
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en'), 
             InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
            [InlineKeyboardButton("🇷🇴 Română", callback_data='lang_ro')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_main_menu_keyboard(self, context):
        """Create the main menu inline keyboard in grid format."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('generate_promo', context), callback_data='generate_promo'),
             InlineKeyboardButton(self.get_text('categories', context), callback_data='categories')],
            [InlineKeyboardButton(self.get_text('examples', context), callback_data='examples'),
             InlineKeyboardButton(self.get_text('help', context), callback_data='help')],
            [InlineKeyboardButton("📢 Channel Settings", callback_data='channel_settings'),
             InlineKeyboardButton(self.get_text('language', context), callback_data='language_select')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_categories_keyboard(self, context):
        """Create the product categories inline keyboard in grid format."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('electronics', context), callback_data='cat_electronics'),
             InlineKeyboardButton(self.get_text('fashion', context), callback_data='cat_fashion')],
            [InlineKeyboardButton(self.get_text('home', context), callback_data='cat_home'),
             InlineKeyboardButton(self.get_text('beauty', context), callback_data='cat_beauty')],
            [InlineKeyboardButton(self.get_text('gaming', context), callback_data='cat_gaming'),
             InlineKeyboardButton(self.get_text('books', context), callback_data='cat_books')],
            [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_back_to_menu_keyboard(self, context):
        """Create a simple back to menu keyboard."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_channel_settings_keyboard(self, context):
        """Create keyboard for channel settings."""
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id')
        auto_post = channel_info.get('auto_post', False)
        
        if channel_id:
            keyboard = [
                [InlineKeyboardButton(f"📋 Current: {channel_id}", callback_data='channel_info')],
                [InlineKeyboardButton("✏️ Change Channel", callback_data='set_channel'),
                 InlineKeyboardButton("❌ Remove Channel", callback_data='remove_channel')],
                [InlineKeyboardButton(f"🤖 Auto-post: {'✅ ON' if auto_post else '❌ OFF'}", callback_data='toggle_autopost')],
                [InlineKeyboardButton("📊 Post History", callback_data='post_history')],
                [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main_menu')]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("➕ Add Channel/Group", callback_data='set_channel')],
                [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main_menu')]
            ]
        return InlineKeyboardMarkup(keyboard)

    def get_post_generation_keyboard(self, context):
        """Create keyboard for after text generation with channel posting option."""
        channel_info = context.user_data.get('channel_info', {})
        has_channel = bool(channel_info.get('channel_id'))
        
        if has_channel:
            keyboard = [
                [InlineKeyboardButton("🔄 Generate Another", callback_data='generate_promo'),
                 InlineKeyboardButton("📤 Post to Channel", callback_data='post_to_channel')],
                [InlineKeyboardButton("⬅️ Main Menu", callback_data='main_menu')]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Generate Another", callback_data='generate_promo'),
                 InlineKeyboardButton("⬅️ Main Menu", callback_data='main_menu')]
            ]
        return InlineKeyboardMarkup(keyboard)

    def get_post_confirmation_keyboard(self, context):
        """Create keyboard for post confirmation."""
        keyboard = [
            [InlineKeyboardButton("✅ Post Now", callback_data='confirm_post'),
             InlineKeyboardButton("✏️ Edit Text", callback_data='edit_post')],
            [InlineKeyboardButton("❌ Cancel", callback_data='cancel_post')]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def verify_channel_permissions(self, context, channel_id):
        """Verify bot has admin permissions in channel/group."""
        try:
            # Remove @ if present
            if channel_id.startswith('@'):
                channel_id = channel_id[1:]
            
            # Get chat member (bot) info
            bot_member = await context.bot.get_chat_member(f"@{channel_id}", context.bot.id)
            
            # Check if bot is admin
            if bot_member.status not in ['administrator', 'creator']:
                return False, "Bot is not an administrator in this channel/group"
            
            # Check if bot can post messages
            if hasattr(bot_member, 'can_post_messages') and not bot_member.can_post_messages:
                return False, "Bot doesn't have permission to post messages"
            
            # Send test message and delete it
            test_msg = await context.bot.send_message(f"@{channel_id}", "🤖 Bot verification test - this message will be deleted")
            await context.bot.delete_message(f"@{channel_id}", test_msg.message_id)
            
            return True, "Permissions verified successfully"
            
        except Exception as e:
            return False, f"Error: {str(e)}"

    def generate_hashtags(self, product_name, context):
        """Generate relevant hashtags for the product."""
        # Basic hashtag generation - can be enhanced
        words = product_name.lower().replace('-', ' ').replace('_', ' ').split()
        hashtags = []
        
        # Add product-specific hashtags
        for word in words:
            if len(word) > 2:  # Skip short words
                hashtags.append(f"#{word}")
        
        # Add general marketing hashtags
        hashtags.extend(["#promo", "#sale", "#newproduct", "#shopping"])
        
        return " ".join(hashtags[:8])  # Limit to 8 hashtags

    async def post_to_channel_action(self, context, text, product_name):
        """Post the promotional text to configured channel."""
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id')
        
        if not channel_id:
            return False, "No channel configured"
        
        try:
            # Generate hashtags
            hashtags = self.generate_hashtags(product_name, context)
            
            # Format final post
            final_post = f"{text}\n\n{hashtags}"
            
            # Post to channel
            sent_message = await context.bot.send_message(f"@{channel_id}", final_post)
            
            # Store post history
            if 'post_history' not in context.user_data:
                context.user_data['post_history'] = []
            
            context.user_data['post_history'].append({
                'product': product_name,
                'timestamp': sent_message.date.strftime('%Y-%m-%d %H:%M'),
                'message_id': sent_message.message_id,
                'status': 'success'
            })
            
            return True, f"Posted successfully to {channel_id}"
            
        except Exception as e:
            # Store failed post
            if 'post_history' not in context.user_data:
                context.user_data['post_history'] = []
            
            context.user_data['post_history'].append({
                'product': product_name,
                'timestamp': 'Failed',
                'message_id': None,
                'status': f'failed: {str(e)}'
            })
            
            return False, f"Failed to post: {str(e)}"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send the welcome message with language selection."""
        # If user doesn't have a language set, show language selection first
        if 'language' not in context.user_data:
            welcome_message = TRANSLATIONS['en']['welcome_message']
            await update.message.reply_text(
                f"{TRANSLATIONS['en']['welcome_title']}\n\n{welcome_message}",
                parse_mode='Markdown',
                reply_markup=self.get_language_selection_keyboard()
            )
        else:
            # Show main menu if language is already set
            await self.show_main_menu_message(update, context)

    async def show_main_menu_message(self, update, context):
        """Show main menu as a new message."""
        text = f"{self.get_text('main_menu_title', context)}\n\n{self.get_text('main_menu_subtitle', context)}"
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=self.get_main_menu_keyboard(context)
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send help message with menu."""
        # Ensure user has a language set
        if 'language' not in context.user_data:
            context.user_data['language'] = 'en'
        
        await update.message.reply_text(
            self.get_text('help_content', context),
            parse_mode='Markdown',
            reply_markup=self.get_main_menu_keyboard(context)
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button press callbacks."""
        query = update.callback_query
        await query.answer()

        # Handle language selection
        if query.data.startswith('lang_'):
            await self.handle_language_selection(query, context)
        elif query.data == 'language_select':
            await self.show_language_selection(query, context)
        elif query.data == 'main_menu':
            await self.show_main_menu(query, context)
        elif query.data == 'generate_promo':
            await self.show_generate_promo(query, context)
        elif query.data == 'categories':
            await self.show_categories(query, context)
        elif query.data == 'examples':
            await self.show_examples(query, context)
        elif query.data == 'help':
            await self.show_help(query, context)
        elif query.data.startswith('cat_'):
            await self.show_category_info(query, context)
        # Channel management callbacks
        elif query.data == 'channel_settings':
            await self.show_channel_settings(query, context)
        elif query.data == 'set_channel':
            await self.prompt_channel_setup(query, context)
        elif query.data == 'remove_channel':
            await self.remove_channel(query, context)
        elif query.data == 'toggle_autopost':
            await self.toggle_autopost(query, context)
        elif query.data == 'post_history':
            await self.show_post_history(query, context)
        elif query.data == 'post_to_channel':
            await self.initiate_channel_post(query, context)
        elif query.data == 'confirm_post':
            await self.confirm_channel_post(query, context)
        elif query.data == 'edit_post':
            await self.edit_post_text(query, context)
        elif query.data == 'cancel_post':
            await self.cancel_post(query, context)

    async def handle_language_selection(self, query, context):
        """Handle language selection."""
        lang_code = query.data.split('_')[1]
        context.user_data['language'] = lang_code
        
        text = f"{self.get_text('language_selected', context)}"
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_main_menu_keyboard(context)
        )

    async def show_language_selection(self, query, context):
        """Show language selection menu."""
        await query.edit_message_text(
            text=f"{self.get_text('language_title', context)}\n\n{self.get_text('language_subtitle', context)}",
            parse_mode='Markdown',
            reply_markup=self.get_language_selection_keyboard()
        )

    async def show_main_menu(self, query, context):
        """Show the main menu."""
        text = f"{self.get_text('main_menu_title', context)}\n\n{self.get_text('main_menu_subtitle', context)}"
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_main_menu_keyboard(context)
        )

    async def show_generate_promo(self, query, context):
        """Show the generate promo text instructions."""
        await query.edit_message_text(
            text=self.get_text('generate_instructions', context),
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def show_categories(self, query, context):
        """Show product categories."""
        text = f"{self.get_text('categories_title', context)}\n\n{self.get_text('categories_subtitle', context)}"
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_categories_keyboard(context)
        )

    async def show_examples(self, query, context):
        """Show example promotional texts."""
        await query.edit_message_text(
            text=self.get_text('examples_content', context),
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def show_help(self, query, context):
        """Show help information."""
        await query.edit_message_text(
            text=self.get_text('help_content', context),
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def show_channel_settings(self, query, context):
        """Show channel settings menu."""
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id')
        
        if channel_id:
            text = f"📢 **Channel Settings**\n\nConfigured channel: @{channel_id}\nAuto-post: {'✅ Enabled' if channel_info.get('auto_post', False) else '❌ Disabled'}"
        else:
            text = "📢 **Channel Settings**\n\nNo channel configured yet. Add a channel to start posting your promotional content automatically!"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def show_category_info(self, query, context):
        """Show information about a specific category."""
        # For now, showing a simplified version - you can expand this with translated category info
        category_name = query.data.split('_')[1]
        text = f"📝 **{category_name.title()} Category**\n\nChoose this category to get specialized tips for creating promotional text.\n\nReady to create promotional text?\nJust type your product name in the chat below! 👇"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def prompt_channel_setup(self, query, context):
        """Prompt user to enter channel ID."""
        context.user_data['waiting_for_channel'] = True
        text = "📢 **Add Channel/Group**\n\nPlease send me the channel/group username (with @) or ID.\n\n**Example:** @mychannel\n\n**Note:** The bot must be added as an administrator to the channel/group with posting permissions."
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def remove_channel(self, query, context):
        """Remove configured channel."""
        if 'channel_info' in context.user_data:
            del context.user_data['channel_info']
        
        text = "✅ **Channel Removed**\n\nChannel configuration has been removed. You can add a new channel anytime from the settings."
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def toggle_autopost(self, query, context):
        """Toggle auto-posting feature."""
        channel_info = context.user_data.get('channel_info', {})
        auto_post = not channel_info.get('auto_post', False)
        
        channel_info['auto_post'] = auto_post
        context.user_data['channel_info'] = channel_info
        
        status = "enabled" if auto_post else "disabled"
        text = f"🤖 **Auto-posting {status.title()}**\n\nAuto-posting is now {status}. Generated promotional texts will {'automatically' if auto_post else 'not'} be posted to your channel."
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def show_post_history(self, query, context):
        """Show posting history."""
        history = context.user_data.get('post_history', [])
        
        if not history:
            text = "📊 **Post History**\n\nNo posts yet. Generate some promotional content and post to your channel!"
        else:
            text = "📊 **Post History**\n\n"
            for i, post in enumerate(history[-10:], 1):  # Show last 10 posts
                status_emoji = "✅" if post['status'] == 'success' else "❌"
                text += f"{i}. {status_emoji} **{post['product']}**\n   {post['timestamp']} - {post['status']}\n\n"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def handle_channel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel ID input from user."""
        if not context.user_data.get('waiting_for_channel'):
            return False
        
        channel_input = update.message.text.strip()
        context.user_data['waiting_for_channel'] = False
        
        # Validate and verify channel
        success, message = await self.verify_channel_permissions(context, channel_input)
        
        if success:
            # Store channel info
            context.user_data['channel_info'] = {
                'channel_id': channel_input.replace('@', ''),
                'auto_post': False
            }
            
            text = f"✅ **Channel Added Successfully**\n\nChannel @{channel_input.replace('@', '')} has been configured!\n\n{message}"
        else:
            text = f"❌ **Channel Setup Failed**\n\n{message}\n\nPlease make sure:\n1. The bot is added to the channel/group\n2. The bot has administrator permissions\n3. The bot can post messages"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=self.get_channel_settings_keyboard(context)
        )
        return True

    async def initiate_channel_post(self, query, context):
        """Initiate posting to channel with confirmation."""
        stored_text = context.user_data.get('last_generated_text', '')
        product_name = context.user_data.get('last_product_name', '')
        
        if not stored_text:
            await query.edit_message_text(
                "❌ No promotional text found. Please generate text first.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id', 'Unknown')
        
        # Store for posting
        context.user_data['pending_post'] = {
            'text': stored_text,
            'product': product_name
        }
        
        hashtags = self.generate_hashtags(product_name, context)
        preview_text = f"{stored_text}\n\n{hashtags}"
        
        text = f"📤 **Confirm Channel Post**\n\nChannel: @{channel_id}\nProduct: {product_name}\n\n**Preview:**\n{preview_text[:200]}{'...' if len(preview_text) > 200 else ''}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_post_confirmation_keyboard(context)
        )

    async def confirm_channel_post(self, query, context):
        """Confirm and execute channel post."""
        pending_post = context.user_data.get('pending_post', {})
        
        if not pending_post:
            await query.edit_message_text(
                "❌ No pending post found.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        # Post to channel
        success, message = await self.post_to_channel_action(
            context, 
            pending_post['text'], 
            pending_post['product']
        )
        
        # Clean up
        if 'pending_post' in context.user_data:
            del context.user_data['pending_post']
        
        status_emoji = "✅" if success else "❌"
        text = f"{status_emoji} **Post {('Successful' if success else 'Failed')}**\n\n{message}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def edit_post_text(self, query, context):
        """Allow user to edit post text before posting."""
        context.user_data['editing_post'] = True
        text = "✏️ **Edit Post Text**\n\nSend me the edited version of your promotional text. You can modify it as needed before posting to the channel."
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def cancel_post(self, query, context):
        """Cancel the pending post."""
        if 'pending_post' in context.user_data:
            del context.user_data['pending_post']
        
        text = "❌ **Post Cancelled**\n\nThe post has been cancelled. You can generate new promotional text or return to the main menu."
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def handle_post_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle edited post text."""
        if not context.user_data.get('editing_post'):
            return False
        
        edited_text = update.message.text.strip()
        context.user_data['editing_post'] = False
        
        # Update pending post
        if 'pending_post' in context.user_data:
            context.user_data['pending_post']['text'] = edited_text
            
            # Show confirmation again
            await self.initiate_channel_post_from_edit(update, context)
        else:
            await update.message.reply_text(
                "❌ No pending post found.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
        return True

    async def initiate_channel_post_from_edit(self, update, context):
        """Show post confirmation after editing."""
        pending_post = context.user_data.get('pending_post', {})
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id', 'Unknown')
        
        hashtags = self.generate_hashtags(pending_post['product'], context)
        preview_text = f"{pending_post['text']}\n\n{hashtags}"
        
        text = f"📤 **Confirm Edited Post**\n\nChannel: @{channel_id}\nProduct: {pending_post['product']}\n\n**Preview:**\n{preview_text[:200]}{'...' if len(preview_text) > 200 else ''}"
        
        await update.message.reply_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_post_confirmation_keyboard(context)
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages from users."""
        # Handle channel input
        if await self.handle_channel_input(update, context):
            return
        
        # Handle post editing
        if await self.handle_post_edit(update, context):
            return
        
        # Handle regular product name input for text generation
        await self.generate_promo_text(update, context)

    async def generate_promo_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate promotional text for the given product."""
        # Ensure user has a language set
        if 'language' not in context.user_data:
            context.user_data['language'] = 'en'

        product_name = update.message.text.strip()
        
        if not product_name:
            await update.message.reply_text(
                self.get_text('empty_product', context),
                reply_markup=self.get_main_menu_keyboard(context)
            )
            return
        
        # Show typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

        try:
            # Create the prompt for OpenAI in the user's language
            prompt = self.get_text('openai_prompt', context, product_name, product_name)
            system_prompt = self.get_text('system_prompt', context)

            # Generate response using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            promo_text = response.choices[0].message.content.strip()
            
            # Store the generated text and product name for potential channel posting
            context.user_data['last_generated_text'] = promo_text
            context.user_data['last_product_name'] = product_name
            
            # Format the response
            formatted_response = f"""
{self.get_text('promo_result', context, product_name)}

{promo_text}

---
{self.get_text('promo_footer', context)}
            """

            await update.message.reply_text(
                formatted_response, 
                parse_mode='Markdown',
                reply_markup=self.get_post_generation_keyboard(context)
            )
            
            # Check for auto-posting
            channel_info = context.user_data.get('channel_info', {})
            if channel_info.get('auto_post', False) and channel_info.get('channel_id'):
                # Auto post to channel
                success, message = await self.post_to_channel_action(context, promo_text, product_name)
                
                # Notify user about auto-post result
                status_emoji = "✅" if success else "❌"
                auto_post_msg = f"\n\n{status_emoji} **Auto-post:** {message}"
                
                # Edit the previous message to include auto-post status
                try:
                    await update.message.edit_text(
                        formatted_response + auto_post_msg,
                        parse_mode='Markdown',
                        reply_markup=self.get_post_generation_keyboard(context)
                    )
                except:
                    # If editing fails, send a new message
                    await update.message.reply_text(
                        auto_post_msg,
                        parse_mode='Markdown'
                    )

        except openai.error.RateLimitError:
            await update.message.reply_text(
                self.get_text('rate_limit', context),
                reply_markup=self.get_main_menu_keyboard(context)
            )
        except openai.error.InvalidRequestError as e:
            logger.error(f"Invalid request to OpenAI: {e}")
            await update.message.reply_text(
                self.get_text('request_error', context),
                reply_markup=self.get_main_menu_keyboard(context)
            )
        except Exception as e:
            logger.error(f"Error generating promo text: {e}")
            await update.message.reply_text(
                self.get_text('general_error', context),
                reply_markup=self.get_main_menu_keyboard(context)
            )

    def run(self):
        """Start the bot."""
        # Create the Application
        application = Application.builder().token(self.telegram_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Run the bot
        logger.info("Starting the Promo Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        bot = PromoBot()
        bot.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        print("Please check your environment variables in the .env file")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")