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
            [InlineKeyboardButton(self.get_text('language', context), callback_data='language_select')]
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

    def get_post_generation_keyboard(self, context):
        """Create keyboard for after text generation in grid format."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('generate_another', context), callback_data='generate_promo'),
             InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

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
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_promo_text))

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