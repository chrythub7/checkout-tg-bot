
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl
import random
import string

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    print("Error: Please add your bot token to Replit Secrets with key 'TELEGRAM_BOT_TOKEN'")
    exit(1)

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": os.getenv("EMAIL_ADDRESS"),
    "password": os.getenv("EMAIL_APP_PASSWORD"),
    "sender_name": "GreenHaven Team"
}

# File paths
WAITLIST_FILE = "waitlist.json"
ORDERS_FILE = "orders.json"

# Business configuration
BUSINESS_CONFIG = {
    "company_name": "GreenHaven",
    "support_contact": "@EratOlee"
}

# Product catalog with enhanced information
PRODUCT_CATALOG = {
    "Gorilla Glue": {
        "in_stock": True, 
        "stock_qty": 35,
        "description": "Ottima qualità con alta potenza",
        "thc_level": "25-28%",
        "category": "Hybrid"
    },
    "Amnesia Haze": {
        "in_stock": True, 
        "stock_qty": 25,
        "description": "Classica varietà sativa-dominante",
        "thc_level": "20-25%",
        "category": "Sativa"
    }, 
    "Girl Scout Cookies": {
        "in_stock": True, 
        "stock_qty": 15,
        "description": "Varietà ibrida di buona qualità",
        "thc_level": "22-26%",
        "category": "Hybrid"
    },
    "OG Kush": {
        "in_stock": True, 
        "stock_qty": 10,
        "description": "Leggendaria varietà indica-dominante",
        "thc_level": "19-24%",
        "category": "Indica"
    }
}

# Quantity options with professional pricing
QUANTITY_OPTIONS = {
    "5g": {"grams": 5, "discount": 0, "emoji": "🌱", "tier": "Starter"},
    "10g": {"grams": 10, "discount": 5, "emoji": "🍃", "tier": "Standard"},
    "15g": {"grams": 15, "discount": 8, "emoji": "🌿", "tier": "Standard+"},
    "25g": {"grams": 25, "discount": 12, "emoji": "💚", "tier": "Premium"},
    "35g": {"grams": 35, "discount": 15, "emoji": "🔥", "tier": "Premium+"},
    "50g": {"grams": 50, "discount": 18, "emoji": "⭐", "tier": "VIP"},
    "75g": {"grams": 75, "discount": 22, "emoji": "💎", "tier": "VIP+"},
    "100g": {"grams": 100, "discount": 25, "emoji": "👑", "tier": "Elite"}
}

# Shipping options
SHIPPING_OPTIONS = {
    "italy_standard": {"name": "Spedizione Standard Italia", "price": 8, "days": "2-3", "emoji": "🇮🇹"},
    "italy_express": {"name": "Spedizione Express Italia", "price": 15, "days": "1", "emoji": "🇮🇹⚡"}
}

