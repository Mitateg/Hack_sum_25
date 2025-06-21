# Language translations for the Telegram Promo Bot
# Separated for better organization and security

TRANSLATIONS = {
    'en': {
        'welcome_title': '🚀 Welcome to the Promo Text Generator Bot! 🚀',
        'welcome_message': 'I can help you create amazing promotional posts for your products!\n\nChoose your language first:',
        'language_selected': '✅ Language set to English!\n\nChoose an option below to get started:',
        'main_menu_title': '🚀 Promo Text Generator Bot - Main Menu',
        'main_menu_subtitle': 'Choose an option below to get started:',
        
        # Menu buttons
        'generate_promo': '✨ Generate Promo',
        'my_products': '📦 My Products', 
        'channel_settings': '📢 Channel Settings',
        'help': '❓ Help',
        'examples': '💡 Examples',
        'language': '🌐 Language',
        'stop_bot': '🛑 Stop Bot',
        'back_menu': '🔙 Back to Menu',
        'back_to_products': '🔙 Back to Products',
        
        # Product management
        'add_product': '➕ Add Product',
        'clear_all': '🗑️ Clear All',
        'delete_product': '🗑️ Delete',
        'open_link': '🔗 Open Link',
        'generate_another_btn': '🔄 Generate Another',
        'translate_btn': '🌐 Translate',
        'edit_text_btn': '✏️ Edit Text',
        'main_menu_btn': '🏠 Main Menu',
        'post_to_channel_btn': '📤 Post to Channel',
        'post_now_btn': '✅ Post Now',
        'edit_post_btn': '✏️ Edit Post',
        'cancel_btn': '❌ Cancel',
        
        # Product messages
        'my_products_title': '📦 My Products',
        'no_products_yet': 'You haven\'t added any products yet.\n\nClick "Add Product" to get started!',
        'my_products_count': 'You have {} product(s) saved:\n\n',
        'product_not_found': '❌ Product not found.',
        'product_details_title': '📦 Product Details',
        'product_details_question': 'What would you like to do with this product?',
        'product_limit_title': '⚠️ Product Limit Reached',
        'product_limit_message': 'You can store up to 5 products. Please delete some products first.',
        'add_product_title': '➕ Add Product ({}/5)',
        'add_product_instructions': 'Please send me a product link from any online store.\n\nI\'ll automatically extract the product information for you!',
        'no_products_to_clear': '❌ No products to clear.',
        'products_cleared': '✅ All {} products have been cleared.',
        'product_deleted_title': '✅ Product Deleted',
        'product_deleted_message': 'Product "{}" has been deleted successfully.',
        
        # Product fields
        'name_label': 'Name',
        'price_label': 'Price', 
        'brand_label': 'Brand',
        'category_label': 'Category',
        'features_label': 'Features',
        
        # Product link handling
        'invalid_url': '❌ Please send a valid product URL starting with http:// or https://',
        'analyzing_product': '🔄 Analyzing product information...',
        'extraction_failed': '❌ Failed to extract product information: {}',
        'product_added_title': '✅ Product Added Successfully!',
        'product_added_message': 'Product has been added to your collection.\n\nYou now have {} product(s) saved.',
        
        # Promo generation
        'promo_choice_title': '✨ Generate Promotional Text',
        'promo_choice_subtitle': 'You have {} saved product(s). Choose how to generate:',
        'no_products_available': 'You don\'t have any saved products yet.\n\nYou can generate promotional text from a description.',
        'from_my_products': '📦 From My Products',
        'from_prompt': '✏️ From Description',
        'generate_title': '✨ Generate Promotional Text',
        'generate_instructions': 'Please describe your product or service, and I\'ll create an engaging promotional text for you!\n\nExample: "Wireless headphones with noise cancellation"',
        'empty_product': '❌ Please provide a product description.',
        'promo_result': '✨ Promotional text for "{}":\n\n{}',
        'promo_footer': '💡 You can generate another version, translate to other languages, or edit the text above.',
        'general_error': '❌ An error occurred. Please try again.',
        
        # Channel settings
        'channel_configured': 'Configured channel: @{}\nAuto-post: {}',
        'channel_not_configured': 'No channel configured yet. Add a channel to automatically post promotional content!',
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
        'add_channel_title': '📢 Add Channel/Group',
        'add_channel_instructions': 'Please send me the channel/group name (with @) or ID.\n\nExample: @mychannel\n\nNote: The bot must be added as admin with posting permissions.',
        'channel_removed_title': '✅ Channel Removed',
        'channel_removed_message': 'Channel configuration has been removed.',
        'autopost_enabled_title': '🤖 Auto-post Enabled',
        'autopost_disabled_title': '🤖 Auto-post Disabled',
        'autopost_enabled_message': 'Auto-posting is now enabled.',
        'autopost_disabled_message': 'Auto-posting is now disabled.',
        'post_history_title': '📊 Post History',
        'post_history_empty': 'No posts yet. Generate promotional content and post to your channel!',
        'channel_added_title': '✅ Channel Added Successfully',
        'channel_added_message': 'Channel @{} has been configured!',
        'channel_setup_failed_title': '❌ Channel Setup Failed',
        'channel_setup_failed_message': 'Please ensure the bot is added as admin with posting permissions.',
        'no_channel_configured': 'No channel configured',
        'posted_successfully': 'Successfully posted to {}',
        'failed_to_post': 'Failed to post: {}',
        
        # Post confirmation
        'confirm_post_title': '📤 Confirm Channel Post',
        'confirm_post_message': 'Channel: @{}\nProduct: {}\n\nPreview:\n{}',
        'no_pending_post': '❌ No pending post found.',
        'post_successful': '✅ Post Successful',
        'post_failed': '❌ Post Failed',
        'edit_post_title': '✏️ Edit Post Text',
        'edit_post_instructions': 'Send me the edited version of the promotional text.',
        'post_cancelled_title': '❌ Post Cancelled',
        'post_cancelled_message': 'The post has been cancelled.',
        
        # OpenAI prompts
        'openai_prompt': 'Create an engaging promotional text for: {}. Make it persuasive and marketing-focused.',
        'system_prompt': 'You are a professional marketing copywriter. Create compelling promotional content.',
        
        # Help content
        'help_content': '❓ How to use this bot:\n\n1. 📦 Add Products - Send product links to save them\n2. ✨ Generate Promos - Create promotional texts\n3. 🌐 Multiple Languages - Available in English, Russian, Romanian\n4. 📢 Channel Integration - Post directly to your channels\n\nNeed more help? Contact support!',
        
        # Examples
        'examples_title': '💡 Examples',
        'examples_content': 'Example 1: "Wireless Bluetooth headphones with active noise cancellation"\n\nExample 2: "Organic skincare cream with natural ingredients"\n\nExample 3: "Gaming laptop with RTX graphics card"\n\nJust describe your product and I\'ll create amazing promotional text!',
        
        # Language selection
        'language_title': '🌐 Language Selection',
        'language_subtitle': 'Choose your preferred language:',
        
        # Stop functionality
        'confirm_stop_title': '🛑 Stop Bot',
        'confirm_stop_message': 'Are you sure you want to stop the bot?\n\nThis will clear your session data.',
        'confirm_stop_btn': '✅ Yes, Stop',
        'cancel_stop_btn': '❌ Cancel',
        'bot_stopped_title': '🛑 Bot Stopped',
        'bot_stopped_message': 'The bot has been stopped. Your session data has been cleared.\n\nSend /start to begin again.',
        
        # Translation and editing
        'translate_to_title': '🌐 Translate Text',
        'translate_to_subtitle': 'Choose target language:',
        'translate_to_english': '🇺🇸 English',
        'translate_to_russian': '🇷🇺 Russian',
        'translate_to_romanian': '🇷🇴 Romanian',
        'edit_generated_title': '✏️ Edit Generated Text',
        'edit_generated_instructions': 'Send me the edited version of the promotional text:',
        
        # Error messages
        'rate_limit': '⚠️ Rate limit exceeded. Please try again in a moment.',
        'request_error': '❌ There was a problem with the request. Please try again.',
        'no_promo_text': '❌ Promotional text not found. Please generate text first.',
    },
    
    'ru': {
        'welcome_title': '🚀 Добро пожаловать в бот генератора промо-текстов! 🚀',
        'welcome_message': 'Я помогу вам создать потрясающие рекламные посты для ваших товаров!\n\nСначала выберите язык:',
        'language_selected': '✅ Язык установлен на русский!\n\nВыберите опцию ниже, чтобы начать:',
        'main_menu_title': '🚀 Бот генератора промо-текстов - Главное меню',
        'main_menu_subtitle': 'Выберите опцию ниже, чтобы начать:',
        
        # Menu buttons
        'generate_promo': '✨ Создать промо',
        'my_products': '📦 Мои товары',
        'channel_settings': '📢 Настройки канала',
        'help': '❓ Помощь',
        'examples': '💡 Примеры',
        'language': '🌐 Язык',
        'stop_bot': '🛑 Остановить бота',
        'back_menu': '🔙 В главное меню',
        'back_to_products': '🔙 К товарам',
        
        # Product management
        'add_product': '➕ Добавить товар',
        'clear_all': '🗑️ Очистить все',
        'delete_product': '🗑️ Удалить',
        'open_link': '🔗 Открыть ссылку',
        'generate_another_btn': '🔄 Создать еще',
        'translate_btn': '🌐 Перевести',
        'edit_text_btn': '✏️ Редактировать',
        'main_menu_btn': '🏠 Главное меню',
        'post_to_channel_btn': '📤 Опубликовать в канал',
        'post_now_btn': '✅ Опубликовать',
        'edit_post_btn': '✏️ Редактировать пост',
        'cancel_btn': '❌ Отменить',
        
        # Product messages
        'my_products_title': '📦 Мои товары',
        'no_products_yet': 'Вы еще не добавили товары.\n\nНажмите "Добавить товар" чтобы начать!',
        'my_products_count': 'У вас сохранено {} товар(ов):\n\n',
        'product_not_found': '❌ Товар не найден.',
        'product_details_title': '📦 Детали товара',
        'product_details_question': 'Что вы хотите сделать с этим товаром?',
        'product_limit_title': '⚠️ Достигнут лимит товаров',
        'product_limit_message': 'Вы можете сохранить до 5 товаров. Сначала удалите некоторые товары.',
        'add_product_title': '➕ Добавить товар ({}/5)',
        'add_product_instructions': 'Пожалуйста, отправьте мне ссылку на товар из любого интернет-магазина.\n\nЯ автоматически извлеку информацию о товаре!',
        'no_products_to_clear': '❌ Нет товаров для очистки.',
        'products_cleared': '✅ Все {} товаров очищены.',
        'product_deleted_title': '✅ Товар удален',
        'product_deleted_message': 'Товар "{}" успешно удален.',
        
        # Product fields
        'name_label': 'Название',
        'price_label': 'Цена',
        'brand_label': 'Бренд',
        'category_label': 'Категория',
        'features_label': 'Особенности',
        
        # Product link handling
        'invalid_url': '❌ Пожалуйста, отправьте действительную ссылку на товар, начинающуюся с http:// или https://',
        'analyzing_product': '🔄 Анализирую информацию о товаре...',
        'extraction_failed': '❌ Не удалось извлечь информацию о товаре: {}',
        'product_added_title': '✅ Товар успешно добавлен!',
        'product_added_message': 'Товар добавлен в вашу коллекцию.\n\nТеперь у вас {} сохраненных товаров.',
        
        # Promo generation
        'promo_choice_title': '✨ Создать рекламный текст',
        'promo_choice_subtitle': 'У вас {} сохраненных товаров. Выберите способ создания:',
        'no_products_available': 'У вас пока нет сохраненных товаров.\n\nВы можете создать рекламный текст из описания.',
        'from_my_products': '📦 Из моих товаров',
        'from_prompt': '✏️ Из описания',
        'generate_title': '✨ Создать рекламный текст',
        'generate_instructions': 'Пожалуйста, опишите ваш товар или услугу, и я создам привлекательный рекламный текст!\n\nПример: "Беспроводные наушники с шумоподавлением"',
        'empty_product': '❌ Пожалуйста, предоставьте описание товара.',
        'promo_result': '✨ Рекламный текст для "{}":\n\n{}',
        'promo_footer': '💡 Вы можете создать другую версию, перевести на другие языки или отредактировать текст выше.',
        'general_error': '❌ Произошла ошибка. Пожалуйста, попробуйте снова.',
        
        # Channel settings
        'channel_configured': 'Настроенный канал: @{}\nАвто-публикация: {}',
        'channel_not_configured': 'Канал еще не настроен. Добавьте канал для автоматической публикации рекламного контента!',
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
        'add_channel_title': '📢 Добавить канал/группу',
        'add_channel_instructions': 'Пожалуйста, отправьте мне имя канала/группы (с @) или ID.\n\nПример: @mychannel\n\nПримечание: Бот должен быть добавлен как администратор с правами публикации.',
        'channel_removed_title': '✅ Канал удален',
        'channel_removed_message': 'Конфигурация канала была удалена.',
        'autopost_enabled_title': '🤖 Авто-публикация включена',
        'autopost_disabled_title': '🤖 Авто-публикация отключена',
        'autopost_enabled_message': 'Авто-публикация теперь включена.',
        'autopost_disabled_message': 'Авто-публикация теперь отключена.',
        'post_history_title': '📊 История публикаций',
        'post_history_empty': 'Публикаций пока нет. Создайте рекламный контент и опубликуйте его в канале!',
        'channel_added_title': '✅ Канал успешно добавлен',
        'channel_added_message': 'Канал @{} настроен!',
        'channel_setup_failed_title': '❌ Настройка канала не удалась',
        'channel_setup_failed_message': 'Пожалуйста, убедитесь что бот добавлен как администратор с правами публикации.',
        'no_channel_configured': 'Канал не настроен',
        'posted_successfully': 'Успешно опубликовано в {}',
        'failed_to_post': 'Не удалось опубликовать: {}',
        
        # Post confirmation
        'confirm_post_title': '📤 Подтвердить публикацию в канале',
        'confirm_post_message': 'Канал: @{}\nТовар: {}\n\nПредпросмотр:\n{}',
        'no_pending_post': '❌ Ожидающая публикация не найдена.',
        'post_successful': '✅ Публикация успешна',
        'post_failed': '❌ Публикация не удалась',
        'edit_post_title': '✏️ Редактировать текст поста',
        'edit_post_instructions': 'Отправьте мне отредактированную версию рекламного текста.',
        'post_cancelled_title': '❌ Публикация отменена',
        'post_cancelled_message': 'Публикация была отменена.',
        
        # OpenAI prompts
        'openai_prompt': 'Создай привлекательный рекламный текст для: {}. Сделай его убедительным и маркетинговым.',
        'system_prompt': 'Ты профессиональный маркетинговый копирайтер. Создавай убедительный рекламный контент.',
        
        # Help content
        'help_content': '❓ Как использовать этого бота:\n\n1. 📦 Добавить товары - Отправляйте ссылки на товары для сохранения\n2. ✨ Создать промо - Создавайте рекламные тексты\n3. 🌐 Несколько языков - Доступен на английском, русском, румынском\n4. 📢 Интеграция каналов - Публикуйте прямо в ваши каналы\n\nНужна помощь? Обратитесь в поддержку!',
        
        # Examples
        'examples_title': '💡 Примеры',
        'examples_content': 'Пример 1: "Беспроводные Bluetooth наушники с активным шумоподавлением"\n\nПример 2: "Органический крем для кожи с натуральными ингредиентами"\n\nПример 3: "Игровой ноутбук с видеокартой RTX"\n\nПросто опишите ваш товар, и я создам потрясающий рекламный текст!',
        
        # Language selection
        'language_title': '🌐 Выбор языка',
        'language_subtitle': 'Выберите предпочитаемый язык:',
        
        # Stop functionality
        'confirm_stop_title': '🛑 Остановить бота',
        'confirm_stop_message': 'Вы уверены, что хотите остановить бота?\n\nЭто очистит данные вашей сессии.',
        'confirm_stop_btn': '✅ Да, остановить',
        'cancel_stop_btn': '❌ Отмена',
        'bot_stopped_title': '🛑 Бот остановлен',
        'bot_stopped_message': 'Бот остановлен. Данные вашей сессии очищены.\n\nОтправьте /start чтобы начать снова.',
        
        # Translation and editing
        'translate_to_title': '🌐 Перевести текст',
        'translate_to_subtitle': 'Выберите язык для перевода:',
        'translate_to_english': '🇺🇸 Английский',
        'translate_to_russian': '🇷🇺 Русский',
        'translate_to_romanian': '🇷🇴 Румынский',
        'edit_generated_title': '✏️ Редактировать сгенерированный текст',
        'edit_generated_instructions': 'Trimite-mi versiunea editată a textului promoțional:',
        
        # Error messages
        'rate_limit': '⚠️ Превышен лимит запросов. Попробуйте еще раз через момент.',
        'request_error': '❌ Возникла проблема с запросом. Попробуйте еще раз.',
        'no_promo_text': '❌ Рекламный текст не найден. Сначала создайте текст.',
    },
    
    'ro': {
        'welcome_title': '🚀 Bun venit la Bot-ul Generator de Texte Promoționale! 🚀',
        'welcome_message': 'Te pot ajuta să creezi postări promoționale uimitoare pentru produsele tale!\n\nAlege mai întâi limba:',
        'language_selected': '✅ Limba setată la română!\n\nAlege o opțiune de mai jos pentru a începe:',
        'main_menu_title': '🚀 Bot Generator Texte Promoționale - Meniu Principal',
        'main_menu_subtitle': 'Alege o opțiune de mai jos pentru a începe:',
        
        # Menu buttons
        'generate_promo': '✨ Generează Promoție',
        'my_products': '📦 Produsele Mele',
        'channel_settings': '📢 Setări Canal',
        'help': '❓ Ajutor',
        'examples': '💡 Exemple',
        'language': '🌐 Limba',
        'stop_bot': '🛑 Oprește Bot-ul',
        'back_menu': '🔙 Înapoi la Meniu',
        'back_to_products': '🔙 Înapoi la Produse',
        
        # Product management
        'add_product': '➕ Adaugă Produs',
        'clear_all': '🗑️ Șterge Tot',
        'delete_product': '🗑️ Șterge',
        'open_link': '🔗 Deschide Link',
        'generate_another_btn': '🔄 Generează Alt',
        'translate_btn': '🌐 Traduce',
        'edit_text_btn': '✏️ Editează Text',
        'main_menu_btn': '🏠 Meniu Principal',
        'post_to_channel_btn': '📤 Postează în Canal',
        'post_now_btn': '✅ Postează Acum',
        'edit_post_btn': '✏️ Editează Post',
        'cancel_btn': '❌ Anulează',
        
        # Product messages
        'my_products_title': '📦 Produsele Mele',
        'no_products_yet': 'Nu ai adăugat încă produse.\n\nApasă "Adaugă Produs" pentru a începe!',
        'my_products_count': 'Ai {} produs(e) salvat(e):\n\n',
        'product_not_found': '❌ Produsul nu a fost găsit.',
        'product_details_title': '📦 Detalii Produs',
        'product_details_question': 'Ce vrei să faci cu acest produs?',
        'product_limit_title': '⚠️ Limita de Produse Atinsă',
        'product_limit_message': 'Poți stoca până la 5 produse. Te rog șterge mai întâi câteva produse.',
        'add_product_title': '➕ Adaugă Produs ({}/5)',
        'add_product_instructions': 'Te rog trimite-mi un link de produs din orice magazin online.\n\nVoi extrage automat informațiile despre produs!',
        'no_products_to_clear': '❌ Niciun produs de șters.',
        'products_cleared': '✅ Toate {} produsele au fost șterse.',
        'product_deleted_title': '✅ Produs Șters',
        'product_deleted_message': 'Produsul "{}" a fost șters cu succes.',
        
        # Product fields
        'name_label': 'Nume',
        'price_label': 'Preț',
        'brand_label': 'Marcă',
        'category_label': 'Categorie',
        'features_label': 'Caracteristici',
        
        # Product link handling
        'invalid_url': '❌ Te rog trimite un URL valid de produs care începe cu http:// sau https://',
        'analyzing_product': '🔄 Analizez informațiile produsului...',
        'extraction_failed': '❌ Eșec în extragerea informațiilor produsului: {}',
        'product_added_title': '✅ Produs Adăugat cu Succes!',
        'product_added_message': 'Produsul a fost adăugat în colecția ta.\n\nAcum ai {} produs(e) salvat(e).',
        
        # Promo generation
        'promo_choice_title': '✨ Generează Text Promoțional',
        'promo_choice_subtitle': 'Ai {} produs(e) salvat(e). Alege cum să generezi:',
        'no_products_available': 'Nu ai încă produse salvate.\n\nPoți genera text promoțional dintr-o descriere.',
        'from_my_products': '📦 Din Produsele Mele',
        'from_prompt': '✏️ Din Descriere',
        'generate_title': '✨ Generează Text Promoțional',
        'generate_instructions': 'Te rog descrie produsul sau serviciul tău, și voi crea un text promoțional atractiv!\n\nExemplu: "Căști wireless cu anularea zgomotului"',
        'empty_product': '❌ Te rog furnizează o descriere a produsului.',
        'promo_result': '✨ Text promoțional pentru "{}":\n\n{}',
        'promo_footer': '💡 Poți genera o altă versiune, traduce în alte limbi sau edita textul de mai sus.',
        'general_error': '❌ A apărut o eroare. Te rog încearcă din nou.',
        
        # Channel settings
        'channel_configured': 'Canal configurat: @{}\nPostare automată: {}',
        'channel_not_configured': 'Niciun canal configurat încă. Adaugă un canal pentru a posta automat conținutul promoțional!',
        'auto_enabled': '✅ Activat',
        'auto_disabled': '❌ Dezactivat',
        'current_channel': '📋 Curent: {}',
        'change_channel': '✏️ Schimbă Canal',
        'remove_channel': '❌ Elimină Canal',
        'auto_post_on': '✅ PORNIT',
        'auto_post_off': '❌ OPRIT',
        'auto_post_toggle': '🤖 Postare automată: {}',
        'post_history': '📊 Istoric Postări',
        'add_channel_group': '➕ Adaugă Canal/Grup',
        'add_channel_title': '📢 Adaugă Canal/Grup',
        'add_channel_instructions': 'Te rog trimite-mi numele canalului/grupului (cu @) sau ID-ul.\n\nExemplu: @mychannel\n\nNotă: Bot-ul trebuie să fie adăugat ca administrator cu permisiuni de postare.',
        'channel_removed_title': '✅ Canal Eliminat',
        'channel_removed_message': 'Configurația canalului a fost eliminată.',
        'autopost_enabled_title': '🤖 Postare Automată Activată',
        'autopost_disabled_title': '🤖 Postare Automată Dezactivată',
        'autopost_enabled_message': 'Postarea automată este acum activată.',
        'autopost_disabled_message': 'Postarea automată este acum dezactivată.',
        'post_history_title': '📊 Istoric Postări',
        'post_history_empty': 'Nu sunt postări încă. Generează conținut promoțional și postează în canalul tău!',
        'channel_added_title': '✅ Canal Adăugat cu Succes',
        'channel_added_message': 'Canalul @{} a fost configurat!',
        'channel_setup_failed_title': '❌ Configurarea Canalului a Eșuat',
        'channel_setup_failed_message': 'Te rog asigură-te că bot-ul este adăugat ca administrator cu permisiuni de postare.',
        'no_channel_configured': 'Niciun canal configurat',
        'posted_successfully': 'Postat cu succes în {}',
        'failed_to_post': 'Postarea a eșuat: {}',
        
        # Post confirmation
        'confirm_post_title': '📤 Confirmă Postarea în Canal',
        'confirm_post_message': 'Canal: @{}\nProdus: {}\n\nPrevizualizare:\n{}',
        'no_pending_post': '❌ Nu există postare în așteptare.',
        'post_successful': '✅ Postare Reușită',
        'post_failed': '❌ Postarea a Eșuat',
        'edit_post_title': '✏️ Editează Textul Postării',
        'edit_post_instructions': 'Trimite-mi versiunea editată a textului promoțional.',
        'post_cancelled_title': '❌ Postare Anulată',
        'post_cancelled_message': 'Postarea a fost anulată.',
        
        # OpenAI prompts
        'openai_prompt': 'Creează un text promoțional atractiv pentru: {}. Fă-l persuasiv și orientat spre marketing.',
        'system_prompt': 'Ești un copywriter marketing profesionist. Creează conținut promoțional convingător.',
        
        # Help content
        'help_content': '❓ Cum să folosești acest bot:\n\n1. 📦 Adaugă Produse - Trimite linkuri de produse pentru a le salva\n2. ✨ Generează Promoții - Creează texte promoționale\n3. 🌐 Limbi Multiple - Disponibil în engleză, rusă, română\n4. 📢 Integrare Canal - Postează direct în canalele tale\n\nAi nevoie de ajutor? Contactează suportul!',
        
        # Examples
        'examples_title': '💡 Exemple',
        'examples_content': 'Exemplul 1: "Căști Bluetooth wireless cu anularea activă a zgomotului"\n\nExemplul 2: "Cremă organică pentru îngrijirea pielii cu ingrediente naturale"\n\nExemplul 3: "Laptop de gaming cu placă grafică RTX"\n\nDescrie-ți produsul și voi crea un text promoțional minunat!',
        
        # Language selection
        'language_title': '🌐 Selecția Limbii',
        'language_subtitle': 'Alege limba preferată:',
        
        # Stop functionality
        'confirm_stop_title': '🛑 Oprește Bot-ul',
        'confirm_stop_message': 'Ești sigur că vrei să oprești bot-ul?\n\nAceasta va șterge datele sesiunii tale.',
        'confirm_stop_btn': '✅ Da, Oprește',
        'cancel_stop_btn': '❌ Anulează',
        'bot_stopped_title': '🛑 Bot Oprit',
        'bot_stopped_message': 'Bot-ul a fost oprit. Datele sesiunii tale au fost șterse.\n\nTrimite /start pentru a începe din nou.',
        
        # Translation and editing
        'translate_to_title': '🌐 Traduce Textul',
        'translate_to_subtitle': 'Alege limba țintă:',
        'translate_to_english': '🇺🇸 Engleză',
        'translate_to_russian': '🇷🇺 Rusă',
        'translate_to_romanian': '🇷🇴 Română',
        'edit_generated_title': '✏️ Editează Textul Generat',
        'edit_generated_instructions': 'Trimite-mi versiunea editată a textului promoțional:',
        
        # Error messages
        'rate_limit': '⚠️ Limita de cereri depășită. Te rog să încerci din nou într-un moment.',
        'request_error': '❌ A fost o problemă cu cererea. Te rog să încerci din nou.',
        'no_promo_text': '❌ Text promoțional nu a fost găsit. Te rog generează textul mai întâi.',
    }
}

def get_text(key: str, language: str, *args) -> str:
    """
    Safely get translated text with input validation.
    
    Args:
        key: Translation key
        language: Language code (en, ru, ro)
        *args: Format arguments
        
    Returns:
        Translated text or fallback to English
    """
    # Input validation for security
    if not isinstance(key, str) or not isinstance(language, str):
        language = 'en'
        key = 'general_error'
    
    # Sanitize language code
    language = language.lower().strip()
    if language not in TRANSLATIONS:
        language = 'en'
    
    # Get translation with fallback
    text = TRANSLATIONS[language].get(key, TRANSLATIONS['en'].get(key, f"Missing translation: {key}"))
    
    # Safe string formatting
    if args:
        try:
            return text.format(*args)
        except (ValueError, IndexError, KeyError):
            return text
    
    return text 