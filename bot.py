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
from datetime import datetime

from config import config
from translations import get_text
from storage import storage
from utils import rate_limit, sanitize_input, scraper, advanced_sanitize_input, validate_url_security, generate_secure_hashtags

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
        
        keyboard.append([InlineKeyboardButton(self.get_text('back_menu', context), callback_data='generate_promo')])
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

    @rate_limit(max_calls=100, window=60, action="start_command")
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command with enhanced security."""
        try:
            user = update.effective_user
            logger.info(f"User {user.id} ({user.username}) started the bot")
            
            # Load or create user data
            user_data = storage.get_user_data(user.id)
            context.user_data.update(user_data)
            
            # Update statistics
            storage.update_stats_secure('total_users')
            storage.update_stats_secure('total_messages')
            
            # Send welcome message
            await update.message.reply_text(
                self.get_text('welcome', context, user.first_name or 'User'),
                reply_markup=self.get_main_menu_keyboard(context)
            )
            
        except Exception as e:
            logger.error(f"Error in start command for user {user.id}: {e}", exc_info=True)
            await update.message.reply_text("Sorry, an error occurred. Please try again.")

    @rate_limit(max_calls=50, window=60, action="help_command")
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command with rate limiting."""
        try:
            await update.message.reply_text(
                self.get_text('help_text', context),
                reply_markup=self.get_back_to_menu_keyboard(context)
            )
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)

    @rate_limit(max_calls=10, window=300, action="stop_command")
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stop command with confirmation."""
        try:
            await update.message.reply_text(
                self.get_text('stop_confirmation', context),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(self.get_text('stop_yes', context), callback_data='confirm_stop'),
                     InlineKeyboardButton(self.get_text('stop_no', context), callback_data='main_menu')]
                ])
            )
        except Exception as e:
            logger.error(f"Error in stop command: {e}", exc_info=True)

    @rate_limit(max_calls=100, window=60, action="button_callback")
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks with enhanced security and error handling."""
        query = update.callback_query
        user = update.effective_user
        
        try:
            await query.answer()
            
            # Simplified validation - less strict
            if not query.data:
                logger.warning(f"Empty callback data from user {user.id}")
                return
            
            # Basic sanitization only
            callback_data = query.data.strip()
            
            # Update message count
            storage.update_stats_secure('total_messages')
            
            # Load user data
            user_data = storage.get_user_data(user.id)
            context.user_data.update(user_data)
            
            # Handle different callback types
            if callback_data == 'main_menu':
                await self.show_main_menu(query, context)
            elif callback_data.startswith('lang_'):
                lang = callback_data.split('_')[1]
                if lang in ['en', 'ru', 'ro']:
                    context.user_data['language'] = lang
                    storage.save_user_data(user.id, context.user_data)
                    await self.show_main_menu(query, context)
            elif callback_data == 'language_select':
                await self.show_language_selection(query, context)
            elif callback_data == 'help':
                await self.show_help(query, context)
            elif callback_data == 'examples':
                await self.show_examples(query, context)
            elif callback_data == 'my_products':
                await self.show_my_products(query, context)
            elif callback_data.startswith('product_'):
                try:
                    product_index = int(callback_data.split('_')[1])
                    if 0 <= product_index < len(context.user_data.get('products', [])):
                        await self.show_product_detail(query, context, product_index)
                except (ValueError, IndexError):
                    pass
            elif callback_data == 'add_product':
                await self.prompt_add_product(query, context)
            elif callback_data == 'clear_products':
                await self.clear_all_products(query, context)
            elif callback_data == 'generate_promo':
                await self.show_generate_promo(query, context)
            elif callback_data == 'promo_from_prompt':
                await self.show_promo_from_prompt(query, context)
            elif callback_data == 'promo_from_product':
                await self.show_promo_from_product(query, context)
            elif callback_data.startswith('select_product_'):
                try:
                    product_index = int(callback_data.split('_')[2])
                    await self.generate_product_promo(query, context, product_index)
                except (ValueError, IndexError):
                    pass
            elif callback_data.startswith('gen_promo_'):
                try:
                    product_index = int(callback_data.split('_')[2])
                    await self.generate_product_promo(query, context, product_index)
                except (ValueError, IndexError):
                    pass
            elif callback_data.startswith('delete_product_'):
                try:
                    product_index = int(callback_data.split('_')[2])
                    await self.delete_product(query, context, product_index)
                except (ValueError, IndexError):
                    pass
            elif callback_data == 'channel_settings':
                await self.show_channel_settings(query, context)
            elif callback_data == 'set_channel':
                await self.prompt_channel_setup(query, context)
            elif callback_data == 'remove_channel':
                await self.remove_channel(query, context)
            elif callback_data == 'toggle_autopost':
                await self.toggle_autopost(query, context)
            elif callback_data == 'post_history':
                await self.show_post_history(query, context)
            elif callback_data == 'post_to_channel':
                await self.initiate_channel_post(query, context)
            elif callback_data == 'confirm_post':
                await self.confirm_channel_post(query, context)
            elif callback_data == 'edit_post':
                await self.edit_post_text(query, context)
            elif callback_data == 'cancel_post':
                await self.cancel_post(query, context)
            elif callback_data == 'translate_text':
                await self.translate_generated_text(query, context)
            elif callback_data.startswith('translate_to_'):
                lang = callback_data.split('_')[2]
                await self.perform_translation(query, context, lang)
            elif callback_data == 'edit_generated_text':
                await self.edit_generated_text(query, context)
            elif callback_data == 'generate_another':
                await self.show_generate_promo(query, context)
            elif callback_data == 'confirm_stop':
                await self.show_stop_confirmation(query, context)
            elif callback_data == 'stop_bot':
                await self.stop_bot(query, context)
            
        except Exception as e:
            logger.error(f"Error in button callback for user {user.id}: {e}", exc_info=True)
            try:
                await query.edit_message_text(
                    "An error occurred. Please try again.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
            except:
                pass

    @rate_limit(max_calls=50, window=60, action="message_handling")
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages with simplified validation."""
        user = update.effective_user
        message_text = update.message.text
        
        try:
            # Simplified validation - less strict
            if not message_text:
                await update.message.reply_text("Please send a valid message.")
                return
            
            # Basic sanitization only
            clean_text = message_text.strip()
            
            # Load user data
            user_data = storage.get_user_data(user.id)
            context.user_data.update(user_data)
            
            # Update statistics
            storage.update_stats_secure('total_messages')
            
            # Handle different message types based on user state
            if context.user_data.get('awaiting_promo_input'):
                await self.generate_promo_text(update, context)
            elif context.user_data.get('awaiting_channel_input') or context.user_data.get('waiting_for_channel_input'):
                await self.handle_channel_input(update, context)
            elif context.user_data.get('awaiting_post_edit') or context.user_data.get('editing_post'):
                await self.handle_post_edit(update, context)
            elif context.user_data.get('awaiting_generated_text_edit') or context.user_data.get('editing_generated_text'):
                await self.handle_generated_text_edit(update, context)
            elif clean_text.startswith('http') or context.user_data.get('waiting_for_product_link'):
                await self.handle_product_link(update, context)
            else:
                # Unknown message type
                await update.message.reply_text(
                    self.get_text('unknown_command', context),
                    reply_markup=self.get_main_menu_keyboard(context)
                )
                
        except Exception as e:
            logger.error(f"Error handling message from user {user.id}: {e}", exc_info=True)
            await update.message.reply_text(
                "An error occurred processing your message. Please try again.",
                reply_markup=self.get_main_menu_keyboard(context)
            )

    @rate_limit(max_calls=20, window=300, action="promo_generation")
    async def generate_promo_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate promotional text with simplified validation."""
        user = update.effective_user
        product_name = update.message.text
        
        try:
            # Simplified validation
            clean_product_name = product_name.strip()
            
            if not clean_product_name or len(clean_product_name) < 2:
                await update.message.reply_text(
                    self.get_text('invalid_product_name', context),
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                return
            
            # Clear the awaiting state
            context.user_data.pop('awaiting_promo_input', None)
            
            # Send processing message
            processing_msg = await update.message.reply_text("🔄 Generating promotional text...")
            
            try:
                # Create the prompt for OpenAI
                prompt = self.get_text('openai_prompt', context, clean_product_name, clean_product_name)
                system_prompt = self.get_text('system_prompt', context)
                
                # Generate promotional text with OpenAI
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7,
                    timeout=30
                )
                
                promo_text = response.choices[0].message.content.strip()
                
                if not promo_text:
                    raise ValueError("Generated text is empty")
                
                # Store generated text
                context.user_data['last_generated_text'] = promo_text
                context.user_data['last_product_name'] = clean_product_name
                
                # Generate hashtags
                hashtags = generate_secure_hashtags(clean_product_name)
                if hashtags:
                    promo_text += f"\n\n{hashtags}"
                
                # Update statistics
                storage.update_stats_secure('total_promos_generated')
                
                # Save user data
                storage.save_user_data(user.id, context.user_data)
                
                # Send result
                result_text = f"{self.get_text('promo_result', context, clean_product_name)}\n\n{promo_text}\n\n{self.get_text('promo_options', context)}"
                
                await processing_msg.edit_text(
                    result_text,
                    reply_markup=self.get_post_generation_keyboard(context)
                )
                
                logger.info(f"Generated promo for user {user.id}, product: {clean_product_name[:50]}")
                
            except Exception as openai_error:
                logger.error(f"OpenAI API error for user {user.id}: {openai_error}")
                await processing_msg.edit_text(
                    self.get_text('generation_error', context),
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                storage.update_stats_secure('total_errors')
                
        except Exception as e:
            logger.error(f"Error in generate_promo_text for user {user.id}: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred during text generation. Please try again.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
            except:
                pass

    async def handle_product_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product link with simplified validation."""
        user = update.effective_user
        url = update.message.text.strip()
        
        try:
            # Clear waiting state
            context.user_data.pop('waiting_for_product_link', None)
            
            # Basic URL validation - much less strict
            if not url.startswith(('http://', 'https://')):
                await update.message.reply_text(
                    "Please provide a valid URL starting with http:// or https://",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                return
            
            # Send processing message
            processing_msg = await update.message.reply_text("🔍 Analyzing product...")
            
            try:
                # Use secure scraper but with simplified error handling
                product_data, error = await scraper.scrape_product_info(url)
                
                if error:
                    await processing_msg.edit_text(
                        f"❌ {error}",
                        reply_markup=self.get_back_to_menu_keyboard(context)
                    )
                    return
                
                if not product_data or not product_data.get('title'):
                    await processing_msg.edit_text(
                        "❌ Could not extract product information from this URL. Please try a different product page.",
                        reply_markup=self.get_back_to_menu_keyboard(context)
                    )
                    return
                
                # Basic data cleaning
                clean_product = {
                    'name': product_data.get('title', 'Unknown Product')[:200],
                    'price': product_data.get('price', 'Price not available')[:100],
                    'url': url,
                    'brand': product_data.get('brand', 'Unknown Brand')[:100],
                    'description': product_data.get('description', 'No description')[:500],
                    'added_timestamp': datetime.now().isoformat()
                }
                
                # Add to user's products
                if 'products' not in context.user_data:
                    context.user_data['products'] = []
                
                # Check product limit
                if len(context.user_data['products']) >= config.max_products_per_user:
                    await processing_msg.edit_text(
                        self.get_text('max_products_reached', context, config.max_products_per_user),
                        reply_markup=self.get_back_to_menu_keyboard(context)
                    )
                    return
                
                context.user_data['products'].append(clean_product)
                
                # Save user data
                storage.save_user_data(user.id, context.user_data)
                
                # Show success message with product details
                product_info = f"📦 {self.get_text('product_added', context)}\n\n"
                product_info += f"🏷️ **{self.get_text('name_label', context)}**: {clean_product['name']}\n"
                product_info += f"💰 **{self.get_text('price_label', context)}**: {clean_product['price']}\n"
                product_info += f"🏢 **{self.get_text('brand_label', context)}**: {clean_product['brand']}\n"
                
                if clean_product.get('description') and clean_product['description'] != 'No description':
                    desc = clean_product['description'][:200] + "..." if len(clean_product['description']) > 200 else clean_product['description']
                    product_info += f"📝 **{self.get_text('description_label', context)}**: {desc}\n"
                
                await processing_msg.edit_text(
                    product_info,
                    reply_markup=self.get_my_products_keyboard(context)
                )
                
                logger.info(f"Product added for user {user.id}: {clean_product['name'][:50]}")
                
            except Exception as scraping_error:
                logger.error(f"Scraping error for user {user.id}: {scraping_error}")
                await processing_msg.edit_text(
                    "❌ Failed to analyze the product. The website might be blocking automated access or the URL might not be a product page. Please try a different URL.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                storage.update_stats_secure('total_errors')
                
        except Exception as e:
            logger.error(f"Error in handle_product_link for user {user.id}: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while processing the product link. Please try again.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
            except:
                pass

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
            product_info = f"{product.get('name', '')} - {product.get('brand', '')} - {product.get('features', '')}"
            
            # Generate promo using OpenAI with proper translation system
            system_prompt = self.get_text('system_prompt', context)
            prompt = self.get_text('openai_prompt', context, product_info, product_info)

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
            
            # Store generated text
            context.user_data['last_generated_promo'] = promo_text
            context.user_data['last_generated_text'] = promo_text
            context.user_data['last_product_name'] = product.get('name', 'Product')
            
            # Update statistics
            storage.update_stats_secure('total_promos_generated')
            
            # Send result
            result_text = f"{self.get_text('promo_result', context, product.get('name', 'Product'))}\n\n{promo_text}\n\n{self.get_text('promo_footer', context)}"
            
            await query.edit_message_text(
                result_text,
                reply_markup=self.get_post_generation_keyboard(context)
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
        
        if not products:
            # No products available, go directly to prompt-based
            await query.edit_message_text(
                f"{self.get_text('generate_title', context)}\n\n{self.get_text('generate_instructions', context)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]])
            )
        else:
            # Show choice between product-based and prompt-based
            promo_text = f"{self.get_text('promo_choice_title', context)}\n\n{self.get_text('promo_choice_subtitle', context, len(products))}"
            await query.edit_message_text(
                promo_text,
                reply_markup=self.get_promo_creation_choice_keyboard(context)
            )
    
    async def show_promo_from_prompt(self, query, context):
        """Show promo from prompt instructions."""
        context.user_data['awaiting_promo_input'] = True
        
        await query.edit_message_text(
            f"{self.get_text('generate_title', context)}\n\n{self.get_text('generate_instructions', context)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]])
        )

    async def show_promo_from_product(self, query, context):
        """Show product selection for promo generation."""
        products = context.user_data.get('products', [])
        
        if not products:
            await query.edit_message_text(
                f"{self.get_text('promo_choice_title', context)}\n\n{self.get_text('no_products_available', context)}",
                reply_markup=self.get_promo_creation_choice_keyboard(context)
            )
        else:
            await query.edit_message_text(
                self.get_text('select_product_title', context, len(products)),
                reply_markup=self.get_product_selection_keyboard(context)
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
        storage.update_stats_secure('total_messages')
        
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

    async def handle_channel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel/group input from user."""
        user = update.effective_user
        channel_input = update.message.text.strip()
        
        try:
            # Clear waiting states
            context.user_data.pop('awaiting_channel_input', None)
            context.user_data.pop('waiting_for_channel_input', None)
            
            # Basic validation
            if not channel_input:
                await update.message.reply_text(
                    "Please provide a valid channel/group username or ID.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                return
            
            # Clean the input
            channel_id = channel_input.replace('@', '').strip()
            
            # Simple validation - just check if it looks reasonable
            if len(channel_id) < 3:
                await update.message.reply_text(
                    "Channel/group name is too short. Please try again.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                return
            
            # Send verification message
            processing_msg = await update.message.reply_text("🔍 Verifying channel/group access...")
            
            try:
                # Try to verify permissions (simplified)
                success, message = await self.verify_channel_permissions(context, channel_id)
                
                if success:
                    # Save channel info
                    context.user_data['channel_info'] = {
                        'channel_id': channel_id,
                        'auto_post': False,
                        'verified_at': datetime.now().isoformat()
                    }
                    
                    # Save user data
                    storage.save_user_data(user.id, context.user_data)
                    
                    await processing_msg.edit_text(
                        f"✅ Channel/group configured successfully!\n\nChannel: @{channel_id}\n\nYou can now post promotional content to this channel.",
                        reply_markup=self.get_channel_settings_keyboard(context)
                    )
                else:
                    await processing_msg.edit_text(
                        f"❌ Failed to verify channel/group access.\n\nError: {message}\n\nPlease make sure:\n1. The bot is added to the channel/group\n2. The bot has admin permissions\n3. The bot can post messages",
                        reply_markup=self.get_channel_settings_keyboard(context)
                    )
                    
            except Exception as e:
                logger.error(f"Channel verification error for user {user.id}: {e}")
                await processing_msg.edit_text(
                    f"❌ Error verifying channel/group: {str(e)}\n\nPlease check the channel/group name and try again.",
                    reply_markup=self.get_channel_settings_keyboard(context)
                )
                
        except Exception as e:
            logger.error(f"Error in handle_channel_input for user {user.id}: {e}", exc_info=True)
            await update.message.reply_text(
                "An error occurred while setting up the channel. Please try again.",
                reply_markup=self.get_channel_settings_keyboard(context)
            )

    async def handle_post_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle post text editing."""
        user = update.effective_user
        new_text = update.message.text.strip()
        
        try:
            # Clear editing states
            context.user_data.pop('awaiting_post_edit', None)
            context.user_data.pop('editing_post', None)
            
            if not new_text:
                await update.message.reply_text(
                    "Please provide valid text for the post.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                return
            
            # Store the edited text
            context.user_data['pending_post_text'] = new_text
            context.user_data['last_generated_text'] = new_text
            
            # Save user data
            storage.save_user_data(user.id, context.user_data)
            
            # Show confirmation
            channel_info = context.user_data.get('channel_info', {})
            product_name = context.user_data.get('last_product_name', 'Unknown')
            
            confirmation_text = f"✅ Text updated!\n\n"
            if channel_info.get('channel_id'):
                confirmation_text += f"Channel: @{channel_info['channel_id']}\n"
            confirmation_text += f"Product: {product_name}\n\n"
            confirmation_text += f"Updated text:\n{new_text}"
            
            await update.message.reply_text(
                confirmation_text,
                reply_markup=self.get_post_confirmation_keyboard(context)
            )
            
        except Exception as e:
            logger.error(f"Error in handle_post_edit for user {user.id}: {e}", exc_info=True)
            await update.message.reply_text(
                "An error occurred while editing the post. Please try again.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )

    async def handle_generated_text_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle generated text editing."""
        user = update.effective_user
        new_text = update.message.text.strip()
        
        try:
            # Clear editing states
            context.user_data.pop('awaiting_generated_text_edit', None)
            context.user_data.pop('editing_generated_text', None)
            
            if not new_text:
                await update.message.reply_text(
                    "Please provide valid text.",
                    reply_markup=self.get_back_to_menu_keyboard(context)
                )
                return
            
            # Store the edited text
            context.user_data['last_generated_text'] = new_text
            
            # Save user data
            storage.save_user_data(user.id, context.user_data)
            
            # Show the updated text with options
            result_text = f"✅ Text updated!\n\n{new_text}\n\n{self.get_text('promo_options', context)}"
            
            await update.message.reply_text(
                result_text,
                reply_markup=self.get_post_generation_keyboard(context)
            )
            
        except Exception as e:
            logger.error(f"Error in handle_generated_text_edit for user {user.id}: {e}", exc_info=True)
            await update.message.reply_text(
                "An error occurred while editing the text. Please try again.",
                reply_markup=self.get_back_to_menu_keyboard(context)
            )

    def run(self):
        """Run the bot."""
        logger.info("🤖 Bot is running...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES) 