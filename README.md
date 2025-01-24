# 🚀 SolanaTradeMaster-Bot

![GitHub](https://img.shields.io/github/license/yourusername/SolanaTradeMaster-Bot)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Solana](https://img.shields.io/badge/solana-latest-green)

A powerful, secure, and feature-rich Telegram bot for automated Solana token trading.

## ✨ Features

### Core Trading Features
- 🔄 Manual buy/sell for Solana meme tokens
- 🌐 Multi-DEX support (Raydium/Jupiter/Meteora/PumpFun)
- 🛡️ Anti-MEV protection against front-running/sandwich attacks
- 📊 Advanced order types (Limit, Stop Loss, Take Profit)

### Wallet Management
- 🔑 Generate new wallets with encrypted private keys
- 🔌 Connect existing wallets
- 🔐 Secure key storage and management

### Token Management
- 📋 List tokens with pagination (20 per page)
- 🔍 Sort by value or purchase date
- 📈 Real-time price tracking
- 🔄 Automatic token discovery from Telegram channels

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Redis
- Linux server (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/SolanaTradeMaster-Bot.git
cd SolanaTradeMaster-Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create a `.env` file in the project root:
```env
TELEGRAM_TOKEN=your_bot_token
ENCRYPTION_KEY=your_encryption_key
RPC_URL=your_rpc_url
REDIS_URL=redis://localhost
```

## 🚀 Running Multiple Instances

### Using Systemd
1. Create service file:
```bash
sudo nano /etc/systemd/system/solanatrade@.service
```

2. Add configuration:
```ini
[Unit]
Description=SolanaTradeMaster Bot Instance %i
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/SolanaTradeMaster-Bot
Environment=BOT_TOKEN=your_token_%i
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Start instances:
```bash
sudo systemctl enable solanatrade@{1..5}
sudo systemctl start solanatrade@{1..5}
```

## 📝 Usage

### Basic Commands
- `/start` - Initialize bot
- `/createwallet` - Generate new wallet
- `/buy` - Buy tokens
- `/sell` - Sell tokens
- `/list` - List your tokens

### Advanced Trading
```
/buy <token_address> <amount> --limit-price 0.1 --anti-mev
/sell <token_address> <amount> --tp 20,50,30 --sl 10
```

## 🔒 Security Features

- AES-256 encryption for private keys
- Secure Redis storage
- Anti-MEV protection
- Rate limiting and request validation

## 📊 RPC Node Recommendations

| Provider | Use Case | Features |
|----------|----------|----------|
| Helius | Primary | High performance, MEV protection |
| QuickNode | Backup | Reliable, good latency |
| Private RPC | Optional | Maximum privacy |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

Trading cryptocurrencies carries significant risk. This bot is provided as-is with no guarantees. Always test thoroughly with small amounts first.

## 🌟 Acknowledgments

- [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Solana Web3.py](https://github.com/michaelhly/solana-py)
- [Jupiter API](https://docs.jup.ag/)
