"""
Main bot class for the Telegram Promo Text Generator Bot
Uses modular architecture with secure components
"""

import logging
import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import config
from translations import get_text
from storage import storage
from utils import rate_limit, sanitize_input, scraper

# Configure OpenAI
openai.api_key = config.openai_api_key

logger = logging.getLogger(__name__)

class PromoBot:
    """Main bot class with modular architecture."""
    
    def __init__(self):
        self.application = Application.builder().token(config.telegram_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all bot handlers."""
        # Commands
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        
        # Callbacks
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def get_user_language(self, context):
        """Get user's selected language, default to English."""
        return context.user_data.get('language', 'en')
    
    def get_text(self, key, context, *args):
        """Get translated text for user's language."""
        lang = self.get_user_language(context)
        return get_text(key, lang, *args)
    
    def get_language_selection_keyboard(self):
        """Create language selection keyboard."""
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
            [InlineKeyboardButton(self.get_text('channel_settings', context), callback_data='channel_settings'),
             InlineKeyboardButton(self.get_text('help', context), callback_data='help')],
            [InlineKeyboardButton(self.get_text('examples', context), callback_data='examples'),
             InlineKeyboardButton(self.get_text('language', context), callback_data='language_select')],
            [InlineKeyboardButton(self.get_text('stop_bot', context), callback_data='confirm_stop')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_my_products_keyboard(self, context):
        """Create my products keyboard."""
        user_data = context.user_data
        products = user_data.get('products', [])
        
        keyboard = []
        
        # Product buttons (max 5)
        for i, product in enumerate(products[:5]):
            keyboard.append([InlineKeyboardButton(f"📦 {product.get('name', 'Product')[:30]}", callback_data=f'product_{i}')])
        
        # Action buttons
        if len(products) < 5:
            keyboard.append([InlineKeyboardButton(self.get_text('add_product', context), callback_data='add_product')])
        
        if products:
            keyboard.append([InlineKeyboardButton(self.get_text('clear_all', context), callback_data='clear_products')])
        
        keyboard.append([InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_product_detail_keyboard(self, context, product_index):
        """Create product detail keyboard."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('generate_promo', context), callback_data=f'gen_promo_{product_index}')],
            [InlineKeyboardButton(self.get_text('delete_product', context), callback_data=f'delete_product_{product_index}'),
             InlineKeyboardButton(self.get_text('open_link', context), callback_data=f'open_link_{product_index}')],
            [InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_promo_generation_keyboard(self, context):
        """Create promo generation keyboard."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('generate_another_btn', context), callback_data='generate_another')],
            [InlineKeyboardButton(self.get_text('translate_btn', context), callback_data='translate_text'),
             InlineKeyboardButton(self.get_text('edit_text_btn', context), callback_data='edit_generated')],
            [InlineKeyboardButton(self.get_text('main_menu_btn', context), callback_data='main_menu')]
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

    def is_valid_url(self, url):
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    @rate_limit(max_calls=config.rate_limit_requests, window=config.rate_limit_window)
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start command handler."""
        user_id = update.effective_user.id
        
        # Update statistics
        storage.update_stats('total_users')
        storage.update_stats('total_messages')
        
        # Get user data
        user_data = storage.get_user_data(user_id)
        context.user_data.update(user_data)
        
        # Show language selection if not set
        if not context.user_data.get('language'):
            await update.message.reply_text(
                get_text('welcome_message', 'en'),
                reply_markup=self.get_language_selection_keyboard()
            )
        else:
            await self.show_main_menu_message(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Help command handler."""
        storage.update_stats('total_messages')
        
        await update.message.reply_text(
            self.get_text('help_content', context)
        )
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Stop command handler."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('confirm_stop_btn', context), callback_data='stop_bot'),
             InlineKeyboardButton(self.get_text('cancel_stop_btn', context), callback_data='main_menu')]
        ]
        
        await update.message.reply_text(
            self.get_text('confirm_stop_message', context),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        storage.update_stats('total_messages')
        
        # Language selection
        if query.data.startswith('lang_'):
            lang = query.data.split('_')[1]
            context.user_data['language'] = lang
            
            # Save user data
            user_id = query.from_user.id
            storage.save_user_data(user_id, context.user_data)
            
            await query.edit_message_text(
                self.get_text('language_selected', context),
                reply_markup=self.get_main_menu_keyboard(context)
            )
        
        # Main menu actions
        elif query.data == 'main_menu':
            await self.show_main_menu(query, context)
        elif query.data == 'help':
            await self.show_help(query, context)
        elif query.data == 'examples':
            await self.show_examples(query, context)
        elif query.data == 'language_select':
            await self.show_language_selection(query, context)
        elif query.data == 'confirm_stop':
            await self.show_stop_confirmation(query, context)
        elif query.data == 'stop_bot':
            await self.stop_bot(query, context)
        
        # Product management
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
        
        # Promo generation
        elif query.data == 'generate_promo':
            await self.show_generate_promo(query, context)
        elif query.data == 'from_prompt':
            await self.show_promo_from_prompt(query, context)
        elif query.data == 'generate_another':
            context.user_data.pop('awaiting_promo_input', None)
            await self.show_promo_from_prompt(query, context)
        
        # Channel settings
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
        
        # Post to channel workflow
        elif query.data == 'post_to_channel':
            await self.initiate_channel_post(query, context)
        elif query.data == 'confirm_post':
            await self.confirm_channel_post(query, context)
        elif query.data == 'edit_post':
            await self.edit_post_text(query, context)
        elif query.data == 'cancel_post':
            await self.cancel_post(query, context)
        
        # Text editing and translation
        elif query.data == 'translate_text':
            await self.translate_generated_text(query, context)
        elif query.data == 'edit_generated_text':
            await self.edit_generated_text(query, context)
        elif query.data.startswith('translate_to_'):
            target_lang = query.data.split('_')[2]
            await self.perform_translation(query, context, target_lang)
        
        # Other features (placeholders for now)
        else:
            await query.edit_message_text(
                f"🚧 Feature Coming Soon\n\nThe '{query.data}' feature is being implemented.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]])
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
            prompt = self.get_text('openai_prompt', context, product_name)
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
            formatted_response = f"{self.get_text('promo_result', context, product_name)}\n\n{promo_text}\n\n---\n{self.get_text('promo_footer', context)}"

            await update.message.reply_text(
                formatted_response,
                reply_markup=self.get_post_generation_keyboard(context)
            )
            
            # Check for auto-posting
            channel_info = context.user_data.get('channel_info', {})
            if channel_info.get('auto_post', False) and channel_info.get('channel_id'):
                # Auto post to channel
                success, message = await self.post_to_channel_action(context, promo_text, product_name)
                
                # Notify user about auto-post result
                status_emoji = "✅" if success else "❌"
                auto_post_msg = f"\n\n{status_emoji} Auto-post: {message}"
                
                # Send additional message with auto-post status
                await update.message.reply_text(auto_post_msg)

        except Exception as e:
            logger.error(f"Error generating promo text: {e}")
            await update.message.reply_text(
                self.get_text('general_error', context),
                reply_markup=self.get_main_menu_keyboard(context)
            )
    
    async def handle_channel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel input when user is setting up a channel."""
        if not context.user_data.get('waiting_for_channel_input'):
            return False
        
        channel_input = update.message.text.strip()
        
        # Clear the waiting state
        context.user_data.pop('waiting_for_channel_input', None)
        
        # Validate channel format
        if not (channel_input.startswith('@') or channel_input.startswith('-') or channel_input.isdigit()):
            await update.message.reply_text(
                "❌ Invalid channel format. Please use @channelname or channel ID.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return True
        
        # Remove @ if present for verification
        channel_id = channel_input[1:] if channel_input.startswith('@') else channel_input
        
        # Verify channel permissions
        success, message = await self.verify_channel_permissions(context, channel_id)
        
        if success:
            # Store channel configuration
            context.user_data['channel_info'] = {
                'channel_id': channel_id,
                'auto_post': False
            }
            
            await update.message.reply_text(
                self.get_text('channel_added_title', context) + "\n\n" + 
                self.get_text('channel_added_message', context, channel_id),
                reply_markup=self.get_channel_settings_keyboard(context)
            )
        else:
            await update.message.reply_text(
                self.get_text('channel_setup_failed_title', context) + "\n\n" + 
                self.get_text('channel_setup_failed_message', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
        
        return True

    async def handle_post_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle post text editing."""
        if not context.user_data.get('editing_post'):
            return False
        
        # Clear editing state
        context.user_data.pop('editing_post', None)
        
        # Get the edited text
        edited_text = update.message.text.strip()
        
        if not edited_text:
            await update.message.reply_text(
                "❌ Please provide some text.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return True
        
        # Update the pending post text
        context.user_data['pending_post_text'] = edited_text
        
        # Show updated confirmation
        await self.initiate_channel_post_from_edit(update, context)
        return True

    async def handle_generated_text_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle editing of generated promotional text."""
        if not context.user_data.get('editing_generated_text'):
            return False
        
        # Clear editing state
        context.user_data.pop('editing_generated_text', None)
        
        # Get the edited text
        edited_text = update.message.text.strip()
        
        if not edited_text:
            await update.message.reply_text(
                "❌ Please provide some text.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return True
        
        # Update the stored generated text
        context.user_data['last_generated_text'] = edited_text
        
        # Show the updated text with options
        formatted_response = f"✅ Text updated!\n\n{edited_text}\n\n---\n{self.get_text('promo_footer', context)}"
        
        await update.message.reply_text(
            formatted_response,
            reply_markup=self.get_post_generation_keyboard(context)
        )
        return True

    async def handle_product_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product link input and extraction."""
        if not context.user_data.get('waiting_for_product_link'):
            return False
        
        url = update.message.text.strip()
        
        # Clear waiting state
        context.user_data.pop('waiting_for_product_link', None)
        
        # Validate URL
        if not self.is_valid_url(url):
            await update.message.reply_text(
                self.get_text('invalid_url', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return True
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            self.get_text('analyzing_product', context)
        )
        
        try:
            # Extract product information
            product_info = await self.scrape_product_info(url)
            
            if product_info:
                # Store product
                if 'products' not in context.user_data:
                    context.user_data['products'] = []
                
                context.user_data['products'].append(product_info)
                
                # Show success message
                await processing_msg.edit_text(
                    self.get_text('product_added_title', context) + "\n\n" + 
                    self.get_text('product_added_message', context, len(context.user_data['products'])),
                    reply_markup=self.get_my_products_keyboard(context)
                )
            else:
                await processing_msg.edit_text(
                    self.get_text('extraction_failed', context, "Unable to extract product information"),
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
        
        except Exception as e:
            logger.error(f"Error processing product link: {e}")
            await processing_msg.edit_text(
                self.get_text('extraction_failed', context, str(e)),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
        
        return True

    async def initiate_channel_post_from_edit(self, update, context):
        """Show confirmation dialog after editing post text."""
        channel_info = context.user_data.get('channel_info', {})
        channel_id = channel_info.get('channel_id', 'Unknown')
        product_name = context.user_data.get('last_product_name', 'Unknown')
        post_text = context.user_data.get('pending_post_text', '')
        
        # Show preview with hashtags
        hashtags = self.generate_hashtags(product_name, context)
        preview_text = post_text
        if '#' not in post_text:
            preview_text = f"{post_text}\n\n{hashtags}"
        
        confirmation_text = f"{self.get_text('confirm_post_title', context)}\n\n"
        confirmation_text += f"Channel: @{channel_id}\n"
        confirmation_text += f"Product: {product_name}\n\n"
        confirmation_text += f"Preview:\n{preview_text}"
        
        await update.message.reply_text(
            confirmation_text,
            reply_markup=self.get_post_confirmation_keyboard(context)
        )
    
    # Menu display methods
    async def show_main_menu_message(self, update, context):
        """Show main menu message."""
        menu_text = f"{self.get_text('main_menu_title', context)}\n\n{self.get_text('main_menu_subtitle', context)}"
        await update.message.reply_text(
            menu_text,
            reply_markup=self.get_main_menu_keyboard(context)
        )
    
    async def show_main_menu(self, query, context):
        """Show main menu."""
        menu_text = f"{self.get_text('main_menu_title', context)}\n\n{self.get_text('main_menu_subtitle', context)}"
        await query.edit_message_text(
            menu_text,
            reply_markup=self.get_main_menu_keyboard(context)
        )
    
    async def show_help(self, query, context):
        """Show help message."""
        back_keyboard = [[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]]
        
        await query.edit_message_text(
            self.get_text('help_content', context),
            reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
    
    async def show_examples(self, query, context):
        """Show examples."""
        back_keyboard = [[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]]
        
        examples_text = f"{self.get_text('examples_title', context)}\n\n{self.get_text('examples_content', context)}"
        await query.edit_message_text(
            examples_text,
            reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
    
    async def show_language_selection(self, query, context):
        """Show language selection."""
        language_text = f"{self.get_text('language_title', context)}\n\n{self.get_text('language_subtitle', context)}"
        await query.edit_message_text(
            language_text,
            reply_markup=self.get_language_selection_keyboard()
        )
    
    async def show_my_products(self, query, context):
        """Show my products menu."""
        products = context.user_data.get('products', [])
        
        if not products:
            products_text = f"{self.get_text('my_products_title', context)}\n\n{self.get_text('no_products_yet', context)}"
        else:
            products_text = self.get_text('my_products_count', context, len(products))
            for i, product in enumerate(products[:5]):
                products_text += f"{i+1}. {product.get('name', 'Unknown Product')}\n"
        
        await query.edit_message_text(
            products_text,
            reply_markup=self.get_my_products_keyboard(context)
        )
    
    async def show_product_detail(self, query, context, product_index):
        """Show product detail."""
        products = context.user_data.get('products', [])
        
        if product_index >= len(products):
            await query.edit_message_text(
                self.get_text('product_not_found', context),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
            return
        
        product = products[product_index]
        
        detail_text = f"{self.get_text('product_details_title', context)}\n\n"
        detail_text += f"{self.get_text('name_label', context)}: {product.get('name', 'N/A')}\n"
        detail_text += f"{self.get_text('price_label', context)}: {product.get('price', 'N/A')}\n"
        detail_text += f"{self.get_text('brand_label', context)}: {product.get('brand', 'N/A')}\n"
        detail_text += f"{self.get_text('category_label', context)}: {product.get('category', 'N/A')}\n"
        detail_text += f"\n{self.get_text('product_details_question', context)}"
        
        await query.edit_message_text(
            detail_text,
            reply_markup=self.get_product_detail_keyboard(context, product_index)
        )
    
    async def prompt_add_product(self, query, context):
        """Prompt user to add product."""
        products = context.user_data.get('products', [])
        
        if len(products) >= 5:
            await query.edit_message_text(
                f"{self.get_text('product_limit_title', context)}\n\n{self.get_text('product_limit_message', context)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
            return
        
        context.user_data['waiting_for_product_link'] = True
        
        await query.edit_message_text(
            f"{self.get_text('add_product_title', context, len(products))}\n\n{self.get_text('add_product_instructions', context)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
        )
    
    async def clear_all_products(self, query, context):
        """Clear all products."""
        products = context.user_data.get('products', [])
        
        if not products:
            await query.edit_message_text(
                self.get_text('no_products_to_clear', context),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
            return
        
        # Clear products
        context.user_data['products'] = []
        
        # Save user data
        user_id = query.from_user.id
        storage.save_user_data(user_id, context.user_data)
        
        await query.edit_message_text(
            self.get_text('products_cleared', context, len(products)),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
        )
    
    async def delete_product(self, query, context, product_index):
        """Delete a specific product."""
        products = context.user_data.get('products', [])
        
        if product_index >= len(products):
            await query.edit_message_text(
                self.get_text('product_not_found', context),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
            return
        
        product_name = products[product_index].get('name', 'Unknown Product')
        del products[product_index]
        context.user_data['products'] = products
        
        # Save user data
        user_id = query.from_user.id
        storage.save_user_data(user_id, context.user_data)
        
        await query.edit_message_text(
            f"{self.get_text('product_deleted_title', context)}\n\n{self.get_text('product_deleted_message', context, product_name)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
        )
    
    async def generate_product_promo(self, query, context, product_index):
        """Generate promo for a specific product."""
        products = context.user_data.get('products', [])
        
        if product_index >= len(products):
            await query.edit_message_text(
                self.get_text('product_not_found', context),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
            return
        
        product = products[product_index]
        
        # Send processing message
        await query.edit_message_text("🔄 Generating promotional text...")
        
        try:
            # Create product description for AI
            product_desc = f"{product.get('name', '')} - {product.get('brand', '')} - {product.get('features', '')}"
            
            # Generate promo using OpenAI
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=self.get_text('openai_prompt', context, product_desc, product_desc),
                max_tokens=200,
                temperature=0.7
            )
            
            promo_text = response.choices[0].text.strip()
            
            # Store generated text
            context.user_data['last_generated_promo'] = promo_text
            context.user_data['last_product_name'] = product.get('name', 'Product')
            
            # Update statistics
            storage.update_stats('total_promos_generated')
            
            # Send result
            result_text = f"{self.get_text('promo_result', context, product.get('name', 'Product'))}\n\n{promo_text}\n\n{self.get_text('promo_footer', context)}"
            
            await query.edit_message_text(
                result_text,
                reply_markup=self.get_promo_generation_keyboard(context)
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            await query.edit_message_text(
                self.get_text('general_error', context),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
    
    async def show_generate_promo(self, query, context):
        """Show promo generation options."""
        products = context.user_data.get('products', [])
        
        if products:
            keyboard = [
                [InlineKeyboardButton(self.get_text('from_my_products', context), callback_data='my_products')],
                [InlineKeyboardButton(self.get_text('from_prompt', context), callback_data='from_prompt')],
                [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
            ]
            
            promo_text = f"{self.get_text('promo_choice_title', context)}\n\n{self.get_text('promo_choice_subtitle', context, len(products))}"
        else:
            keyboard = [
                [InlineKeyboardButton(self.get_text('from_prompt', context), callback_data='from_prompt')],
                [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
            ]
            
            promo_text = f"{self.get_text('promo_choice_title', context)}\n\n{self.get_text('no_products_available', context)}"
        
        await query.edit_message_text(
            promo_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_promo_from_prompt(self, query, context):
        """Show promo from prompt instructions."""
        context.user_data['awaiting_promo_input'] = True
        
        await query.edit_message_text(
            f"{self.get_text('generate_title', context)}\n\n{self.get_text('generate_instructions', context)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]])
        )
    
    async def show_stop_confirmation(self, query, context):
        """Show stop confirmation."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('confirm_stop_btn', context), callback_data='stop_bot'),
             InlineKeyboardButton(self.get_text('cancel_stop_btn', context), callback_data='main_menu')]
        ]
        
        stop_text = f"{self.get_text('confirm_stop_title', context)}\n\n{self.get_text('confirm_stop_message', context)}"
        await query.edit_message_text(
            stop_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def stop_bot(self, query, context):
        """Stop the bot for user."""
        # Clear user data
        context.user_data.clear()
        
        # Update statistics
        storage.update_stats('total_messages')
        
        stop_text = f"{self.get_text('bot_stopped_title', context)}\n\n{self.get_text('bot_stopped_message', context)}"
        await query.edit_message_text(stop_text)
    
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
            product_info = {
                'url': url,
                'name': self.extract_title(soup),
                'price': self.extract_price(soup),
                'description': self.extract_description(soup),
                'image_url': self.extract_image(soup, url),
                'brand': self.extract_brand(soup),
                'category': 'General',
                'features': self.extract_description(soup)[:200]  # Limit features
            }
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error scraping product info: {e}")
            return None

    def extract_title(self, soup):
        """Extract product title from soup."""
        # Try multiple selectors for title
        selectors = [
            'h1',
            '[data-testid="product-title"]',
            '.product-title',
            '.product-name',
            '.title',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)[:100]  # Limit length
        
        return "Unknown Product"

    def extract_price(self, soup):
        """Extract price from soup."""
        # Try multiple selectors for price
        selectors = [
            '.price',
            '.product-price',
            '[data-testid="price"]',
            '.price-current',
            '.sale-price',
            '.regular-price'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                price_text = element.get_text(strip=True)
                # Clean up price text
                import re
                price_match = re.search(r'[\d,]+\.?\d*', price_text)
                if price_match:
                    return price_match.group()
        
        return "Price not available"

    def extract_description(self, soup):
        """Extract description from soup."""
        # Try multiple selectors for description
        selectors = [
            '.product-description',
            '.description',
            '[data-testid="product-description"]',
            '.product-details',
            '.product-info'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)[:300]  # Limit length
        
        # Fallback to meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')[:300]
        
        return "No description available"

    def extract_image(self, soup, base_url):
        """Extract main product image URL."""
        # Try multiple selectors for image
        selectors = [
            '.product-image img',
            '.main-image img',
            '[data-testid="product-image"] img',
            '.hero-image img',
            'img[alt*="product"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get('src'):
                img_url = element.get('src')
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = urljoin(base_url, img_url)
                return img_url
        
        return None

    def extract_brand(self, soup):
        """Extract brand from soup."""
        # Try multiple selectors for brand
        selectors = [
            '.brand',
            '.product-brand',
            '[data-testid="brand"]',
            '.manufacturer',
            '.brand-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return "Unknown Brand"

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

    async def show_channel_settings(self, query, context):
        """Show channel settings menu."""
        channel_info = context.user_data.get('channel_info', {})
        
        if channel_info.get('channel_id'):
            auto_status = self.get_text('auto_enabled', context) if channel_info.get('auto_post', False) else self.get_text('auto_disabled', context)
            text = f"{self.get_text('channel_settings', context)}\n\n{self.get_text('channel_configured', context, channel_info['channel_id'], auto_status)}"
        else:
            text = f"{self.get_text('channel_settings', context)}\n\n{self.get_text('channel_not_configured', context)}"
        
        await query.edit_message_text(
            text,
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def prompt_channel_setup(self, query, context):
        """Prompt user to set up a channel."""
        context.user_data['waiting_for_channel_input'] = True
        
        await query.edit_message_text(
            f"{self.get_text('add_channel_title', context)}\n\n{self.get_text('add_channel_instructions', context)}",
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def remove_channel(self, query, context):
        """Remove configured channel."""
        context.user_data.pop('channel_info', None)
        
        # Save user data
        user_id = query.from_user.id
        storage.save_user_data(user_id, context.user_data)
        
        await query.edit_message_text(
            f"{self.get_text('channel_removed_title', context)}\n\n{self.get_text('channel_removed_message', context)}",
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def toggle_autopost(self, query, context):
        """Toggle autopost setting."""
        channel_info = context.user_data.get('channel_info', {})
        
        if not channel_info.get('channel_id'):
            await query.edit_message_text(
                "❌ No channel configured. Please add a channel first.",
                reply_markup=self.get_channel_settings_keyboard(context)
            )
            return
        
        # Toggle autopost
        current_autopost = channel_info.get('auto_post', False)
        channel_info['auto_post'] = not current_autopost
        context.user_data['channel_info'] = channel_info
        
        # Save user data
        user_id = query.from_user.id
        storage.save_user_data(user_id, context.user_data)
        
        # Show result
        if channel_info['auto_post']:
            title = self.get_text('autopost_enabled_title', context)
            message = self.get_text('autopost_enabled_message', context)
        else:
            title = self.get_text('autopost_disabled_title', context)
            message = self.get_text('autopost_disabled_message', context)
        
        await query.edit_message_text(
            f"{title}\n\n{message}",
            reply_markup=self.get_channel_settings_keyboard(context)
        )

    async def show_post_history(self, query, context):
        """Show post history."""
        post_history = context.user_data.get('post_history', [])
        
        if not post_history:
            text = f"{self.get_text('post_history_title', context)}\n\n{self.get_text('post_history_empty', context)}"
        else:
            text = f"{self.get_text('post_history_title', context)}\n\n"
            for i, post in enumerate(post_history[-10:], 1):  # Show last 10 posts
                status = "✅" if post['status'] == 'success' else "❌"
                text += f"{i}. {status} {post['product']} - {post['timestamp']}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='channel_settings')]])
        )

    async def initiate_channel_post(self, query, context):
        """Initiate posting to channel."""
        channel_info = context.user_data.get('channel_info', {})
        
        if not channel_info.get('channel_id'):
            await query.edit_message_text(
                "❌ No channel configured. Please set up a channel first.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        promo_text = context.user_data.get('last_generated_text')
        product_name = context.user_data.get('last_product_name', 'Unknown')
        
        if not promo_text:
            await query.edit_message_text(
                self.get_text('no_promo_text', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        # Show preview with hashtags
        hashtags = self.generate_hashtags(product_name, context)
        preview_text = promo_text
        if '#' not in promo_text:
            preview_text = f"{promo_text}\n\n{hashtags}"
        
        # Store pending post
        context.user_data['pending_post_text'] = promo_text
        
        confirmation_text = f"{self.get_text('confirm_post_title', context)}\n\n"
        confirmation_text += f"Channel: @{channel_info['channel_id']}\n"
        confirmation_text += f"Product: {product_name}\n\n"
        confirmation_text += f"Preview:\n{preview_text}"
        
        await query.edit_message_text(
            confirmation_text,
            reply_markup=self.get_post_confirmation_keyboard(context)
        )

    async def confirm_channel_post(self, query, context):
        """Confirm and execute channel post."""
        promo_text = context.user_data.get('pending_post_text') or context.user_data.get('last_generated_text')
        product_name = context.user_data.get('last_product_name', 'Unknown')
        
        if not promo_text:
            await query.edit_message_text(
                self.get_text('no_pending_post', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        # Post to channel
        success, message = await self.post_to_channel_action(context, promo_text, product_name)
        
        # Show result
        if success:
            title = self.get_text('post_successful', context)
        else:
            title = self.get_text('post_failed', context)
        
        await query.edit_message_text(
            f"{title}\n\n{message}",
            reply_markup=self.get_back_to_menu_keyboard(context)
        )
        
        # Clear pending post
        context.user_data.pop('pending_post_text', None)

    async def edit_post_text(self, query, context):
        """Edit post text before posting."""
        context.user_data['editing_post'] = True
        
        await query.edit_message_text(
            f"{self.get_text('edit_post_title', context)}\n\n{self.get_text('edit_post_instructions', context)}",
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def cancel_post(self, query, context):
        """Cancel the post."""
        context.user_data.pop('pending_post_text', None)
        
        await query.edit_message_text(
            f"{self.get_text('post_cancelled_title', context)}\n\n{self.get_text('post_cancelled_message', context)}",
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def translate_generated_text(self, query, context):
        """Show translation options."""
        keyboard = [
            [InlineKeyboardButton(self.get_text('translate_to_english', context), callback_data='translate_to_en'),
             InlineKeyboardButton(self.get_text('translate_to_russian', context), callback_data='translate_to_ru')],
            [InlineKeyboardButton(self.get_text('translate_to_romanian', context), callback_data='translate_to_ro')],
            [InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            f"{self.get_text('translate_to_title', context)}\n\n{self.get_text('translate_to_subtitle', context)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def edit_generated_text(self, query, context):
        """Edit generated text."""
        context.user_data['editing_generated_text'] = True
        
        await query.edit_message_text(
            f"{self.get_text('edit_generated_title', context)}\n\n{self.get_text('edit_generated_instructions', context)}",
            reply_markup=self.get_back_to_menu_keyboard(context)
        )

    async def perform_translation(self, query, context, target_lang):
        """Perform translation of generated text."""
        promo_text = context.user_data.get('last_generated_text')
        
        if not promo_text:
            await query.edit_message_text(
                self.get_text('no_promo_text', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
            return
        
        # Show processing message
        await query.edit_message_text("🔄 Translating text...")
        
        try:
            # Use OpenAI for translation
            target_language_names = {'en': 'English', 'ru': 'Russian', 'ro': 'Romanian'}
            target_name = target_language_names.get(target_lang, 'English')
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate the following promotional text to {target_name} while maintaining the marketing tone and persuasiveness."},
                    {"role": "user", "content": promo_text}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Update stored text
            context.user_data['last_generated_text'] = translated_text
            
            # Show result
            result_text = f"✅ Text translated to {target_name}!\n\n{translated_text}\n\n---\n{self.get_text('promo_footer', context)}"
            
            await query.edit_message_text(
                result_text,
                reply_markup=self.get_post_generation_keyboard(context)
            )
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            await query.edit_message_text(
                self.get_text('general_error', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )

    def run(self):
        """Run the bot."""
        logger.info("🤖 Bot is running...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES) 