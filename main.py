import asyncio
import sqlite3
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# SQLite Database connection
def get_db_connection():
    try:
        conn = sqlite3.connect('numbers.db')
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

# Function to ensure four-digit numbers (leading zeros)
def format_number(number: int) -> str:
    return f"{number:04d}"


def split_message_and_send(update: Update, message: str):
    max_length = 4096
    for i in range(0, len(message), max_length):
        update.message.reply_text(message[i:i+max_length])

async def split_message_and_send(update: Update, message: str):
    max_length = 4096
    if len(message) <= max_length:
        await update.message.reply_text(message)
    else:
        parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        for part in parts:
            await update.message.reply_text(part)

# Start command
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         # Fetch the user's first name
#         user_first_name = update.message.from_user.first_name
        
#         # Send a greeting message with the user's name
#         await update.message.reply_markdown_v2(f"Hello\\, ***{user_first_name}***\\! Welcome to the Lottery Bot 🎉\\. Let's get started\\!")
#     except Exception as e:
#         logging.error(f"Error sending start message: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Fetch the user's first name
        user_first_name = update.message.from_user.first_name
        
        # Send a greeting message with the user's name
        await update.message.reply_markdown_v2(f"Hello\\, ***{user_first_name}***\\! ")
    except Exception as e:
        logging.error(f"Error sending start message: {e}")


conversion_rules = {
    '_': r'\\_','.': r'\\.', '[': r'\\[', ']': r'\\]', '(': r'\\(', ')': r'\\)', '~': r'\\~', '>': r'\\>',
    '<': r'\\<', '#': r'\\#', '+': r'\\+', '-': r'\\-', '=': r'\\=', '|': r'\\|', '{': r'\\{',
    '}': r'\\}', '.': r'\\.', '!': r'\\!', '@': r'\\@', '?': r'\\?', '"': r'\\"'
}

def convert_content_parser(content: str) -> str:
    content = re.sub(r'(?<!\\)\*(?!\\)', r'\\*', content)
    content = re.sub(r'(?<!\\)\*\*(?!\\)', r'***', content)
    content = re.sub(r'(?<!`)`(?![`])', r'***', content)
    for original, replacement in conversion_rules.items():
        content = content.replace(original, replacement)
    return content

# Function for animated message
async def howtouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = [
        "1\\. **Check a Number**:\n\n\\- Send me any number, and I will check if it is available in the lottery\\.\n\n\\- Example: ``` 2000``` ",
        "2\\. **Add a Number**:\n\n\\- You can add a new number to the database by sending the command like:\n\n\\- ``` add 3000```  to add number 3000\\.",
        "3\\. **Remove a Number**:\n\n\\- To remove a number from the database, just send the command:\n\n\\- ``` remove 3000```  to remove number 3000\\.",
        "4\\. **Query a Range of Numbers**:\n\n\\- You can query a range of numbers to see which ones are available\\.\n\n\\- ``` 2000 \\- 3000``` \n\n\\- ``` 2000to3000``` \n\n\\- ``` 2000 to 3000``` ",
        "thank you"
    ]

    previous_message = await update.message.reply_text(messages[0],parse_mode='MarkdownV2')
    for message in messages[1:]:
        await asyncio.sleep(5)
        previous_message = await previous_message.edit_text(message,parse_mode='MarkdownV2')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    
    # If the message is "add <number>", process it
    if user_message.lower().startswith("add ") and user_message[4:].isdigit():
        number = int(user_message[4:])
        formatted_number = format_number(number)  # Ensure the number is four digits
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO numbers (number) VALUES (?)', (formatted_number,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"The number ***{formatted_number}*** has been added to the database.")
        return

    # If the message is "remove <number>", process it
    elif user_message.lower().startswith("remove ") and user_message[7:].isdigit():
        number = int(user_message[7:])
        formatted_number = format_number(number)  # Ensure the number is four digits
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM numbers WHERE number = ?', (formatted_number,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"The number ***{formatted_number}*** has been removed from the database.")
        return

    # If the message is a direct number (check if number exists in the database)
    elif user_message.isdigit():
        number = int(user_message)
        formatted_number = format_number(number)  # Ensure the number is four digits
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM numbers WHERE number = ?', (formatted_number,))
        result = cursor.fetchone()
        conn.close()

        if result:
            await update.message.reply_markdown_v2(f"✅ The number ***{formatted_number}*** is available for the lottery\\!"
)

        else:
            await update.message.reply_markdown_v2(f"❌ Oops\\! The number ***{formatted_number}*** has already been chosen\\. "
)

    
    # Handle range queries (e.g., "between 1000 and 2000")
    else:
        # Regex patterns for different range formats
        patterns = [
            r'between (\d{1,4}) and (\d{1,4})',  # "between 2000 and 3000"
            r'(\d{1,4})-(\d{1,4})',             # "2000-3000"
            r'(\d{1,4}) - (\d{1,4})',             # "2000-3000"
            r'(\d{1,4})to(\d{1,4})',             # "2000-3000"
            r'(\d{1,4}) to (\d{1,4})',             # "2000-3000"
            r'between (\d{1,4})-(\d{1,4})'      # "between 2000-3000"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, user_message)
            if match:
                start_number = int(match.group(1))
                end_number = int(match.group(2))
                
                # Ensure the numbers are four digits
                formatted_start = format_number(start_number)
                formatted_end = format_number(end_number)
                
                # Fetch numbers in range
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT number FROM numbers WHERE number BETWEEN ? AND ?', 
                               (formatted_start, formatted_end))
                results = cursor.fetchall()
                conn.close()

                if results:
                    numbers = [str(result[0]) for result in results]  # Convert each number to a string
                    numbers_str = ', '.join(numbers)
                    await split_message_and_send(update, f"Numbers between {formatted_start} and {formatted_end}: {numbers_str}")
                else:
                    await update.message.reply_text(f"No numbers found between {formatted_start} and {formatted_end}.")
                return
        await update.message.reply_text("Sorry, I couldn't understand your range query. Please try again.")


def main():
    TELEGRAM_BOT_TOKEN = "7779911666:AAGzmk1FJksITK_SFspqmTbaepIobtqXidk"
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("howtouse", howtouse))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logging.info("Bot shutting down.")
    except Exception as e:
        logging.error(f"Error running bot: {e}")

if __name__ == "__main__":
    main()



    # updater = Updater("7779911666:AAGzmk1FJksITK_SFspqmTbaepIobtqXidk", use_context=True)


    
