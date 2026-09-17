import telebot
import schedule
import time
import threading
from config import CHAT_ID, CHECK_INTERVAL
from signal import generate_signal

# Inisialisasi Bot dengan Token langsung
TOKEN = "8619871111:AAGLdfPCbLsSGCiTEmmbPxqnlciyzEQlpsY"
bot = telebot.TeleBot(TOKEN)

def send_signal():
    try:
        msg = generate_signal()
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
        print("Signal sent successfully.")
    except Exception as e:
        print(f"Error sending message: {e}")

def run_schedule():
    schedule.every(CHECK_INTERVAL).minutes.do(send_signal)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("Bot started...")
    
    # Jalankan penjadwalan di background thread
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Kirim sinyal pertama kali saat dijalankan
    send_signal()
    
    # Menjaga script tetap berjalan
    while True:
        time.sleep(1)
