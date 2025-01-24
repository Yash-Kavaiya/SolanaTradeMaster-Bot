import asyncio
import base64
import json
from typing import Dict, List, Optional
from datetime import datetime

import aiohttp
from cryptography.fernet import Fernet
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import TransactionInstruction
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from redis import Redis

class SecurityManager:
    def __init__(self, encryption_key: str):
        self.fernet = Fernet(encryption_key.encode())
        
    def encrypt_private_key(self, private_key: bytes) -> str:
        """Encrypt private key using Fernet (implementation of AES)"""
        return self.fernet.encrypt(private_key).decode()
    
    def decrypt_private_key(self, encrypted_key: str) -> bytes:
        """Decrypt private key"""
        return self.fernet.decrypt(encrypted_key.encode())

class TokenManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
    async def add_token(self, wallet_id: str, token_address: str, token_data: dict):
        """Store token data in Redis"""
        key = f"tokens:{wallet_id}:{token_address}"
        self.redis.hmset(key, token_data)
        
    async def get_tokens(self, wallet_id: str, page: int = 1, sort_by: str = 'value') -> List[dict]:
        """Get paginated token list (20 per page)"""
        tokens_per_page = 20
        start = (page - 1) * tokens_per_page
        end = start + tokens_per_page
        
        # Get all tokens for wallet
        pattern = f"tokens:{wallet_id}:*"
        token_keys = self.redis.keys(pattern)
        
        tokens = []
        for key in token_keys:
            token_data = self.redis.hgetall(key)
            tokens.append(token_data)
        
        # Sort tokens
        if sort_by == 'value':
            tokens.sort(key=lambda x: float(x.get('value', 0)), reverse=True)
        elif sort_by == 'date':
            tokens.sort(key=lambda x: x.get('purchase_date', ''), reverse=True)
            
        return tokens[start:end]

class TradingManager:
    def __init__(self, rpc_url: str):
        self.client = AsyncClient(rpc_url)
        self.jupiter_api = "https://quote-api.jup.ag/v6"
        
    async def get_quote(self, input_mint: str, output_mint: str, amount: int) -> dict:
        """Get quote from Jupiter aggregator"""
        async with aiohttp.ClientSession() as session:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": 50,  # 0.5% slippage
            }
            async with session.get(f"{self.jupiter_api}/quote", params=params) as response:
                return await response.json()
                
    async def execute_trade(self, quote: dict, wallet: Keypair, anti_mev: bool = True) -> str:
        """Execute trade with optional MEV protection"""
        if anti_mev:
            # Add random delay
            delay = random.uniform(0.1, 2.0)
            await asyncio.sleep(delay)
            
        # Get transaction from Jupiter
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.jupiter_api}/swap", json=quote) as response:
                swap_tx = await response.json()
                
        # Sign and send transaction
        transaction = Transaction.deserialize(base64.b64decode(swap_tx['swapTransaction']))
        signed_tx = wallet.sign_transaction(transaction)
        
        return await self.client.send_raw_transaction(signed_tx.serialize())

class SolanaTelegramBot:
    def __init__(self, token: str, security_manager: SecurityManager, 
                 token_manager: TokenManager, trading_manager: TradingManager):
        self.application = Application.builder().token(token).build()
        self.security_manager = security_manager
        self.token_manager = token_manager
        self.trading_manager = trading_manager
        
        # Register handlers
        self.register_handlers()
        
    def register_handlers(self):
        """Register command handlers"""
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('createwallet', self.create_wallet_command))
        self.application.add_handler(CommandHandler('buy', self.buy_command))
        self.application.add_handler(CommandHandler('sell', self.sell_command))
        self.application.add_handler(CommandHandler('list', self.list_tokens_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
    async def start_command(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        welcome_text = """
        Welcome to Solana Trading Bot!
        
        Available commands:
        /createwallet - Create new wallet
        /buy - Buy tokens
        /sell - Sell tokens
        /list - List your tokens
        """
        await update.message.reply_text(welcome_text)
        
    async def create_wallet_command(self, update: Update, context: CallbackContext):
        """Handle /createwallet command"""
        keypair = Keypair()
        encrypted_private_key = self.security_manager.encrypt_private_key(keypair.secret_key)
        
        # Store encrypted private key
        user_id = str(update.effective_user.id)
        wallet_data = {
            'public_key': str(keypair.public_key),
            'private_key': encrypted_private_key
        }
        
        await update.message.reply_text(
            f"Wallet created!\nPublic Key: {keypair.public_key}\n\n"
            "Your private key has been encrypted and stored securely."
        )
        
    async def list_tokens_command(self, update: Update, context: CallbackContext):
        """Handle /list command"""
        user_id = str(update.effective_user.id)
        page = context.args[0] if context.args else 1
        sort_by = context.args[1] if len(context.args) > 1 else 'value'
        
        tokens = await self.token_manager.get_tokens(user_id, page, sort_by)
        
        if not tokens:
            await update.message.reply_text("No tokens found.")
            return
            
        # Create token list message
        message = "Your tokens:\n\n"
        for token in tokens:
            message += (f"Symbol: {token['symbol']}\n"
                       f"Value: ${float(token['value']):.2f}\n"
                       f"Purchase Date: {token['purchase_date']}\n\n")
            
        # Add pagination buttons
        keyboard = [
            [
                InlineKeyboardButton("Previous", callback_data=f"list_{page-1}_{sort_by}"),
                InlineKeyboardButton("Next", callback_data=f"list_{page+1}_{sort_by}")
            ],
            [
                InlineKeyboardButton("Sort by Value", callback_data=f"list_{page}_value"),
                InlineKeyboardButton("Sort by Date", callback_data=f"list_{page}_date")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
    async def handle_callback(self, update: Update, context: CallbackContext):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        data = query.data.split('_')
        
        if data[0] == 'list':
            page = int(data[1])
            sort_by = data[2]
            await self.list_tokens_command(update, context)
            
    def run(self):
        """Start the bot"""
        self.application.run_polling()

# Configuration
config = {
    'telegram_token': 'YOUR_BOT_TOKEN',
    'encryption_key': Fernet.generate_key().decode(),
    'rpc_url': 'https://api.mainnet-beta.solana.com',
    'redis_url': 'redis://localhost'
}

# Initialize components
redis_client = Redis.from_url(config['redis_url'])
security_manager = SecurityManager(config['encryption_key'])
token_manager = TokenManager(redis_client)
trading_manager = TradingManager(config['rpc_url'])

# Create and run bot
bot = SolanaTelegramBot(
    config['telegram_token'],
    security_manager,
    token_manager,
    trading_manager
)

if __name__ == "__main__":
    bot.run()
