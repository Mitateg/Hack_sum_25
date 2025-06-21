import os
import logging
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from PIL import Image
import io
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
        'my_products': '📦 My Products',
        'examples': '💡 Examples',
        'help': '❓ Help',
        'language': '🌍 Language',
        'back_menu': '⬅️ Back to Main Menu',
        'channel_settings': '📢 Channel Settings',
        'add_product_link': '➕ Add Product Link',
        'add_product': '➕ Add Product',
        'clear_all': '🗑️ Clear All',
        'delete_product': '🗑️ Delete Product',
        'open_link': '🔗 Open Link',
        'back_to_products': '⬅️ Back to Products',
        'from_my_products': '📦 From My Products',
        'from_prompt': '✏️ From Prompt',
        'back_to_generation_menu': '⬅️ Back to Generation Menu',
        'generate_title': '🎯 **Generate Promotional Text**',
        'generate_instructions': 'Ready to create amazing promotional content!\n\n**How to proceed:**\n1. Simply type the name of your product in the chat\n2. I\'ll generate compelling promotional text for you\n3. You can then copy and use it for your marketing!\n\n**Examples of what to send:**\n• "Wireless Bluetooth Headphones"\n• "Organic Green Tea"\n• "Gaming Mechanical Keyboard"\n• "Women\'s Running Shoes"\n\nJust type your product name below! 👇',
        'promo_choice_title': '🎯 **Generate Promotional Text**\n\nChoose how you want to create your promo:',
        'promo_choice_subtitle': '📦 **From My Products** - Generate promo from your saved products ({} available)\n\n✏️ **From Prompt** - Create promo by typing a product name\n\nWhat would you like to do?',
        'no_products_available': '📦 **No Products Available**\n\nYou don\'t have any saved products yet. Add some products first or create a promo from a prompt!',
        'select_product_title': '📦 **Select Product ({} available)**\n\nChoose a product to generate promotional text for:',
        'examples_title': '💡 **Example Promotional Texts**',
        'examples_content': 'Here are some examples of what I can generate:\n\n**🎧 Wireless Headphones:**\n*"Experience freedom with our premium wireless headphones! 🎵 Crystal-clear sound, 30-hour battery life, and noise cancellation technology. Perfect for work, travel, and workouts. Order now and get FREE shipping! 🚚"*\n\n**👟 Running Shoes:**\n*"Step up your game with our lightweight running shoes! 🏃‍♀️ Advanced cushioning, breathable mesh, and durable design. Whether you\'re training for a marathon or daily jogs, these shoes will keep you comfortable. Get yours today! 💪"*\n\n**📱 Smartphone:**\n*"Capture life in stunning detail with our latest smartphone! 📸 Professional-grade camera, all-day battery, and lightning-fast performance. Stay connected, create memories, and experience technology at its finest. Available now! ✨"*\n\nReady to create your own? Just type any product name!',
        'help_title': '❓ **Help & Support**',
        'help_content': '**🔧 How to use this bot:**\n\n1. **Generate Promo Text** - Click the button and send a product name\n2. **Browse Categories** - Get inspiration from different product types\n3. **View Examples** - See sample promotional texts I can create\n4. **Direct Input** - Type any product name anytime for instant results!\n\n**💡 Tips for better results:**\n• Be specific (e.g., "Noise-cancelling wireless headphones")\n• Include key features ("Waterproof fitness tracker")\n• Mention target audience ("Gaming headset for professionals")\n\n**🎯 What I create for you:**\n• Engaging promotional text (50-150 words)\n• Social media ready content\n• Professional marketing copy\n• Call-to-action phrases\n• Appropriate emojis\n\n**Commands:**\n/start - Show main menu\n/help - Show this help message\n\nNeed more help? Just start typing your product name! 🚀',
        'channel_settings_title': '📢 **Channel Settings**',
        'channel_configured': 'Configured channel: @{}\nAuto-post: {}',
        'channel_not_configured': 'No channel configured yet. Add a channel to start posting your promotional content automatically!',
        'auto_enabled': '✅ Enabled',
        'auto_disabled': '❌ Disabled',
        'current_channel': '📋 Current: {}',
        'change_channel': '✏️ Change Channel',
        'remove_channel': '❌ Remove Channel',
        'auto_post_on': '✅ ON',
        'auto_post_off': '❌ OFF',
        'auto_post_toggle': '🤖 Auto-post: {}',
        'post_history': '📊 Post History',
        'add_channel_group': '➕ Add Channel/Group',
        'my_products_title': '📦 **My Products**',
        'no_products_yet': 'No products added yet!\n\nAdd product links to start creating amazing promotional content. I can analyze any e-commerce link and extract product information automatically.\n\n**Supported:** Amazon, eBay, AliExpress, Shopify stores, and many more!',
        'my_products_count': '📦 **My Products ({}/5)**\n\nYour saved products:\n\n',
        'add_channel_title': '📢 **Add Channel/Group**',
        'add_channel_instructions': 'Please send me the channel/group username (with @) or ID.\n\n**Example:** @mychannel\n\n**Note:** The bot must be added as an administrator to the channel/group with posting permissions.',
        'channel_removed_title': '✅ **Channel Removed**',
        'channel_removed_message': 'Channel configuration has been removed. You can add a new channel anytime from the settings.',
        'autopost_enabled_title': '🤖 **Auto-posting Enabled**',
        'autopost_disabled_title': '🤖 **Auto-posting Disabled**',
        'autopost_enabled_message': 'Auto-posting is now enabled. Generated promotional texts will automatically be posted to your channel.',
        'autopost_disabled_message': 'Auto-posting is now disabled. Generated promotional texts will not be posted to your channel.',
        'post_history_title': '📊 **Post History**',
        'post_history_empty': 'No posts yet. Generate some promotional content and post to your channel!',
        'channel_added_title': '✅ **Channel Added Successfully**',
        'channel_added_message': 'Channel @{} has been configured!\n\n{}',
        'channel_setup_failed_title': '❌ **Channel Setup Failed**',
        'channel_setup_failed_message': '{}\n\nPlease make sure:\n1. The bot is added to the channel/group\n2. The bot has administrator permissions\n3. The bot can post messages',
        'no_promo_text': '❌ No promotional text found. Please generate text first.',
        'confirm_post_title': '📤 **Confirm Channel Post**',
        'confirm_post_message': 'Channel: @{}\nProduct: {}\n\n**Preview:**\n{}',
        'no_pending_post': '❌ No pending post found.',
        'post_successful': '✅ **Post Successful**',
        'post_failed': '❌ **Post Failed**',
        'edit_post_title': '✏️ **Edit Post Text**',
        'edit_post_instructions': 'Send me the edited version of your promotional text. You can modify it as needed before posting to the channel.',
        'post_cancelled_title': '❌ **Post Cancelled**',
        'post_cancelled_message': 'The post has been cancelled. You can generate new promotional text or return to the main menu.',
        'confirm_edited_post_title': '📤 **Confirm Edited Post**',
        'product_limit_title': '📦 **Product Limit Reached**',
        'product_limit_message': 'You can only store 5 products at a time. Please delete some products first or clear all to add new ones.\n\nThis limit helps keep the bot fast and efficient! 🚀',
        'add_product_title': '🔗 **Add Product Link ({}/5)**',
        'add_product_instructions': 'Send me a product link from any online store!\n\n**Examples:**\n• Amazon: https://amazon.com/product-name\n• eBay: https://ebay.com/itm/product\n• AliExpress: https://aliexpress.com/item/product\n• Any e-commerce site with product pages\n\n**What I\'ll extract:**\n✅ Product name & price\n✅ Description & features\n✅ Brand & category\n✅ Product image\n\nJust paste the link below! 👇',
        'no_products_to_clear': '📦 **No Products to Clear**\n\nYou don\'t have any products saved yet.',
        'products_cleared': '🗑️ **All Products Cleared**\n\nRemoved {} products from your list. You can now add new products!',
        'product_details_title': '📦 **Product Details**',
        'product_details_question': 'Ready to create promotional content for this product?',
        'product_deleted_title': '🗑️ **Product Deleted**',
        'product_deleted_message': '**{}** has been removed from your products list.',
        'product_not_found': '❌ Product not found.',
        'invalid_url': '❌ **Invalid URL**\n\nPlease send a valid product link starting with http:// or https://',
        'analyzing_product': '🔄 **Analyzing Product...**\n\nExtracting information from the link...',
        'analyzing_with_ai': '🤖 **Analyzing with AI...**\n\nProcessing product information...',
        'extraction_failed': '❌ **Extraction Failed**\n\n{}\n\n**Suggestions:**\n• Try a different product link\n• Make sure the link is public\n• Check if the website allows automated access',
        'product_added_title': '✅ **Product Added Successfully!**',
        'product_added_message': 'Product saved to your list ({}/5)!',
        'promo_result': '🎯 **Promotional Text for: {}**',
        'promo_footer': '💡 *Feel free to customize this text for your specific needs!*',
        'language_title': '🌍 **Choose Your Language**',
        'language_subtitle': 'Select your preferred language:',
        'openai_prompt': 'Create a compelling promotional post for the following product: {}\n\nThe promotional text should:\n- Be engaging and attention-grabbing\n- Highlight key benefits and features\n- Include a strong call-to-action\n- Be suitable for social media posting\n- Use emojis appropriately\n- Be between 50-150 words\n- Sound persuasive and professional\n- BE WRITTEN IN ENGLISH\n\nProduct: {}',
        'system_prompt': 'You are a professional marketing copywriter specializing in creating compelling promotional content for products. Your writing style is engaging, persuasive, and modern. Write in English.',
        'add_channel_title': '📢 **Add Channel/Group**',
        'add_channel_instructions': 'Please send me the channel/group username (with @) or ID.\n\n**Example:** @mychannel\n\n**Note:** The bot must be added as an administrator to the channel/group with posting permissions.',
        'channel_removed_title': '✅ **Channel Removed**',
        'channel_removed_message': 'Channel configuration has been removed. You can add a new channel anytime from the settings.',
        'autopost_enabled_title': '🤖 **Auto-posting Enabled**',
        'autopost_disabled_title': '🤖 **Auto-posting Disabled**',
        'autopost_enabled_message': 'Auto-posting is now enabled. Generated promotional texts will automatically be posted to your channel.',
        'autopost_disabled_message': 'Auto-posting is now disabled. Generated promotional texts will not be posted to your channel.',
        'post_history_title': '📊 **Post History**',
        'post_history_empty': 'No posts yet. Generate some promotional content and post to your channel!',
        'channel_added_title': '✅ **Channel Added Successfully**',
        'channel_added_message': 'Channel @{} has been configured!\n\n{}',
        'channel_setup_failed_title': '❌ **Channel Setup Failed**',
        'channel_setup_failed_message': '{}\n\nPlease make sure:\n1. The bot is added to the channel/group\n2. The bot has administrator permissions\n3. The bot can post messages',
        'no_promo_text': '❌ No promotional text found. Please generate text first.',
        'confirm_post_title': '📤 **Confirm Channel Post**',
        'confirm_post_message': 'Channel: @{}\nProduct: {}\n\n**Preview:**\n{}',
        'no_pending_post': '❌ No pending post found.',
        'post_successful': '✅ **Post Successful**',
        'post_failed': '❌ **Post Failed**',
        'edit_post_title': '✏️ **Edit Post Text**',
        'edit_post_instructions': 'Send me the edited version of your promotional text. You can modify it as needed before posting to the channel.',
        'post_cancelled_title': '❌ **Post Cancelled**',
        'post_cancelled_message': 'The post has been cancelled. You can generate new promotional text or return to the main menu.',
        'generate_another_btn': '🔄 Generate Another',
        'post_to_channel_btn': '📤 Post to Channel',
        'main_menu_btn': '⬅️ Main Menu',
        'post_now_btn': '✅ Post Now',
        'edit_text_btn': '✏️ Edit Text',
        'cancel_btn': '❌ Cancel',
        'permissions_verified': 'Permissions verified successfully',
        'back_to_channel_settings': '⬅️ Back to Channel Settings',
        'confirm_edited_post_title': '📤 **Confirm Edited Post**',
        'posted_successfully': 'Posted successfully to {}',
        'failed_to_post': 'Failed to post: {}',
        'translate_btn': '🌍 Translate',
        'no_channel_configured': 'No channel configured',
        'translate_to_title': '🌍 **Translate Text**',
        'translate_to_subtitle': 'Choose target language:',
        'translate_to_english': '🇺🇸 English',
        'translate_to_russian': '🇷🇺 Russian',
        'translate_to_romanian': '🇷🇴 Romanian',
        'edit_generated_title': '✏️ **Edit Generated Text**',
        'edit_generated_instructions': 'Send me your edited version of the promotional text:'
    },
    'ru': {
        'welcome_title': '🚀 **Добро пожаловать в бот генератора рекламных текстов!** 🚀',
        'welcome_message': 'Я помогу вам создать потрясающие рекламные посты для ваших товаров!\n\nСначала выберите язык:',
        'language_selected': '✅ Язык установлен на русский!\n\nВыберите опцию ниже, чтобы начать:',
        'main_menu_title': '🚀 **Бот генератора рекламных текстов - Главное меню**',
        'main_menu_subtitle': 'Выберите опцию для продолжения:',
        'generate_promo': '🎯 Создать рекламный текст',
        'my_products': '📦 Мои товары',
        'examples': '💡 Примеры', 
        'help': '❓ Помощь',
        'language': '🌍 Язык',
        'back_menu': '⬅️ Назад в главное меню',
        'channel_settings': '📢 Настройки канала',
        'add_product_link': '➕ Добавить ссылку товара',
        'add_product': '➕ Добавить товар',
        'clear_all': '🗑️ Очистить все',
        'delete_product': '🗑️ Удалить товар',
        'open_link': '🔗 Открыть ссылку',
        'back_to_products': '⬅️ Назад к товарам',
        'from_my_products': '📦 Из моих товаров',
        'from_prompt': '✏️ Из запроса',
        'back_to_generation_menu': '⬅️ Назад к генерации',
        'generate_title': '🎯 **Создание рекламного текста**',
        'generate_instructions': 'Готов создать потрясающий рекламный контент!\n\n**Как продолжить:**\n1. Просто напишите название вашего товара в чате\n2. Я создам убедительный рекламный текст для вас\n3. Вы сможете скопировать и использовать его для маркетинга!\n\n**Примеры того, что отправить:**\n• "Беспроводные Bluetooth наушники"\n• "Органический зеленый чай"\n• "Игровая механическая клавиатура"\n• "Женские кроссовки для бега"\n\nПросто введите название товара ниже! 👇',
        'promo_choice_title': '🎯 **Создание рекламного текста**\n\nВыберите способ создания рекламы:',
        'promo_choice_subtitle': '📦 **Из моих товаров** - Создать рекламу из сохраненных товаров ({} доступно)\n\n✏️ **Из запроса** - Создать рекламу введя название товара\n\nЧто хотите сделать?',
        'no_products_available': '📦 **Нет доступных товаров**\n\nУ вас пока нет сохраненных товаров. Добавьте товары или создайте рекламу из запроса!',
        'select_product_title': '📦 **Выберите товар ({} доступно)**\n\nВыберите товар для создания рекламного текста:',
        'examples_title': '💡 **Примеры рекламных текстов**',
        'examples_content': 'Вот несколько примеров того, что я могу создать:\n\n**🎧 Беспроводные наушники:**\n*"Почувствуйте свободу с нашими премиальными беспроводными наушниками! 🎵 Кристально чистый звук, 30-часовая батарея и технология шумоподавления. Идеально для работы, путешествий и тренировок. Заказывайте сейчас и получите БЕСПЛАТНУЮ доставку! 🚚"*\n\n**👟 Кроссовки для бега:**\n*"Поднимите свою игру с нашими легкими кроссовками для бега! 🏃‍♀️ Продвинутая амортизация, дышащий материал и прочный дизайн. Готовитесь к марафону или ежедневным пробежкам - эти кроссовки обеспечат комфорт. Получите свои уже сегодня! 💪"*\n\n**📱 Смартфон:**\n*"Запечатлейте жизнь в потрясающих деталях с нашим новейшим смартфоном! 📸 Профессиональная камера, батарея на весь день и молниеносная производительность. Оставайтесь на связи, создавайте воспоминания и наслаждайтесь технологиями. Доступно сейчас! ✨"*\n\nГотовы создать свой? Просто введите любое название товара!',
        'help_title': '❓ **Помощь и поддержка**',
        'help_content': '**🔧 Как использовать этот бот:**\n\n1. **Создать рекламный текст** - Нажмите кнопку и отправьте название товара\n2. **Просмотр категорий** - Получите вдохновение от разных типов товаров\n3. **Просмотр примеров** - Посмотрите образцы рекламных текстов\n4. **Прямой ввод** - Вводите название товара в любое время!\n\n**💡 Советы для лучших результатов:**\n• Будьте конкретны (например, "Шумоподавляющие беспроводные наушники")\n• Включайте ключевые особенности ("Водонепроницаемый фитнес-трекер")\n• Упоминайте целевую аудиторию ("Игровая гарнитура для профессионалов")\n\n**🎯 Что я создаю для вас:**\n• Увлекательный рекламный текст (50-150 слов)\n• Контент готовый для соцсетей\n• Профессиональные маркетинговые тексты\n• Призывы к действию\n• Подходящие эмодзи\n\n**Команды:**\n/start - Показать главное меню\n/help - Показать это сообщение помощи\n\nНужна дополнительная помощь? Просто начните вводить название товара! 🚀',
        'channel_settings_title': '📢 **Настройки канала**',
        'channel_configured': 'Настроенный канал: @{}\nАвто-публикация: {}',
        'channel_not_configured': 'Канал еще не настроен. Добавьте канал, чтобы автоматически публиковать рекламный контент!',
        'auto_enabled': '✅ Включено',
        'auto_disabled': '❌ Отключено',
        'current_channel': '📋 Текущий: {}',
        'change_channel': '✏️ Изменить канал',
        'remove_channel': '❌ Удалить канал',
        'auto_post_on': '✅ ВКЛ',
        'auto_post_off': '❌ ВЫКЛ',
        'auto_post_toggle': '🤖 Авто-публикация: {}',
        'post_history': '📊 История публикаций',
        'add_channel_group': '➕ Добавить канал/группу',
        'my_products_title': '📦 **Мои товары**',
        'no_products_yet': 'Товары еще не добавлены!\n\nДобавьте ссылки на товары для создания потрясающего рекламного контента. Я могу анализировать любые ссылки интернет-магазинов и автоматически извлекать информацию о товарах.\n\n**Поддерживается:** Amazon, eBay, AliExpress, магазины Shopify и многие другие!',
        'my_products_count': '📦 **Мои товары ({}/5)**\n\nВаши сохраненные товары:\n\n',
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
        'system_prompt': 'Ты профессиональный маркетинговый копирайтер, специализирующийся на создании убедительного рекламного контента для товаров. Твой стиль письма привлекательный, убедительный и современный. Пиши на русском языке.',
        'add_channel_title': '📢 **Добавить канал/группу**',
        'add_channel_instructions': 'Пожалуйста, отправьте мне имя канала/группы (с @) или ID-ул.\n\n**Пример:** @mychannel\n\n**Примечание:** Бот должен быть добавлен как администратор в канал/группу с правами публикации сообщений.',
        'channel_removed_title': '✅ **Канал удален**',
        'channel_removed_message': 'Конфигурация канала была удалена. Вы можете добавить новый канал в любое время из настроек.',
        'autopost_enabled_title': '🤖 **Авто-публикация включена**',
        'autopost_disabled_title': '🤖 **Авто-публикация отключена**',
        'autopost_enabled_message': 'Авто-публикация теперь включена. Созданные рекламные тексты будут автоматически публиковаться в вашем канале.',
        'autopost_disabled_message': 'Авто-публикация теперь отключена. Созданные рекламные тексты не будут публиковаться в вашем канале.',
        'post_history_title': '📊 **История публикаций**',
        'post_history_empty': 'Публикаций пока нет. Создайте рекламный контент и опубликуйте его в канале!',
        'channel_added_title': '✅ **Канал успешно добавлен**',
        'channel_added_message': 'Канал @{} настроен!\n\n{}',
        'channel_setup_failed_title': '❌ **Настройка канала не удалась**',
        'channel_setup_failed_message': '{}\n\nПожалуйста, убедитесь что:\n1. Бот добавлен в канал/группу\n2. У бота есть права администратора\n3. Бот может публиковать сообщения',
        'no_promo_text': '❌ Рекламный текст не найден. Сначала создайте текст.',
        'confirm_post_title': '📤 **Подтвердить публикацию в канале**',
        'confirm_post_message': 'Канал: @{}\nТовар: {}\n\n**Предпросмотр:**\n{}',
        'no_pending_post': '❌ Ожидающая публикация не найдена.',
        'post_successful': '✅ **Публикация успешна**',
        'post_failed': '❌ **Публикация не удалась**',
        'edit_post_title': '✏️ **Редактировать текст поста**',
        'edit_post_instructions': 'Отправьте мне отредактированную версию рекламного текста. Вы можете изменить его перед публикацией в канале.',
        'post_cancelled_title': '❌ **Публикация отменена**',
        'post_cancelled_message': 'Публикация была отменена. Вы можете создать новый рекламный текст или вернуться в главное меню.',
        'generate_another_btn': '🔄 Создать еще один',
        'post_to_channel_btn': '📤 Публикация в канал',
        'main_menu_btn': '⬅️ Главное меню',
        'post_now_btn': '✅ Опубликовать сейчас',
        'edit_text_btn': '✏️ Редактировать текст',
        'cancel_btn': '❌ Отменить',
        'permissions_verified': 'Права доступа успешно проверены',
        'back_to_channel_settings': '⬅️ Назад к настройкам канала',
        'product_limit_title': '📦 **Лимит продуктов достигнут**',
        'product_limit_message': 'Вы можете сохранить только 5 продуктов одновременно. Пожалуйста, удалите некоторые продукты сначала или очистите все, чтобы добавить новые.\n\nЭтот лимит помогает боту работать быстро и эффективно! 🚀',
        'add_product_title': '🔗 **Добавить ссылку на товар ({}/5)**',
        'add_product_instructions': 'Отправьте мне ссылку на товар из любого интернет-магазина!\n\n**Примеры:**\n• Amazon: https://amazon.com/product-name\n• eBay: https://ebay.com/itm/product\n• AliExpress: https://aliexpress.com/item/product\n• Любой сайт электронной коммерции со страницами товаров\n\n**Что я извлеку:**\n✅ Название товара и цена\n✅ Описание и характеристики\n✅ Бренд и категория\n✅ Изображение товара\n\nПросто вставьте ссылку ниже! 👇',
        'invalid_url': '❌ **Неверная ссылка**\n\nПожалуйста, отправьте действительную ссылку на товар, начинающуюся с http:// или https://',
        'analyzing_product': '🔄 **Анализ товара...**\n\nИзвлечение информации из ссылки...',
        'analyzing_with_ai': '🤖 **Анализ с помощью ИИ...**\n\nОбработка информации о товаре...',
        'extraction_failed': '❌ **Извлечение не удалось**\n\n{}\n\n**Предложения:**\n• Попробуйте другую ссылку на товар\n• Убедитесь, что ссылка публичная\n• Проверьте, разрешает ли сайт автоматический доступ',
        'product_added_title': '✅ **Товар успешно добавлен!**',
        'product_added_message': 'Товар сохранен в ваш список ({}/5)!',
        'confirm_edited_post_title': '📤 **Подтвердить отредактированный пост**',
        'posted_successfully': 'Успешно опубликовано в {}',
        'failed_to_post': 'Не удалось опубликовать: {}',
        'translate_btn': '🌍 Перевести',
        'no_channel_configured': 'Канал не настроен',
        'translate_to_title': '🌍 **Перевести текст**',
        'translate_to_subtitle': 'Выберите язык для перевода:',
        'translate_to_english': '🇺🇸 Английский',
        'translate_to_russian': '🇷🇺 Русский',
        'translate_to_romanian': '🇷🇴 Румынский',
        'edit_generated_title': '✏️ **Редактировать сгенерированный текст**',
        'edit_generated_instructions': 'Отправьте мне отредактированную версию рекламного текста:'
    },
    'ro': {
        'welcome_title': '🚀 **Bun venit la botul generator de texte promoționale!** 🚀',
        'welcome_message': 'Te pot ajuta să creezi postări promoționale uimitoare pentru produsele tale!\n\nAlege mai întâi limba:',
        'language_selected': '✅ Limba setată în română!\n\nAlege o opțiune de mai jos pentru a începe:',
        'main_menu_title': '🚀 **Bot generator de texte promoționale - Meniul principal**',
        'main_menu_subtitle': 'Alege o opțiune pentru a continua:',
        'generate_promo': '🎯 Generează text promoțional',
        'my_products': '📦 Produsele mele',
        'examples': '💡 Exemple',
        'help': '❓ Ajutor',
        'language': '🌍 Limba',
        'back_menu': '⬅️ Înapoi la meniul principal',
        'channel_settings': '📢 Setări canal',
        'add_product_link': '➕ Adaugă link produs',
        'add_product': '➕ Adaugă produs',
        'clear_all': '🗑️ Șterge toate',
        'delete_product': '🗑️ Șterge produs',
        'open_link': '🔗 Deschide link',
        'back_to_products': '⬅️ Înapoi la produse',
        'from_my_products': '📦 Din produsele mele',
        'from_prompt': '✏️ Din prompt',
        'back_to_generation_menu': '⬅️ Înapoi la generare',
        'generate_title': '🎯 **Generare text promoțional**',
        'generate_instructions': 'Gata să creez conținut promoțional uimitor!\n\n**Cum să continui:**\n1. Pur și simplu scrie numele produsului tău în chat\n2. Voi genera un text promoțional convingător pentru tine\n3. Apoi îl poți copia și folosi pentru marketing!\n\n**Exemple de ce să trimiți:**\n• "Căști Bluetooth wireless"\n• "Ceai verde organic"\n• "Tastatură mecanică pentru gaming"\n• "Pantofi de alergare pentru femei"\n\nScrie numele produsului mai jos! 👇',
        'promo_choice_title': '🎯 **Generare text promoțional**\n\nAlege cum vrei să creezi promoția:',
        'promo_choice_subtitle': '📦 **Din produsele mele** - Generează promoție din produsele salvate ({} disponibile)\n\n✏️ **Din prompt** - Creează promoție scriind numele produsului\n\nCe vrei să faci?',
        'no_products_available': '📦 **Nu sunt produse disponibile**\n\nNu ai încă produse salvate. Adaugă produse mai întâi sau creează o promoție din prompt!',
        'select_product_title': '📦 **Selectează produs ({} disponibile)**\n\nAlege un produs pentru a genera text promoțional:',
        'examples_title': '💡 **Exemple de texte promoționale**',
        'examples_content': 'Iată câteva exemple de ce pot genera:\n\n**🎧 Căști wireless:**\n*"Simte libertatea cu căștile noastre premium wireless! 🎵 Sunet cristalin, baterie de 30 de ore și tehnologie de anulare a zgomotului. Perfect pentru muncă, călătorii și antrenamente. Comandă acum și beneficiezi de livrare GRATUITĂ! 🚚"*\n\n**👟 Pantofi de alergare:**\n*"Ridică-ți nivelul cu pantofii noștri ușori de alergare! 🏃‍♀️ Amortizare avansată, material respirabil și design durabil. Fie că te antrenezi pentru maraton sau pentru alergări zilnice, acești pantofi te vor menține confortabil. Obține-i astăzi! 💪"*\n\n**📱 Smartphone:**\n*"Surprinde viața în detalii uimitoare cu cel mai nou smartphone! 📸 Cameră de nivel profesional, baterie pentru toată ziua și performanță fulgerătoare. Rămâi conectat, creează amintiri și experimentează tehnologia la cel mai înalt nivel. Disponibil acum! ✨"*\n\nGata să creezi propriul tău? Scrie orice nume de produs!',
        'help_title': '❓ **Ajutor și suport**',
        'help_content': '**🔧 Cum să folosești acest bot:**\n\n1. **Generează text promoțional** - Apasă butonul și trimite numele produsului\n2. **Răsfoiește categoriile** - Obține inspirație de la diferite tipuri de produse\n3. **Vezi exemple** - Privește exemple de texte promoționale\n4. **Introducere directă** - Scrie orice nume de produs oricând!\n\n**💡 Sfaturi pentru rezultate mai bune:**\n• Fii specific (ex: "Căști wireless cu anulare zgomot")\n• Include caracteristici cheie ("Tracker fitness rezistent la apă")\n• Menționează publicul țintă ("Căști gaming pentru profesioniști")\n\n**🎯 Ce creez pentru tine:**\n• Text promoțional captivant (50-150 cuvinte)\n• Conținut gata pentru rețelele sociale\n• Texte de marketing profesionale\n• Chemări la acțiune\n• Emoji-uri potrivite\n\n**Comenzi:**\n/start - Arată meniul principal\n/help - Arată acest mesaj de ajutor\n\nAi nevoie de mai mult ajutor? Doar începe să scrii numele produsului! 🚀',
        'channel_settings_title': '📢 **Setări canal**',
        'channel_configured': 'Canal configurat: @{}\nPostare automată: {}',
        'channel_not_configured': 'Niciun canal configurat încă. Adaugă un canal pentru a posta automat conținutul promoțional!',
        'auto_enabled': '✅ Activat',
        'auto_disabled': '❌ Dezactivat',
        'current_channel': '📋 Curent: {}',
        'change_channel': '✏️ Schimbă canal',
        'remove_channel': '❌ Elimină canal',
        'auto_post_on': '✅ PORNIT',
        'auto_post_off': '❌ OPRIT',
        'auto_post_toggle': '🤖 Postare automată: {}',
        'post_history': '📊 Istoric postări',
        'add_channel_group': '➕ Adaugă canal/grup',
        'my_products_title': '📦 **Produsele mele**',
        'no_products_yet': 'Nu sunt produse adăugate încă!\n\nAdaugă linkuri de produse pentru a începe să creezi conținut promoțional uimitor. Pot analiza orice link de magazin online și extrage automat informațiile despre produs.\n\n**Suportat:** Amazon, eBay, AliExpress, magazine Shopify și multe altele!',
        'my_products_count': '📦 **Produsele mele ({}/5)**\n\nProdusele tale salvate:\n\n',
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
        'system_prompt': 'Ești un copywriter de marketing profesional specializat în crearea de conținut promoțional convingător pentru produse. Stilul tău de scriere este captivant, convingător și modern. Scrie în limba română.',
        'add_channel_title': '📢 **Adaugă canal/grup**',
        'add_channel_instructions': 'Te rog trimite-mi numele canalului/grupului (cu @) sau ID-ul.\n\n**Exemplu:** @mychannel\n\n**Notă:** Botul trebuie să fie adăugat ca administrator în canal/grup cu permisiuni de postare.',
        'channel_removed_title': '✅ **Canal eliminat**',
        'channel_removed_message': 'Configurația canalului a fost eliminată. Poți adăuga un canal nou oricând din setări.',
        'autopost_enabled_title': '🤖 **Postare automată activată**',
        'autopost_disabled_title': '🤖 **Postare automată dezactivată**',
        'autopost_enabled_message': 'Postarea automată este acum activată. Textele promoționale generate vor fi postate automat în canalul tău.',
        'autopost_disabled_message': 'Postarea automată este acum dezactivată. Textele promoționale generate nu vor fi postate în canalul tău.',
        'post_history_title': '📊 **Istoric postări**',
        'post_history_empty': 'Nu sunt postări încă. Generează conținut promoțional și postează în canalul tău!',
        'channel_added_title': '✅ **Canal adăugat cu succes**',
        'channel_added_message': 'Canalul @{} a fost configurat!\n\n{}',
        'channel_setup_failed_title': '❌ **Configurarea canalului a eșuat**',
        'channel_setup_failed_message': '{}\n\nTe rog asigură-te că:\n1. Botul este adăugat în canal/grup\n2. Botul are permisiuni de administrator\n3. Botul poate posta mesaje',
        'no_promo_text': '❌ Text promoțional nu a fost găsit. Te rog generează textul mai întâi.',
        'confirm_post_title': '📤 **Confirmă postarea în canal**',
        'confirm_post_message': 'Canal: @{}\nProdus: {}\n\n**Previzualizare:**\n{}',
        'no_pending_post': '❌ Nu există postare în așteptare.',
        'post_successful': '✅ **Postare reușită**',
        'post_failed': '❌ **Postarea a eșuat**',
        'edit_post_title': '✏️ **Editează textul postării**',
        'edit_post_instructions': 'Trimite-mi versiunea editată a textului promoțional. O poți modifica după cum este necesar înainte de postarea în canal.',
        'post_cancelled_title': '❌ **Postare anulată**',
        'post_cancelled_message': 'Postarea a fost anulată. Poți genera un text promoțional nou sau să te întorci la meniul principal.',
        'generate_another_btn': '🔄 Generează altul',
        'post_to_channel_btn': '📤 Postare în canal',
        'main_menu_btn': '⬅️ Meniul principal',
        'post_now_btn': '✅ Postare acum',
        'edit_text_btn': '✏️ Editează textul',
        'cancel_btn': '❌ Anulează',
        'permissions_verified': 'Permisiunile au fost verificate cu succes',
        'back_to_channel_settings': '⬅️ Înapoi la setările canalului',
        'product_limit_title': '📦 **Limita de produse atinsă**',
        'product_limit_message': 'Poți stoca doar 5 produse odată. Te rog șterge câteva produse mai întâi sau șterge toate pentru a adăuga altele noi.\n\nAceastă limită ajută botul să funcționeze rapid și eficient! 🚀',
        'add_product_title': '🔗 **Adaugă link produs ({}/5)**',
        'add_product_instructions': 'Trimite-mi un link de produs de la orice magazin online!\n\n**Exemple:**\n• Amazon: https://amazon.com/product-name\n• eBay: https://ebay.com/itm/product\n• AliExpress: https://aliexpress.com/item/product\n• Orice site de comerț electronic cu pagini de produse\n\n**Ce voi extrage:**\n✅ Numele produsului și prețul\n✅ Descrierea și caracteristicile\n✅ Marca și categoria\n✅ Imaginea produsului\n\nDoar lipește link-ul mai jos! 👇',
        'invalid_url': '❌ **URL invalid**\n\nTe rog trimite un link valid de produs care începe cu http:// sau https://',
        'analyzing_product': '🔄 **Analizez produsul...**\n\nExtrag informații din link...',
        'analyzing_with_ai': '🤖 **Analizez cu AI...**\n\nProcesez informațiile despre produs...',
        'extraction_failed': '❌ **Extragerea a eșuat**\n\n{}\n\n**Sugestii:**\n• Încearcă un alt link de produs\n• Asigură-te că link-ul este public\n• Verifică dacă site-ul permite accesul automatizat',
        'product_added_title': '✅ **Produs adăugat cu succes!**',
        'product_added_message': 'Produsul a fost salvat în lista ta ({}/5)!',
        'confirm_edited_post_title': '📤 **Confirmă postarea editată**',
        'posted_successfully': 'Postat cu succes în {}',
        'failed_to_post': 'Postarea a eșuat: {}',
        'translate_btn': '🌍 Traduce',
        'no_channel_configured': 'Niciun canal configurat',
        'translate_to_title': '🌍 **Traduce textul**',
        'translate_to_subtitle': 'Alege limba țintă:',
        'translate_to_english': '🇺🇸 Engleză',
        'translate_to_russian': '🇷🇺 Rusă',
        'translate_to_romanian': '🇷🇴 Română',
        'edit_generated_title': '✏️ **Editează textul generat**',
        'edit_generated_instructions': 'Trimite-mi versiunea editată a textului promoțional:'
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
             InlineKeyboardButton(self.get_text('my_products', context), callback_data='my_products')],
            [InlineKeyboardButton(self.get_text('examples', context), callback_data='examples'),
             InlineKeyboardButton(self.get_text('help', context), callback_data='help')],
            [InlineKeyboardButton(self.get_text('channel_settings', context), callback_data='channel_settings'),
             InlineKeyboardButton(self.get_text('language', context), callback_data='language_select')]
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
            auto_status = self.get_text('auto_post_on', context) if auto_post else self.get_text('auto_post_off', context)
            keyboard = [
                [InlineKeyboardButton(self.get_text('current_channel', context, channel_id), callback_data='channel_info')],
                [InlineKeyboardButton(self.get_text('change_channel', context), callback_data='set_channel'),
                 InlineKeyboardButton(self.get_text('remove_channel', context), callback_data='remove_channel')],
                [InlineKeyboardButton(self.get_text('auto_post_toggle', context, auto_status), callback_data='toggle_autopost')],
                [InlineKeyboardButton(self.get_text('post_history', context), callback_data='post_history')],
                [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton(self.get_text('add_channel_group', context), callback_data='set_channel')],
                [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
            ]
        return InlineKeyboardMarkup(keyboard)

    def get_post_generation_keyboard(self, context):
        """Create keyboard for after text generation with channel posting option."""
        channel_info = context.user_data.get('channel_info', {})
        has_channel = bool(channel_info.get('channel_id'))
        
        if has_channel:
            keyboard = [
                [InlineKeyboardButton(self.get_text('generate_another_btn', context), callback_data='generate_promo'),
                 InlineKeyboardButton(self.get_text('post_to_channel_btn', context), callback_data='post_to_channel')],
                [InlineKeyboardButton(self.get_text('translate_btn', context), callback_data='translate_text'),
                 InlineKeyboardButton(self.get_text('edit_text_btn', context), callback_data='edit_generated_text')],
                [InlineKeyboardButton(self.get_text('main_menu_btn', context), callback_data='main_menu')]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton(self.get_text('generate_another_btn', context), callback_data='generate_promo'),
                 InlineKeyboardButton(self.get_text('translate_btn', context), callback_data='translate_text')],
                [InlineKeyboardButton(self.get_text('edit_text_btn', context), callback_data='edit_generated_text'),
                 InlineKeyboardButton(self.get_text('main_menu_btn', context), callback_data='main_menu')]
            ]
        return InlineKeyboardMarkup(keyboard)

    def get_post_confirmation_keyboard(self, context):
        """Create keyboard for post confirmation."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('post_now_btn', context), callback_data='confirm_post'),
             InlineKeyboardButton(self.get_text('edit_text_btn', context), callback_data='edit_post')],
            [InlineKeyboardButton(self.get_text('cancel_btn', context), callback_data='cancel_post')]
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
            
            return True, "permissions_verified"
            
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
        
        return " ".join(hashtags[:6])  # Limit to 6 hashtags

    async def post_to_channel_action(self, context, text, product_name):
        """Post the promotional text to configured channel."""
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id')
        
        if not channel_id:
            return False, self.get_text('no_channel_configured', context)
        
        try:
            # Check if text already contains hashtags
            has_hashtags = '#' in text
            
            if has_hashtags:
                # Text already has hashtags, post as is
                final_post = text
            else:
                # Generate hashtags (limited to 5-6) only if text doesn't have them
                hashtags = self.generate_hashtags(product_name, context)
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
            
            return True, self.get_text('posted_successfully', context, channel_id)
            
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
            
            return False, self.get_text('failed_to_post', context, str(e))

    def is_valid_url(self, url):
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    async def scrape_product_info(self, url):
        """Scrape product information from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic info using common selectors
            raw_data = {
                'url': url,
                'title': self.extract_title(soup),
                'price': self.extract_price(soup),
                'description': self.extract_description(soup),
                'image_url': self.extract_image(soup, url),
                'brand': self.extract_brand(soup),
                'raw_text': soup.get_text()[:2000]  # Limit text for AI analysis
            }
            
            return raw_data
            
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
            return None, f"Scraping failed: {str(e)}"

    def extract_title(self, soup):
        """Extract product title from page."""
        # Try multiple common selectors
        selectors = [
            'h1[data-automation-id="product-title"]',  # Generic
            'h1.product-title',
            'h1#product-title', 
            '.product-name h1',
            '.product-title',
            'h1[class*="title"]',
            'h1[class*="product"]',
            'h1[id*="title"]',
            'h1[id*="product"]',
            'title',
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return "Product Title Not Found"

    def extract_price(self, soup):
        """Extract product price from page."""
        # Try multiple price selectors
        selectors = [
            '.price-current',
            '.price',
            '.product-price',
            '[class*="price"]',
            '[data-testid*="price"]',
            '.cost',
            '.amount',
            '[class*="cost"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                # Look for price patterns
                price_match = re.search(r'[\$€£¥₽]\s*[\d,]+\.?\d*|\d+[,.]?\d*\s*[\$€£¥₽]', text)
                if price_match:
                    return price_match.group()
        
        return "Price Not Found"

    def extract_description(self, soup):
        """Extract product description from page."""
        selectors = [
            '.product-description',
            '.description',
            '[class*="description"]',
            '.product-details',
            '.product-info',
            '[class*="details"]',
            '.product-summary',
            'meta[name="description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    desc = element.get('content', '').strip()
                else:
                    desc = element.get_text().strip()
                
                if desc and len(desc) > 20:
                    return desc[:500]  # Limit description length
        
        return "Description Not Found"

    def extract_image(self, soup, base_url):
        """Extract product image URL."""
        selectors = [
            '.product-image img',
            '.main-image img',
            '[class*="product"] img',
            '[class*="main"] img',
            'img[alt*="product"]',
            'img[class*="product"]',
            'img[src*="product"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src')
                if src:
                    return urljoin(base_url, src)
        
        return None

    def extract_brand(self, soup):
        """Extract product brand from page."""
        selectors = [
            '.brand',
            '.product-brand',
            '[class*="brand"]',
            '[data-testid*="brand"]',
            'meta[property="product:brand"]',
            'span[itemprop="brand"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    brand = element.get('content', '').strip()
                else:
                    brand = element.get_text().strip()
                
                if brand and len(brand) < 50:
                    return brand
        
        return "Brand Not Found"

    async def analyze_product_with_ai(self, raw_data):
        """Use AI to analyze and clean up product information."""
        try:
            # Create a concise prompt to save tokens
            prompt = f"""Analyze this product data and extract key information:

URL: {raw_data['url']}
Title: {raw_data['title']}
Price: {raw_data['price']}
Brand: {raw_data['brand']}
Description: {raw_data['description']}

Extract and return ONLY:
1. Clean product name (max 50 chars) 
2. Category (Electronics/Fashion/Home/Beauty/Other)
3. Key features (max 100 chars)
4. Clean price if found

Format: NAME|CATEGORY|FEATURES|PRICE"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a product data analyzer. Be concise to save tokens."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,  # Limit tokens to save money
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            parts = result.split('|')
            
            if len(parts) >= 4:
                return {
                    'name': parts[0].strip(),
                    'category': parts[1].strip(),
                    'features': parts[2].strip(),
                    'price': parts[3].strip(),
                    'brand': raw_data['brand'],
                    'image_url': raw_data['image_url'],
                    'url': raw_data['url']
                }
            else:
                # Fallback to raw data if AI parsing fails
                return {
                    'name': raw_data['title'][:50],
                    'category': 'Other',
                    'features': raw_data['description'][:100],
                    'price': raw_data['price'],
                    'brand': raw_data['brand'],
                    'image_url': raw_data['image_url'],
                    'url': raw_data['url']
                }
                
        except Exception as e:
            # Fallback to raw data if AI fails
            return {
                'name': raw_data['title'][:50],
                'category': 'Other', 
                'features': raw_data['description'][:100],
                'price': raw_data['price'],
                'brand': raw_data['brand'],
                'image_url': raw_data['image_url'],
                'url': raw_data['url']
            }

    def get_my_products_keyboard(self, context):
        """Create keyboard for My Products menu."""
        products = context.user_data.get('products', [])
        
        if not products:
            keyboard = [
                [InlineKeyboardButton(self.get_text('add_product_link', context), callback_data='add_product')],
                [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
            ]
        else:
            keyboard = []
            
            # Show products (max 5)
            for i, product in enumerate(products):
                keyboard.append([InlineKeyboardButton(
                    f"📦 {product['name'][:25]}{'...' if len(product['name']) > 25 else ''}", 
                    callback_data=f'product_{i}'
                )])
            
            # Add controls
            keyboard.append([
                InlineKeyboardButton(self.get_text('add_product', context), callback_data='add_product'),
                InlineKeyboardButton(self.get_text('clear_all', context), callback_data='clear_products')
            ])
            keyboard.append([InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')])
        
        return InlineKeyboardMarkup(keyboard)

    def get_product_detail_keyboard(self, context, product_index):
        """Create keyboard for individual product details."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('delete_product', context), callback_data=f'delete_product_{product_index}'),
             InlineKeyboardButton(self.get_text('open_link', context), url=context.user_data['products'][product_index]['url'])],
            [InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_promo_creation_choice_keyboard(self, context):
        """Create keyboard for promo creation choice."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('from_my_products', context), callback_data='promo_from_product'),
             InlineKeyboardButton(self.get_text('from_prompt', context), callback_data='promo_from_prompt')],
            [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_product_selection_keyboard(self, context):
        """Create keyboard for selecting a product to generate promo from."""
        products = context.user_data.get('products', [])
        keyboard = []
        
        for i, product in enumerate(products):
            keyboard.append([InlineKeyboardButton(
                f"📦 {product['name'][:30]}{'...' if len(product['name']) > 30 else ''}", 
                callback_data=f'select_product_{i}'
            )])
        
        keyboard.append([InlineKeyboardButton(self.get_text('back_to_generation_menu', context), callback_data='generate_promo')])
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
            await self.cancel_post(query, context)        # Product management callbacks
        elif query.data == 'translate_text':
            await self.translate_generated_text(query, context)
        elif query.data == 'edit_generated_text':
            await self.edit_generated_text(query, context)
        elif query.data == 'my_products':
            await self.show_my_products(query, context)
        elif query.data == 'add_product':
            await self.prompt_add_product(query, context)
        elif query.data == 'clear_products':
            await self.clear_all_products(query, context)
        elif query.data.startswith('product_'):
            product_index = int(query.data.split('_')[1])
            await self.show_product_detail(query, context, product_index)
        elif query.data.startswith('delete_product_'):
            product_index = int(query.data.split('_')[2])
            await self.delete_product(query, context, product_index)
        elif query.data.startswith('gen_promo_'):
            product_index = int(query.data.split('_')[2])
            await self.generate_product_promo(query, context, product_index)
        elif query.data == 'promo_from_product':
            await self.show_promo_from_product(query, context)
        elif query.data == 'promo_from_prompt':
            await self.show_promo_from_prompt(query, context)
        elif query.data.startswith('select_product_'):
            product_index = int(query.data.split('_')[2])
            await self.generate_product_promo(query, context, product_index)
        elif query.data.startswith('translate_'):
            target_lang = query.data.split('_')[1]
            await self.perform_translation(query, context, target_lang)

    async def show_generate_promo(self, query, context):
        """Show the promo generation choice menu."""
        products = context.user_data.get('products', [])
        
        if not products:
            # No products available, go directly to prompt-based
            await query.edit_message_text(
                text=self.get_text('generate_instructions', context),
                parse_mode='Markdown',
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
        else:
            # Show choice between product-based and prompt-based
            text = f"{self.get_text('promo_choice_title', context)}\n\n{self.get_text('promo_choice_subtitle', context, len(products))}"
            await query.edit_message_text(
                text=text,
                parse_mode='Markdown',
                reply_markup=self.get_promo_creation_choice_keyboard(context)
            )

    async def show_promo_from_product(self, query, context):
        """Show product selection for promo generation."""
        products = context.user_data.get('products', [])
        
        if not products:
            await query.edit_message_text(
                text=self.get_text('no_products_available', context),
                parse_mode='Markdown',
                reply_markup=self.get_promo_creation_choice_keyboard(context)
            )
        else:
            text = self.get_text('select_product_title', context, len(products))
            await query.edit_message_text(
                text=text,
                parse_mode='Markdown',
                reply_markup=self.get_product_selection_keyboard(context)
            )

    async def show_promo_from_prompt(self, query, context):
        """Show prompt-based promo generation instructions."""
        await query.edit_message_text(
            text=self.get_text('generate_instructions', context),
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages from users."""
        # Handle channel input
        if await self.handle_channel_input(update, context):
            return
        
        # Handle post editing
        if await self.handle_post_edit(update, context):
            return
            
        # Handle generated text editing
        if await self.handle_generated_text_edit(update, context):
            return
            
        # Handle product link input
        if await self.handle_product_link(update, context):
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
            try:
                await update.message.reply_text(
                    self.get_text('rate_limit', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
            except:
                pass
        except openai.error.InvalidRequestError as e:
            logger.error(f"Invalid request to OpenAI: {e}")
            try:
                await update.message.reply_text(
                    self.get_text('request_error', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
            except:
                pass
        except Exception as e:
            logger.error(f"Error generating promo text: {e}")
            try:
                await update.message.reply_text(
                    self.get_text('general_error', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
            except:
                pass

    async def show_my_products(self, query, context):
        """Show My Products menu."""
        products = context.user_data.get('products', [])
        
        if not products:
            text = f"{self.get_text('my_products_title', context)}\n\n{self.get_text('no_products_yet', context)}"
        else:
            text = self.get_text('my_products_count', context, len(products))
            for i, product in enumerate(products, 1):
                text += f"{i}. **{product['name']}**\n   💰 {product['price']} | 📂 {product['category']}\n\n"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_my_products_keyboard(context)
        )

    async def prompt_add_product(self, query, context):
        """Prompt user to add a product link."""
        products = context.user_data.get('products', [])
        
        if len(products) >= 5:
            text = f"{self.get_text('product_limit_title', context)}\n\n{self.get_text('product_limit_message', context)}"
        else:
            context.user_data['waiting_for_product_link'] = True
            text = f"{self.get_text('add_product_title', context, len(products))}\n\n{self.get_text('add_product_instructions', context)}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def clear_all_products(self, query, context):
        """Clear all products with confirmation."""
        products = context.user_data.get('products', [])
        
        if not products:
            text = "📦 **No Products to Clear**\n\nYou don't have any products saved yet."
        else:
            context.user_data['products'] = []
            text = f"🗑️ **All Products Cleared**\n\nRemoved {len(products)} products from your list. You can now add new products!"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_my_products_keyboard(context)
        )

    async def show_product_detail(self, query, context, product_index):
        """Show detailed information about a specific product."""
        products = context.user_data.get('products', [])
        
        if product_index >= len(products):
            await query.edit_message_text(
                "❌ Product not found.",
                reply_markup=self.get_my_products_keyboard(context)
            )
            return
        
        product = products[product_index]
        
        text = f"📦 **Product Details**\n\n"
        text += f"**Name:** {product['name']}\n"
        text += f"**Price:** {product['price']}\n"
        text += f"**Brand:** {product['brand']}\n"
        text += f"**Category:** {product['category']}\n"
        text += f"**Features:** {product['features']}\n\n"
        text += f"Ready to create promotional content for this product?"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_product_detail_keyboard(context, product_index)
        )

    async def delete_product(self, query, context, product_index):
        """Delete a specific product."""
        products = context.user_data.get('products', [])
        
        if product_index >= len(products):
            await query.edit_message_text(
                "❌ Product not found.",
                reply_markup=self.get_my_products_keyboard(context)
            )
            return
        
        product_name = products[product_index]['name']
        del products[product_index]
        context.user_data['products'] = products
        
        text = f"🗑️ **Product Deleted**\n\n**{product_name}** has been removed from your products list."
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_my_products_keyboard(context)
        )

    async def generate_product_promo(self, query, context, product_index):
        """Generate promotional text for a specific product."""
        products = context.user_data.get('products', [])
        
        if product_index >= len(products):
            await query.edit_message_text(
                "❌ Product not found.",
                reply_markup=self.get_my_products_keyboard(context)
            )
            return
        
        product = products[product_index]
        
        # Show typing action
        await context.bot.send_chat_action(chat_id=query.message.chat.id, action='typing')
        
        try:
            # Create product-specific prompt
            product_info = f"Product: {product['name']}\nPrice: {product['price']}\nBrand: {product['brand']}\nCategory: {product['category']}\nKey Features: {product['features']}"
            
            # Use the translated prompt with product info
            prompt = self.get_text('openai_prompt', context, product_info, product_info)
            
            system_prompt = self.get_text('system_prompt', context)
            
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
            
            # Store for channel posting
            context.user_data['last_generated_text'] = promo_text
            context.user_data['last_product_name'] = product['name']
            
            # Format response
            formatted_response = f"""
{self.get_text('promo_result', context, product['name'])}

{promo_text}

---
{self.get_text('promo_footer', context)}
            """
            
            await query.edit_message_text(
                text=formatted_response,
                parse_mode='Markdown',
                reply_markup=self.get_post_generation_keyboard(context)
            )
            
            # Check for auto-posting
            channel_info = context.user_data.get('channel_info', {})
            if channel_info.get('auto_post', False) and channel_info.get('channel_id'):
                success, message = await self.post_to_channel_action(context, promo_text, product['name'])
                
                status_emoji = "✅" if success else "❌"
                auto_post_msg = f"\n\n{status_emoji} **Auto-post:** {message}"
                
                try:
                    await query.edit_message_text(
                        formatted_response + auto_post_msg,
                        parse_mode='Markdown',
                        reply_markup=self.get_post_generation_keyboard(context)
                    )
                except:
                    pass
        
        except openai.error.RateLimitError:
            try:
                await query.edit_message_text(
                    self.get_text('rate_limit', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
            except:
                await query.message.reply_text(
                    self.get_text('rate_limit', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
        except openai.error.InvalidRequestError as e:
            logger.error(f"Invalid request to OpenAI: {e}")
            try:
                await query.edit_message_text(
                    self.get_text('request_error', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
            except:
                await query.message.reply_text(
                    self.get_text('request_error', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
        except Exception as e:
            logger.error(f"Error generating product promo: {e}")
            try:
                await query.edit_message_text(
                    self.get_text('general_error', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
            except:
                await query.message.reply_text(
                    self.get_text('general_error', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )

    async def handle_product_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product link input from user."""
        if not context.user_data.get('waiting_for_product_link'):
            return False
        
        url = update.message.text.strip()
        context.user_data['waiting_for_product_link'] = False
        
        # Validate URL
        if not self.is_valid_url(url):
            await update.message.reply_text(
                self.get_text('invalid_url', context),
                parse_mode='Markdown',
                reply_markup=self.get_my_products_keyboard(context)
            )
            return True
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            self.get_text('analyzing_product', context),
            parse_mode='Markdown'
        )
        
        # Scrape product info
        raw_data = await self.scrape_product_info(url)
        
        if isinstance(raw_data, tuple):  # Error occurred
            await processing_msg.edit_text(
                self.get_text('extraction_failed', context, raw_data[1]),
                parse_mode='Markdown',
                reply_markup=self.get_my_products_keyboard(context)
            )
            return True
        
        # Analyze with AI
        await processing_msg.edit_text(
            self.get_text('analyzing_with_ai', context),
            parse_mode='Markdown'
        )
        
        product_data = await self.analyze_product_with_ai(raw_data)
        
        # Store product
        if 'products' not in context.user_data:
            context.user_data['products'] = []
        
        context.user_data['products'].append(product_data)
        
        # Show success message
        text = f"{self.get_text('product_added_title', context)}\n\n"
        text += f"**Name:** {product_data['name']}\n"
        text += f"**Price:** {product_data['price']}\n"
        text += f"**Brand:** {product_data['brand']}\n"
        text += f"**Category:** {product_data['category']}\n\n"
        text += self.get_text('product_added_message', context, len(context.user_data['products']))
        
        await processing_msg.edit_text(
            text,
            parse_mode='Markdown',
            reply_markup=self.get_my_products_keyboard(context)
        )
        
        return True

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

    async def show_help(self, query, context):
        """Show help information."""
        await query.edit_message_text(
            text=self.get_text('help_content', context),
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def show_examples(self, query, context):
        """Show example promotional texts."""
        await query.edit_message_text(
            text=self.get_text('examples_content', context),
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def show_channel_settings(self, query, context):
        """Show channel settings menu."""
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id')
        
        if channel_id:
            auto_status = self.get_text('auto_post_on', context) if channel_info.get('auto_post', False) else self.get_text('auto_post_off', context)
            text = f"{self.get_text('channel_settings_title', context)}\n\n{self.get_text('channel_configured', context, channel_id, auto_status)}"
        else:
            text = f"{self.get_text('channel_settings_title', context)}\n\n{self.get_text('channel_not_configured', context)}"
        
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
        text = f"{self.get_text('add_channel_title', context)}\n\n{self.get_text('add_channel_instructions', context)}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def remove_channel(self, query, context):
        """Remove configured channel."""
        if 'channel_info' in context.user_data:
            del context.user_data['channel_info']
        
        text = f"{self.get_text('channel_removed_title', context)}\n\n{self.get_text('channel_removed_message', context)}"
        
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
        
        if auto_post:
            title = self.get_text('autopost_enabled_title', context)
            message = self.get_text('autopost_enabled_message', context)
        else:
            title = self.get_text('autopost_disabled_title', context)
            message = self.get_text('autopost_disabled_message', context)
        
        text = f"{title}\n\n{message}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def show_post_history(self, query, context):
        """Show posting history."""
        history = context.user_data.get('post_history', [])
        
        if not history:
            text = f"{self.get_text('post_history_title', context)}\n\n{self.get_text('post_history_empty', context)}"
        else:
            text = f"{self.get_text('post_history_title', context)}\n\n"
            for i, post in enumerate(history[-10:], 1):  # Show last 10 posts
                status_emoji = "✅" if post['status'] == 'success' else "❌"
                text += f"{i}. {status_emoji} **{post['product']}**\n   {post['timestamp']} - {post['status']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton(self.get_text('back_to_channel_settings', context), callback_data='channel_settings'),
             InlineKeyboardButton(self.get_text('main_menu_btn', context), callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
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
            
            # Translate the message if it's a key
            translated_message = self.get_text(message, context) if message == 'permissions_verified' else message
            text = f"{self.get_text('channel_added_title', context)}\n\n{self.get_text('channel_added_message', context, channel_input.replace('@', ''), translated_message)}"
        else:
            text = f"{self.get_text('channel_setup_failed_title', context)}\n\n{self.get_text('channel_setup_failed_message', context, message)}"
        
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
                self.get_text('no_promo_text', context),
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
        
        # Check if text already has hashtags for preview
        has_hashtags = '#' in stored_text
        if has_hashtags:
            preview_text = stored_text
        else:
            hashtags = self.generate_hashtags(product_name, context)
            preview_text = f"{stored_text}\n\n{hashtags}"
        
        text = f"{self.get_text('confirm_post_title', context)}\n\n{self.get_text('confirm_post_message', context, channel_id, product_name, preview_text[:200] + ('...' if len(preview_text) > 200 else ''))}"
        
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
                self.get_text('no_pending_post', context),
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
        
        if success:
            title = self.get_text('post_successful', context)
        else:
            title = self.get_text('post_failed', context)
        
        text = f"{title}\n\n{message}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def edit_post_text(self, query, context):
        """Allow user to edit post text before posting."""
        context.user_data['editing_post'] = True
        text = f"{self.get_text('edit_post_title', context)}\n\n{self.get_text('edit_post_instructions', context)}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def cancel_post(self, query, context):
        """Cancel the pending post."""
        if 'pending_post' in context.user_data:
            del context.user_data['pending_post']
        
        text = f"{self.get_text('post_cancelled_title', context)}\n\n{self.get_text('post_cancelled_message', context)}"
        
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
                self.get_text('no_pending_post', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
        return True

    async def initiate_channel_post_from_edit(self, update, context):
        """Show post confirmation after editing."""
        pending_post = context.user_data.get('pending_post', {})
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id', 'Unknown')
        
        # Check if text already has hashtags for preview
        has_hashtags = '#' in pending_post['text']
        if has_hashtags:
            preview_text = pending_post['text']
        else:
            hashtags = self.generate_hashtags(pending_post['product'], context)
            preview_text = f"{pending_post['text']}\n\n{hashtags}"
        
        text = f"{self.get_text('confirm_edited_post_title', context)}\n\nChannel: @{channel_id}\nProduct: {pending_post['product']}\n\n**Preview:**\n{preview_text[:200]}{'...' if len(preview_text) > 200 else ''}"
        
        await update.message.reply_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_post_confirmation_keyboard(context)
        )

    async def translate_generated_text(self, query, context):
        """Show language options for translating the generated text."""
        stored_text = context.user_data.get('last_generated_text', '')
        
        if not stored_text:
            await query.edit_message_text(
                self.get_text('no_promo_text', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        # Create translation keyboard
        keyboard = [
            [InlineKeyboardButton(self.get_text('translate_to_english', context), callback_data='translate_en'),
             InlineKeyboardButton(self.get_text('translate_to_russian', context), callback_data='translate_ru')],
            [InlineKeyboardButton(self.get_text('translate_to_romanian', context), callback_data='translate_ro')],
            [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
        ]
        
        text = f"{self.get_text('translate_to_title', context)}\n\n{self.get_text('translate_to_subtitle', context)}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def edit_generated_text(self, query, context):
        """Allow user to edit the generated text."""
        stored_text = context.user_data.get('last_generated_text', '')
        
        if not stored_text:
            await query.edit_message_text(
                self.get_text('no_promo_text', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        context.user_data['editing_generated_text'] = True
        text = f"{self.get_text('edit_generated_title', context)}\n\n{self.get_text('edit_generated_instructions', context)}\n\n**Current text:**\n{stored_text}"
        
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def perform_translation(self, query, context, target_lang):
        """Translate the generated text to the target language."""
        stored_text = context.user_data.get('last_generated_text', '')
        product_name = context.user_data.get('last_product_name', '')
        
        if not stored_text:
            await query.edit_message_text(
                self.get_text('no_promo_text', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        # Show typing action
        await context.bot.send_chat_action(chat_id=query.message.chat.id, action='typing')
        
        try:
            # Create translation prompt
            lang_names = {'en': 'English', 'ru': 'Russian', 'ro': 'Romanian'}
            target_language = lang_names.get(target_lang, 'English')
            
            translation_prompt = f"Translate the following promotional text to {target_language}. Keep the same tone, style, and marketing appeal. Maintain any emojis and formatting:\n\n{stored_text}"
            
            # Generate translation using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a professional translator specializing in marketing content. Translate accurately while maintaining the promotional tone and appeal."},
                    {"role": "user", "content": translation_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )

            translated_text = response.choices[0].message.content.strip()
            
            # Store the translated text
            context.user_data['last_generated_text'] = translated_text
            
            # Format the response
            formatted_response = f"""
🌍 **Translated to {target_language}**

{self.get_text('promo_result', context, product_name)}

{translated_text}

---
{self.get_text('promo_footer', context)}
            """

            await query.edit_message_text(
                formatted_response, 
                parse_mode='Markdown',
                reply_markup=self.get_post_generation_keyboard(context)
            )
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            await query.edit_message_text(
                self.get_text('general_error', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )

    async def handle_generated_text_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle editing of generated promotional text."""
        if not context.user_data.get('editing_generated_text'):
            return False
        
        edited_text = update.message.text.strip()
        context.user_data['editing_generated_text'] = False
        
        # Update the stored generated text
        context.user_data['last_generated_text'] = edited_text
        product_name = context.user_data.get('last_product_name', '')
        
        # Format the response
        formatted_response = f"""
{self.get_text('promo_result', context, product_name)}

{edited_text}

---
{self.get_text('promo_footer', context)}
        """

        await update.message.reply_text(
            formatted_response, 
            parse_mode='Markdown',
            reply_markup=self.get_post_generation_keyboard(context)
        )
        return True

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