class EmailManager:
    """Handle email operations for order confirmations and tracking"""
    
    @staticmethod
    def generate_tracking_id():
        """Generate a unique tracking ID"""
        prefix = "GH"
        numbers = ''.join(random.choices(string.digits, k=10))
        return f"{prefix}{numbers}"
    
    @staticmethod
    def send_email(to_email, subject, html_content, text_content=None):
        """Send email using SMTP"""
        try:
            if not EMAIL_CONFIG["email"] or not EMAIL_CONFIG["password"]:
                logger.error("Email credentials not configured in environment variables")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['email']}>"
            msg['To'] = to_email
            
            # Add text and HTML content
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                server.starttls(context=context)
                server.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_order_confirmation(order_data):
        """Send order confirmation email to customer"""
        try:
            email = order_data["shipping_data"]["email"]
            order_id = order_data["order_id"]
            
            subject = f"🌿 Conferma Ordine {order_id} - GreenHaven"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                    .footer {{ background: #333; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; }}
                    .order-details {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #4CAF50; }}
                    .highlight {{ color: #4CAF50; font-weight: bold; }}
                    .warning {{ background: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌿 GreenHaven</h1>
                        <h2>Conferma del Tuo Ordine</h2>
                    </div>
                    
                    <div class="content">
                        <p>Ciao <strong>{order_data["shipping_data"]["name"]}</strong>,</p>
                        
                        <p>Grazie per aver scelto GreenHaven! Il tuo ordine è stato ricevuto e sarà processato dopo la conferma del pagamento PayPal.</p>
                        
                        <div class="order-details">
                            <h3>📋 Dettagli Ordine</h3>
                            <p><strong>ID Ordine:</strong> <span class="highlight">{order_id}</span></p>
                            <p><strong>Prodotto:</strong> {order_data["product"]} ({order_data["quantity"]["grams"]}g)</p>
                            <p><strong>Totale:</strong> <span class="highlight">€{order_data["total_price"]:.2f}</span></p>
                            <p><strong>Spedizione:</strong> {order_data["shipping"]["name"]}</p>
                            <p><strong>Tempi di Consegna:</strong> {order_data["shipping"]["days"]} giorni lavorativi</p>
                        </div>
                        
                        <div class="order-details">
                            <h3>📦 Indirizzo di Spedizione</h3>
                            <p>{order_data["shipping_data"]["name"]}<br>
                            {order_data["shipping_data"]["address"]}<br>
                            Tel: {order_data["shipping_data"]["phone"]}</p>
                        </div>
                        
                        <div class="warning">
                            <strong>⚠️ Importante:</strong> Il tuo ordine sarà processato e spedito solo dopo la conferma del pagamento PayPal. Riceverai un'email con il numero di tracking entro 24 ore dall'elaborazione.
                        </div>
                        
                        <p><strong>Cosa succede ora:</strong></p>
                        <ol>
                            <li>✅ Ordine ricevuto (completato)</li>
                            <li>💳 Verifica pagamento PayPal (in corso)</li>
                            <li>📦 Preparazione e spedizione</li>
                            <li>🚚 Consegna in {order_data["shipping"]["days"]} giorni</li>
                        </ol>
                    </div>
                    
                    <div class="footer">
                        <p>🔒 Packaging discreto garantito | 🇮🇹 Spedizione in tutta Italia</p>
                        <p>Supporto: @EratOlee | Email: {EMAIL_CONFIG["email"]}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            GreenHaven - Conferma Ordine {order_id}
            
            Ciao {order_data["shipping_data"]["name"]},
            
            Il tuo ordine è stato ricevuto:
            - Prodotto: {order_data["product"]} ({order_data["quantity"]["grams"]}g)
            - Totale: €{order_data["total_price"]:.2f}
            - Spedizione: {order_data["shipping"]["name"]}
            
            L'ordine sarà processato dopo la conferma del pagamento PayPal.
            
            Grazie per aver scelto GreenHaven!
            """
            
            return EmailManager.send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending order confirmation: {e}")
            return False
    
    @staticmethod
    def send_shipping_notification(order_data, tracking_id):
        """Send shipping notification with tracking ID"""
        try:
            email = order_data["shipping_data"]["email"]
            order_id = order_data["order_id"]
            
            subject = f"📦 Il Tuo Ordine {order_id} è Stato Spedito!"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                    .footer {{ background: #333; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; }}
                    .tracking {{ background: white; padding: 20px; margin: 15px 0; border-radius: 5px; border: 2px solid #4CAF50; text-align: center; }}
                    .tracking-id {{ font-size: 24px; color: #4CAF50; font-weight: bold; letter-spacing: 2px; }}
                    .highlight {{ color: #4CAF50; font-weight: bold; }}
                    .success {{ background: #d4edda; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌿 GreenHaven</h1>
                        <h2>📦 Il Tuo Ordine è in Viaggio!</h2>
                    </div>
                    
                    <div class="content">
                        <p>Ciao <strong>{order_data["shipping_data"]["name"]}</strong>,</p>
                        
                        <div class="success">
                            <strong>🎉 Ottime notizie!</strong> Il tuo ordine è stato spedito e sta arrivando da te!
                        </div>
                        
                        <div class="tracking">
                            <h3>📍 Numero di Tracking</h3>
                            <div class="tracking-id">{tracking_id}</div>
                            <p><small>Usa questo codice per tracciare il tuo pacco</small></p>
                        </div>
                        
                        <p><strong>📋 Riepilogo Spedizione:</strong></p>
                        <ul>
                            <li><strong>Ordine:</strong> {order_id}</li>
                            <li><strong>Prodotto:</strong> {order_data["product"]} ({order_data["quantity"]["grams"]}g)</li>
                            <li><strong>Metodo:</strong> {order_data["shipping"]["name"]}</li>
                            <li><strong>Tempi previsti:</strong> {order_data["shipping"]["days"]} giorni lavorativi</li>
                            <li><strong>Indirizzo:</strong> {order_data["shipping_data"]["address"]}</li>
                        </ul>
                        
                        <div class="success">
                            <strong>📦 Packaging Discreto:</strong> Il tuo ordine è confezionato in modo completamente discreto, senza riferimenti al contenuto.
                        </div>
                        
                        <p><strong>🔍 Come tracciare il pacco:</strong></p>
                        <ol>
                            <li>Utilizza il codice tracking fornito sopra</li>
                            <li>Controlla sul sito del corriere o app mobile</li>
                            <li>Riceverai SMS di notifica dal corriere</li>
                        </ol>
                        
                        <p><strong>📱 Contattaci se hai domande:</strong> @EratOlee</p>
                    </div>
                    
                    <div class="footer">
                        <p>🚚 Tracking: {tracking_id} | 🇮🇹 Spedizione Italia</p>
                        <p>Grazie per aver scelto GreenHaven! 💚</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            GreenHaven - Ordine Spedito!
            
            Ciao {order_data["shipping_data"]["name"]},
            
            Il tuo ordine {order_id} è stato spedito!
            
            Tracking ID: {tracking_id}
            Prodotto: {order_data["product"]} ({order_data["quantity"]["grams"]}g)
            Consegna prevista: {order_data["shipping"]["days"]} giorni
            
            Usa il tracking ID per seguire la spedizione.
            
            Grazie per aver scelto GreenHaven!
            """
            
            return EmailManager.send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending shipping notification: {e}")
            return False

class DataManager:
    """Handle data persistence operations"""
    
    @staticmethod
    def load_json(filename, default=None):
        if default is None:
            default = {}
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
        return default
    
    @staticmethod
    def save_json(filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            return False

class PriceCalculator:
    """Handle price calculations and formatting"""
    
    BASE_PRICE_PER_GRAM = 9.59  # Professional pricing
    
    @classmethod
    def calculate_product_price(cls, grams, discount=0):
        base_price = grams * cls.BASE_PRICE_PER_GRAM
        discount_amount = base_price * (discount / 100)
        return base_price - discount_amount
    
    @classmethod
    def calculate_total_price(cls, product_price, shipping_price):
        return product_price + shipping_price
    
    @staticmethod
    def format_price(price):
        return f"€{price:.2f}"

class MessageFormatter:
    """Handle message formatting and templates"""
    
    @staticmethod
    def welcome_message():
        return (
            f"🌿 *Benvenuto su {BUSINESS_CONFIG['company_name']}* 🌿\n\n"
            "✨ *Prodotti Cannabis di Buona Qualità*\n"
            "📦 *Packaging Discreto e Sicuro*\n"
            "🇮🇹 *Spedizione Veloce in Tutta Italia*\n"
            "💎 *Sconti Volume fino al 25%*\n"
            "💳 *Pagamento Sicuro con PayPal*\n\n"
            "📧 *Supporto:* " + BUSINESS_CONFIG['support_contact'] + "\n\n"
            "👇 *Seleziona una varietà per continuare:*"
        )
    
    @staticmethod
    def product_details(product_name, product_info):
        return (
            f"🌿 *{product_name}* - {product_info['category']}\n\n"
            f"📝 *Description:* {product_info['description']}\n"
            f"🧪 *THC Level:* {product_info['thc_level']}\n"
            f"📦 *Available Stock:* {product_info['stock_qty']}g\n"
            f"💰 *Base Price:* {PriceCalculator.format_price(PriceCalculator.BASE_PRICE_PER_GRAM)}/g\n\n"
            f"💎 *Volume Discounts Available*\n"
            f"🚚 *Professional Shipping Options*\n\n"
            f"👇 *Choose your preferred quantity:*"
        )
    
    @staticmethod
    def out_of_stock_message(product_name):
        return (
            f"⚠️ *Stock Notice*\n\n"
            f"🌿 *{product_name}* is currently *out of stock*\n\n"
            f"📧 *Get notified when back in stock:*\n"
            f"Please provide your email address and we'll notify you immediately when this product becomes available.\n\n"
            f"✅ *Professional stock management ensures quick restocking*"
        )
    
    @staticmethod
    def order_summary(product_name, quantity_info, shipping_info, prices):
        discount_text = ""
        if quantity_info['discount'] > 0:
            savings = prices['original'] - prices['discounted']
            discount_text = (
                f"💰 *Regular Price:* {PriceCalculator.format_price(prices['original'])}\n"
                f"🎉 *{quantity_info['tier']} Discount ({quantity_info['discount']}%):* "
                f"-{PriceCalculator.format_price(savings)}\n"
            )
        
        return (
            f"✅ *Order Summary*\n\n"
            f"🌿 *Product:* {product_name}\n"
            f"📦 *Quantity:* {quantity_info['grams']}g ({quantity_info['tier']} Tier)\n\n"
            + discount_text +
            f"💳 *Subtotal:* {PriceCalculator.format_price(prices['discounted'])}\n"
            f"🚚 *{shipping_info['name']}:* {PriceCalculator.format_price(shipping_info['price'])}\n"
            f"⏱️ *Delivery:* {shipping_info['days']} business days\n\n"
            f"💎 *TOTAL AMOUNT: {PriceCalculator.format_price(prices['total'])}*\n\n"
            f"🔒 *Secure Payment Processing*\n"
            f"📦 *Discreet Packaging Guaranteed*\n\n"
            f"👇 *Proceed to secure checkout:*"
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        keyboard = []
        for product_name, info in PRODUCT_CATALOG.items():
            if info["in_stock"] and info["stock_qty"] > 0:
                button_text = f"{product_name} ({info['stock_qty']}g)"
            else:
                button_text = f"{product_name} (Out of Stock)"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"product_{product_name}")])
        
        # Add support button
        keyboard.append([
            InlineKeyboardButton("📞 Support", callback_data="support")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            MessageFormatter.welcome_message(),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ Service temporarily unavailable. Please try again later.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data.startswith("product_"):
            await handle_product_selection(query, context)
        elif query.data.startswith("qty_"):
            await handle_quantity_selection(query, context)
        elif query.data.startswith("shipping_"):
            await handle_shipping_selection(query, context)
        elif query.data == "back_to_products":
            await show_product_catalog(query)
        elif query.data == "support":
            await show_support_info(query)
    except Exception as e:
        logger.error(f"Error handling callback query {query.data}: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again or contact support.")

async def handle_product_selection(query, context):
    """Handle product selection"""
    product_name = query.data.replace("product_", "")
    product_info = PRODUCT_CATALOG.get(product_name)
    
    if not product_info:
        await query.edit_message_text("❌ Product not found.")
        return
    
    if not product_info["in_stock"] or product_info["stock_qty"] <= 0:
        # Handle out of stock
        context.user_data['waiting_product'] = product_name
        context.user_data['waiting_contact'] = True
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Products", callback_data="back_to_products")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            MessageFormatter.out_of_stock_message(product_name),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    # Show quantity options based on available stock
    keyboard = []
    available_stock = product_info["stock_qty"]
    
    for qty_key, qty_info in QUANTITY_OPTIONS.items():
        if qty_info["grams"] <= available_stock:
            # Available quantity
            price = PriceCalculator.calculate_product_price(qty_info["grams"], qty_info["discount"])
            
            if qty_info["discount"] > 0:
                original_price = PriceCalculator.calculate_product_price(qty_info["grams"], 0)
                savings = original_price - price
                button_text = (f"{qty_info['emoji']} {qty_key} - {PriceCalculator.format_price(price)} "
                             f"(Save {PriceCalculator.format_price(savings)}!)")
            else:
                button_text = f"{qty_info['emoji']} {qty_key} - {PriceCalculator.format_price(price)}"
        else:
            # Out of stock for this quantity
            button_text = f"❌ {qty_key} - Out of Stock"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"qty_{product_name}_{qty_key}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Products", callback_data="back_to_products")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        MessageFormatter.product_details(product_name, product_info),
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_quantity_selection(query, context):
    """Handle quantity selection and show shipping options"""
    parts = query.data.split("_", 2)
    product_name = parts[1]
    quantity_key = parts[2]
    
    # Check if quantity is available
    product_info = PRODUCT_CATALOG.get(product_name)
    quantity_info = QUANTITY_OPTIONS.get(quantity_key)
    
    if not product_info or not quantity_info:
        await query.edit_message_text("❌ Invalid selection.")
        return
    
    # Check if the requested quantity is available
    if quantity_info["grams"] > product_info["stock_qty"]:
        await query.answer("❌ This quantity is out of stock", show_alert=True)
        return
    
    context.user_data['selected_product'] = product_name
    context.user_data['selected_quantity'] = quantity_key
    
    keyboard = []
    for ship_key, ship_info in SHIPPING_OPTIONS.items():
        button_text = (f"{ship_info['emoji']} {ship_info['name']} - "
                      f"{PriceCalculator.format_price(ship_info['price'])} "
                      f"({ship_info['days']} days)")
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"shipping_{ship_key}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"product_{product_name}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    shipping_text = (
        "🚚 *Scegli la Tua Opzione di Spedizione:*\n\n"
        "📦 *Tutti i pacchi sono confezionati in modo discreto*\n"
        "🔒 *Numero di tracciamento fornito*\n"
        "✅ *Assicurazione inclusa*\n"
        "🇮🇹 *Spedizione solo in Italia*\n\n"
        "👇 *Scegli il tuo metodo di consegna preferito:*"
    )
    
    await query.edit_message_text(shipping_text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_shipping_selection(query, context):
    """Handle shipping selection and start collecting shipping info"""
    shipping_key = query.data.replace("shipping_", "")
    product_name = context.user_data.get('selected_product')
    quantity_key = context.user_data.get('selected_quantity')
    
    if not all([product_name, quantity_key]):
        await query.edit_message_text("❌ Session expired. Please start over with /start")
        return
    
    # Store shipping selection
    context.user_data['selected_shipping'] = shipping_key
    context.user_data['collecting_shipping_info'] = True
    context.user_data['shipping_step'] = 'name'
    
    quantity_info = QUANTITY_OPTIONS[quantity_key]
    shipping_info = SHIPPING_OPTIONS[shipping_key]
    
    # Calculate prices for reference
    original_price = PriceCalculator.calculate_product_price(quantity_info["grams"], 0)
    discounted_price = PriceCalculator.calculate_product_price(quantity_info["grams"], quantity_info["discount"])
    total_price = PriceCalculator.calculate_total_price(discounted_price, shipping_info["price"])
    
    context.user_data['order_total'] = total_price
    
    shipping_form_text = (
        f"📋 *Informazioni di Spedizione*\n\n"
        f"🌿 *Prodotto:* {product_name} ({quantity_info['grams']}g)\n"
        f"🚚 *Spedizione:* {shipping_info['name']}\n"
        f"💰 *Totale:* {PriceCalculator.format_price(total_price)}\n\n"
        f"📝 *Per completare l'ordine, fornisci le seguenti informazioni:*\n\n"
        f"👤 **Passo 1/5: Nome e Cognome**\n"
        f"Scrivi il tuo nome completo:"
    )
    
    keyboard = [[InlineKeyboardButton("❌ Annulla Ordine", callback_data="back_to_products")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(shipping_form_text, parse_mode='Markdown', reply_markup=reply_markup)

async def show_product_catalog(query):
    """Show the product catalog"""
    keyboard = []
    for product_name, info in PRODUCT_CATALOG.items():
        if info["in_stock"] and info["stock_qty"] > 0:
            button_text = f"{product_name} ({info['stock_qty']}g)"
        else:
            button_text = f"{product_name} (Out of Stock)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"product_{product_name}")])
    
    keyboard.append([
        InlineKeyboardButton("📞 Support", callback_data="support")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        MessageFormatter.welcome_message(),
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_support_info(query):
    """Show support information"""
    support_text = (
        f"📞 *Supporto Clienti*\n\n"
        f"💬 *Supporto Telegram:* {BUSINESS_CONFIG['support_contact']}\n\n"
        f"❓ *Domande Frequenti:*\n"
        f"• Tempi di spedizione: 1-3 giorni lavorativi\n"
        f"• Metodi di pagamento: Solo PayPal\n"
        f"• Ordine minimo: 5g\n"
        f"• Spedizione: Solo Italia 🇮🇹\n"
        f"• Packaging: 100% discreto\n"
        f"• Garanzia di qualità"
    )
    
    keyboard = [
        [InlineKeyboardButton("💬 Contatta il Supporto", url=f"https://t.me/{BUSINESS_CONFIG['support_contact'].replace('@', '')}")],
        [InlineKeyboardButton("🛒 Continua lo Shopping", callback_data="back_to_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(support_text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for waitlist and shipping form"""
    
    # Handle waitlist contact info
    if context.user_data.get('waiting_contact'):
        await handle_waitlist_contact(update, context)
        return
    
    # Handle shipping form
    if context.user_data.get('collecting_shipping_info'):
        await handle_shipping_form_input(update, context)
        return

async def handle_waitlist_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact information for waitlist"""
    contact_info = update.message.text
    product_name = context.user_data.get('waiting_product')
    user_id = update.effective_user.id
    
    # Load and update waitlist
    waitlist = DataManager.load_json(WAITLIST_FILE, {})
    if product_name not in waitlist:
        waitlist[product_name] = []
    
    # Add user to waitlist
    user_entry = {
        "user_id": user_id,
        "contact_info": contact_info,
        "username": update.effective_user.username or "N/A",
        "timestamp": datetime.now().isoformat()
    }
    
    # Check if user already exists
    user_exists = any(entry["user_id"] == user_id for entry in waitlist[product_name])
    
    if not user_exists:
        waitlist[product_name].append(user_entry)
        DataManager.save_json(WAITLIST_FILE, waitlist)
        
        confirmation_text = (
            f"✅ *Waitlist Registration Confirmed*\n\n"
            f"📧 *Contact:* {contact_info}\n"
            f"🌿 *Product:* {product_name}\n"
            f"🔔 *You'll be notified immediately when back in stock*\n\n"
            f"Thank you for choosing {BUSINESS_CONFIG['company_name']}! 💚"
        )
    else:
        confirmation_text = (
            f"ℹ️ *Already Registered*\n\n"
            f"You're already on our waitlist for {product_name}.\n"
            f"We'll notify you as soon as it's available! 💚"
        )
    
    keyboard = [[InlineKeyboardButton("🛒 Browse Other Products", callback_data="back_to_products")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(confirmation_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    # Reset user state
    context.user_data['waiting_contact'] = False
    context.user_data['waiting_product'] = None

async def handle_shipping_form_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shipping form input step by step"""
    user_input = update.message.text.strip()
    current_step = context.user_data.get('shipping_step')
    
    if not context.user_data.get('shipping_data'):
        context.user_data['shipping_data'] = {}
    
    if current_step == 'name':
        context.user_data['shipping_data']['name'] = user_input
        context.user_data['shipping_step'] = 'address'
        
        next_message = (
            f"✅ *Nome:* {user_input}\n\n"
            f"🏠 **Passo 2/5: Indirizzo Completo**\n"
            f"Scrivi l'indirizzo di spedizione completo:\n"
            f"(Via, Numero Civico, Città, CAP, Provincia)\n\n"
            f"*Esempio:* Via Roma 123, Milano, 20100, MI"
        )
        
    elif current_step == 'address':
        context.user_data['shipping_data']['address'] = user_input
        context.user_data['shipping_step'] = 'phone'
        
        next_message = (
            f"✅ *Indirizzo:* {user_input}\n\n"
            f"📱 **Passo 3/5: Numero di Telefono**\n"
            f"Inserisci il tuo numero di telefono:\n"
            f"(Necessario per la consegna)\n\n"
            f"*Esempio:* +39 333 1234567"
        )
        
    elif current_step == 'phone':
        context.user_data['shipping_data']['phone'] = user_input
        context.user_data['shipping_step'] = 'email'
        
        next_message = (
            f"✅ *Telefono:* {user_input}\n\n"
            f"📧 **Passo 4/5: Email**\n"
            f"Inserisci la tua email:\n"
            f"(Per ricevere tracking e conferme)\n\n"
            f"*Esempio:* mario.rossi@email.com"
        )
        
    elif current_step == 'email':
        if '@' not in user_input or '.' not in user_input:
            await update.message.reply_text("❌ Email non valida. Riprova con un formato corretto (esempio@email.com)")
            return
            
        context.user_data['shipping_data']['email'] = user_input
        context.user_data['shipping_step'] = 'notes'
        
        next_message = (
            f"✅ *Email:* {user_input}\n\n"
            f"📝 **Passo 5/5: Note Aggiuntive (Opzionale)**\n"
            f"Aggiungi eventuali note per la consegna:\n"
            f"(Citofono, piano, orari preferiti, ecc.)\n\n"
            f"Scrivi le note oppure digita 'SALTA' per continuare:"
        )
        
    elif current_step == 'notes':
        if user_input.upper() != 'SALTA':
            context.user_data['shipping_data']['notes'] = user_input
        else:
            context.user_data['shipping_data']['notes'] = "Nessuna nota"
            
        # Show final order confirmation
        await show_final_order_confirmation(update, context)
        return
    
    keyboard = [[InlineKeyboardButton("❌ Annulla Ordine", callback_data="back_to_products")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(next_message, parse_mode='Markdown', reply_markup=reply_markup)

async def show_final_order_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final order confirmation with all details"""
    shipping_data = context.user_data.get('shipping_data', {})
    product_name = context.user_data.get('selected_product')
    quantity_key = context.user_data.get('selected_quantity')
    shipping_key = context.user_data.get('selected_shipping')
    
    quantity_info = QUANTITY_OPTIONS[quantity_key]
    shipping_info = SHIPPING_OPTIONS[shipping_key]
    total_price = context.user_data.get('order_total')
    
    # Create order summary
    order_summary = (
        f"📋 *RIEPILOGO ORDINE FINALE*\n\n"
        f"🌿 *Prodotto:* {product_name} ({quantity_info['grams']}g)\n"
        f"💰 *Totale:* {PriceCalculator.format_price(total_price)}\n"
        f"🚚 *Spedizione:* {shipping_info['name']}\n\n"
        f"📦 *DATI DI SPEDIZIONE:*\n"
        f"👤 *Nome:* {shipping_data.get('name', 'N/A')}\n"
        f"🏠 *Indirizzo:* {shipping_data.get('address', 'N/A')}\n"
        f"📱 *Telefono:* {shipping_data.get('phone', 'N/A')}\n"
        f"📧 *Email:* {shipping_data.get('email', 'N/A')}\n"
        f"📝 *Note:* {shipping_data.get('notes', 'Nessuna')}\n\n"
        f"💳 *Paga con PayPal per completare l'ordine*\n"
        f"⚠️ *L'ordine sarà processato dopo il pagamento*"
    )
    
    # Generate unique order ID
    order_id = f"GH{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Save order to file
    order_data = {
        "order_id": order_id,
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "N/A",
        "product": product_name,
        "quantity": quantity_info,
        "shipping": shipping_info,
        "shipping_data": shipping_data,
        "total_price": total_price,
        "status": "pending_payment",
        "timestamp": datetime.now().isoformat()
    }
    
    # Load existing orders and add new one
    orders = DataManager.load_json(ORDERS_FILE, [])
    orders.append(order_data)
    DataManager.save_json(ORDERS_FILE, orders)
    
    # Send order confirmation email
    email_sent = EmailManager.send_order_confirmation(order_data)
    if email_sent:
        logger.info(f"Order confirmation email sent for {order_id}")
    else:
        logger.warning(f"Failed to send order confirmation email for {order_id}")
    
    # Generate PayPal payment link with order reference
    payment_link = f"https://paypal.me/greenhaven/{total_price:.2f}EUR"
    
    keyboard = [
        [InlineKeyboardButton("💳 PAGA CON PAYPAL", url=payment_link)],
        [InlineKeyboardButton("✏️ Modifica Dati", callback_data="back_to_products")],
        [InlineKeyboardButton("📞 Supporto", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{order_summary}\n\n🆔 *ID Ordine:* `{order_id}`",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    # Send order notification to admin (you)
    admin_notification = (
        f"🔔 *NUOVO ORDINE RICEVUTO*\n\n"
        f"🆔 *ID:* {order_id}\n"
        f"👤 *Cliente:* @{update.effective_user.username or 'N/A'}\n"
        f"🌿 *Prodotto:* {product_name} ({quantity_info['grams']}g)\n"
        f"💰 *Totale:* {PriceCalculator.format_price(total_price)}\n\n"
        f"📦 *SPEDIRE A:*\n"
        f"👤 {shipping_data.get('name')}\n"
        f"🏠 {shipping_data.get('address')}\n"
        f"📱 {shipping_data.get('phone')}\n"
        f"📧 {shipping_data.get('email')}\n"
        f"📝 Note: {shipping_data.get('notes')}\n\n"
        f"⚠️ *Ordine in attesa di pagamento PayPal*"
    )
    
    # You can send this to yourself or save it to check later
    logger.info(f"New order received: {order_id}")
    logger.info(admin_notification)
    
    # Reset user state
    context.user_data.clear()

# Admin commands
async def admin_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to manage stock"""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin_stock <product_name> <quantity>")
        return
    
    product_name = context.args[0]
    try:
        quantity = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid quantity. Please use a number.")
        return
    
    if product_name in PRODUCT_CATALOG:
        PRODUCT_CATALOG[product_name]['stock_qty'] = quantity
        PRODUCT_CATALOG[product_name]['in_stock'] = quantity > 0
        await update.message.reply_text(f"✅ Updated {product_name} stock to {quantity}g")
    else:
        await update.message.reply_text(f"❌ Product '{product_name}' not found")

async def admin_ship_order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to mark order as shipped and send tracking email"""
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /admin_ship <order_id>")
        return
    
    order_id = context.args[0]
    
    # Load orders
    orders = DataManager.load_json(ORDERS_FILE, [])
    
    # Find the order
    order_found = None
    for i, order in enumerate(orders):
        if order["order_id"] == order_id:
            order_found = order
            order_index = i
            break
    
    if not order_found:
        await update.message.reply_text(f"❌ Order {order_id} not found")
        return
    
    if order_found["status"] == "shipped":
        await update.message.reply_text(f"⚠️ Order {order_id} already marked as shipped")
        return
    
    # Generate tracking ID
    tracking_id = EmailManager.generate_tracking_id()
    
    # Update order status
    orders[order_index]["status"] = "shipped"
    orders[order_index]["tracking_id"] = tracking_id
    orders[order_index]["shipped_date"] = datetime.now().isoformat()
    
    # Save updated orders
    DataManager.save_json(ORDERS_FILE, orders)
    
    # Send shipping notification email
    email_sent = EmailManager.send_shipping_notification(order_found, tracking_id)
    
    if email_sent:
        await update.message.reply_text(
            f"✅ Order {order_id} marked as shipped\n"
            f"📦 Tracking ID: {tracking_id}\n"
            f"📧 Shipping notification sent to customer"
        )
    else:
        await update.message.reply_text(
            f"✅ Order {order_id} marked as shipped\n"
            f"📦 Tracking ID: {tracking_id}\n"
            f"⚠️ Failed to send email notification"
        )

async def admin_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to view recent orders"""
    orders = DataManager.load_json(ORDERS_FILE, [])
    
    if not orders:
        await update.message.reply_text("📭 No orders found")
        return
    
    # Show last 5 orders
    recent_orders = orders[-5:]
    
    message = "📋 *Recent Orders:*\n\n"
    
    for order in reversed(recent_orders):
        status_emoji = "💳" if order["status"] == "pending_payment" else "📦"
        message += (
            f"{status_emoji} *{order['order_id']}*\n"
            f"👤 {order['shipping_data']['name']}\n"
            f"🌿 {order['product']} ({order['quantity']['grams']}g)\n"
            f"💰 €{order['total_price']:.2f}\n"
            f"📧 {order['shipping_data']['email']}\n"
            f"📅 {order['timestamp'][:16]}\n"
            f"🔄 Status: {order['status']}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_test_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to test email configuration"""
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /admin_test_email <email_address>")
        return
    
    test_email = context.args[0]
    
    subject = "🧪 Test Email - GreenHaven"
    html_content = """
    <h2>🌿 Test Email da GreenHaven</h2>
    <p>Se ricevi questa email, la configurazione SMTP funziona correttamente!</p>
    <p><strong>✅ Email configurata con successo</strong></p>
    """
    text_content = "Test Email da GreenHaven - Configurazione SMTP funzionante!"
    
    email_sent = EmailManager.send_email(test_email, subject, html_content, text_content)
    
    if email_sent:
        await update.message.reply_text(f"✅ Test email sent successfully to {test_email}")
    else:
        await update.message.reply_text(f"❌ Failed to send test email to {test_email}")
        
        # Check configuration
        missing_configs = []
        if not EMAIL_CONFIG["email"]:
            missing_configs.append("EMAIL_ADDRESS")
        if not EMAIL_CONFIG["password"]:
            missing_configs.append("EMAIL_APP_PASSWORD")
            
        if missing_configs:
            await update.message.reply_text(
                f"⚠️ Missing email configuration in Secrets:\n" + 
                "\n".join(f"- {config}" for config in missing_configs)
            )

def main():
    """Start the bot"""
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("admin_stock", admin_stock_command))
        app.add_handler(CommandHandler("admin_ship", admin_ship_order_command))
        app.add_handler(CommandHandler("admin_orders", admin_orders_command))
        app.add_handler(CommandHandler("admin_test_email", admin_test_email_command))
        app.add_handler(CallbackQueryHandler(handle_callback_query))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
        
        logger.info(f"Starting {BUSINESS_CONFIG['company_name']} Bot...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
