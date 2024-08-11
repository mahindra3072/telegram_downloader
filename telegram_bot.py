from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import aria2p
import time
import os
from urllib.parse import urlparse

# Initialize the aria2p API
print("Connecting to aria2c with aria2p")
aria2 = aria2p.API(
    aria2p.Client(host="http://localhost", port=6800, secret="")
)
print(aria2)

def bytes_to_mb(bytes_amount):
    return bytes_amount / (1024 * 1024)

# Function to download the file using aria2p with custom options
def download_file(update: Update, url: str, download_dir: str):
    # Extract filename from URL
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)

    # Set user-agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.134 Safari/537.36"

    # Add the download with custom options
    download = aria2.add_uris(
        [url],
        options={
            "dir": download_dir,
            "out": filename,
            "user-agent": user_agent,
            "max-connection-per-server": "2"  # Equivalent to -x2
        }
    )

    # Send initial message
    message = update.message.reply_text("Starting download...")

    previous_text = None

    while not download.is_complete:
        # Refresh the download status
        try:
            download.update()
        except Exception as e:
            print(f"Error updating download status: {e}")
            break

        # Calculate progress percentage
        progress = download.completed_length / download.total_length * 100 if download.total_length else 0

        # Create a progress bar
        bar_length = 20
        filled_length = int(bar_length * progress // 100)
        bar = "*" * filled_length + "-" * (bar_length - filled_length)

        # Generate new status text
        status_text = (f"Downloading: {download.name}\n"
                       f"Downloaded: {bytes_to_mb(download.completed_length):.2f} MB / {bytes_to_mb(download.total_length):.2f} MB\n"
                       f"Progress: [{bar}] {progress:.2f}%")

        # Update the message only if content has changed
        if status_text != previous_text:
            try:
                print(download.completed_length)
                if download.completed_length != "0":
                    update.message.bot.edit_message_text(
                        chat_id=message.chat_id,
                        message_id=message.message_id,
                        text=status_text
                    )

                previous_text = status_text
            except Exception as e:
                print(f"Failed to update message: {e}")

        time.sleep(5)  # Wait for 5 seconds before updating the progress

    # Send a final message when the download is complete
    final_text = (f"Download complete: {download.name}\n"
                  f"Total size: {bytes_to_mb(download.total_length):.2f} MB")
    try:
        update.message.bot.edit_message_text(
            chat_id=message.chat_id,
            message_id=message.message_id,
            text=final_text
        )
    except Exception as e:
        print(f"Failed to update message: {e}")

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Send me a URL to download the file.')

# Message handler for URLs
def download_handler(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    download_dir = '/dev/temp_disk'  # Change this to your preferred directory

    if url.startswith("http://") or url.startswith("https://"):
        download_file(update, url, download_dir)
    else:
        update.message.reply_text("Please send a valid URL.")

# Main function to start the bot
def main() -> None:
    token = '6663096430:AAHCHoh07SmEi5Yxx8nFyiBYptg5F0a3HhA'  # Replace with your bot's token

    updater = Updater(token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
