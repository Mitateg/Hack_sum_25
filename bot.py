"""
Main bot class for the Telegram Promo Text Generator Bot
Uses modular architecture with secure components
"""

import logging
import openai
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
        """Create main menu keyboard."""
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
        
        # Channel settings (placeholder)
        elif query.data == 'channel_settings':
            await query.edit_message_text(
                "🚧 Channel Settings\n\nThis feature will be implemented in the next phase of development.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]])
            )
        
        # Other features (placeholders)
        else:
            await query.edit_message_text(
                f"🚧 Feature Coming Soon\n\nThe '{query.data}' feature is being implemented.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_menu', context), callback_data='main_menu')]])
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        storage.update_stats('total_messages')
        
        # Check if waiting for product link
        if context.user_data.get('awaiting_product_link'):
            await self.handle_product_link(update, context)
            return
        
        # Check if waiting for promo input
        if context.user_data.get('awaiting_promo_input'):
            await self.generate_promo_text(update, context)
            return
        
        # Default: treat as promo generation request
        text = sanitize_input(update.message.text)
        if text:
            await self.generate_promo_text(update, context)
        else:
            await update.message.reply_text(
                self.get_text('empty_product', context)
            )
    
    async def generate_promo_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate promotional text using OpenAI."""
        try:
            text = sanitize_input(update.message.text)
            
            # Send processing message
            processing_msg = await update.message.reply_text("🔄 Generating promotional text...")
            
            # Generate promo using OpenAI
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=self.get_text('openai_prompt', context, text, text),
                    max_tokens=200,
                    temperature=0.7
                )
                
                promo_text = response.choices[0].text.strip()
                
                # Store generated text
                context.user_data['last_generated_promo'] = promo_text
                context.user_data['last_product_name'] = text
                
                # Update statistics
                storage.update_stats('total_promos_generated')
                
                # Send result
                result_text = f"{self.get_text('promo_result', context, text)}\n\n{promo_text}\n\n{self.get_text('promo_footer', context)}"
                
                await processing_msg.edit_text(
                    result_text,
                    reply_markup=self.get_promo_generation_keyboard(context)
                )
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                await processing_msg.edit_text(
                    self.get_text('general_error', context)
                )
                
        except Exception as e:
            logger.error(f"Error in generate_promo_text: {e}")
            await update.message.reply_text(
                self.get_text('general_error', context)
            )
        finally:
            # Clear awaiting state
            context.user_data.pop('awaiting_promo_input', None)
    
    async def handle_product_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product link input."""
        url = sanitize_input(update.message.text)
        
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text(
                self.get_text('invalid_url', context)
            )
            return
        
        # Send analyzing message
        analyzing_msg = await update.message.reply_text(
            self.get_text('analyzing_product', context)
        )
        
        try:
            # Scrape product info
            raw_data, error = scraper.scrape_product_info(url)
            
            if error:
                await analyzing_msg.edit_text(
                    self.get_text('extraction_failed', context, error)
                )
                return
            
            # Add to products
            products = context.user_data.get('products', [])
            products.append(raw_data)
            context.user_data['products'] = products
            
            # Save user data
            user_id = update.effective_user.id
            storage.save_user_data(user_id, context.user_data)
            
            await analyzing_msg.edit_text(
                f"{self.get_text('product_added_title', context)}\n\n{self.get_text('product_added_message', context, len(products))}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(self.get_text('back_to_products', context), callback_data='my_products')]])
            )
            
        except Exception as e:
            logger.error(f"Error handling product link: {e}")
            await analyzing_msg.edit_text(
                self.get_text('extraction_failed', context, str(e))
            )
        finally:
            # Clear awaiting state
            context.user_data.pop('awaiting_product_link', None)
    
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
        
        context.user_data['awaiting_product_link'] = True
        
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
    
    def run(self):
        """Run the bot."""
        logger.info("🤖 Bot is running...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES) 