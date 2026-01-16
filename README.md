# SVU Helper Bot 🚀

A modular Telegram bot built with **Aiogram 3** to manage student project submissions and tutor offers.

## Features
- 📚 **Project Submission**: Guided FSM flow for students to submit projects with file support.
- 🎁 **Offer Management**: Admins can send price/delivery offers for submitted projects.
- 💳 **Payment Verification**: Integrated workflow for handling payment receipts.
- 📂 **Project Tracking**: Categorized views for pending, ongoing, and completed projects.
- 📢 **Broadcasting**: Admin tool to send messages to all bot users.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 2. Installation
1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration
Create a `.env` file in the root directory:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
```

### 4. Running the Bot
```bash
python main.py
```

## Project Structure
- `handlers/`: logic for admin and client events.
- `keyboards/`: Inline and reply keyboard definitions.
- `utils/`: Constants and formatting helpers.
- `scripts/`: Maintenance and debugging utilities.
- `database.py`: SQLite database abstraction layer.
- `main.py`: Entry point and bot initialization.

## Maintenance
Use scripts in the `scripts/` folder for routine checks:
- `python scripts/read_db.py`: View current database records.
- `python scripts/debug_commands.py`: Reset bot menu commands.
