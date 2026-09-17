import time
import random
import threading
from datetime import datetime
import telebot

from config import (
    TOKEN, CHAT_ID, CHECK_INTERVAL,
    MIN_CONFIDENCE, MIN_SCORE
)
from engine import get_price, analyze
from formatter import format_signal, format_wait

# ─────────────────────────────
#  STATE
# ─────────────────────────────
price_history  = []
high_history   = []
low_history    = []
last_direction = "NONE"
total_signals  = 0
bot            = telebot.TeleBot(TOKEN)

def log(msg):
    now = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

# ─────────────────────────────
#  MAIN LOOP
# ─────────────────────────────
def check_and_send():
    global price_history, high_history, low_history
    global last_direction, total_signals

    price = get_price()
    if price is None:
        log("❌ Gagal ambil harga")
        return

    # Simulasi high/low M5
    noise = round(random.uniform(0.2, 0.9), 2)
    high  = round(price + noise, 2)
    low   = round(price - noise, 2)

    price_history.append(price)
    high_history.append(high)
    low_history.append(low)

    MAX = 200
    if len(price_history) > MAX:
        price_history = price_history[-MAX:]
        high_history  = high_history[-MAX:]
        low_history   = low_history[-MAX:]

    # Butuh minimal 30 data dulu
    if len(price_history) < 30:
        log(f"📊 Collecting data... {len(price_history)}/30 | Price: {price}")
        return

    # Analyze
    data = analyze(price_history, high_history, low_history)
    confidence = data['confidence']
    direction  = data['direction']
    buy_score  = data['buy_score']
    sell_score = data['sell_score']

    log(f"📊 Price: {price} | Dir: {direction} | "
        f"Conf: {confidence}% | B:{buy_score} S:{sell_score}")

    # ── Filter: hanya kirim kalau confidence >= 60% ──
    dominant_score = max(buy_score, sell_score)

    if (confidence >= MIN_CONFIDENCE
            and dominant_score >= MIN_SCORE
            and direction != "NEUTRAL"):

        # Hindari duplicate signal arah yang sama berturut-turut
        if direction == last_direction:
            log(f"⏭ Skip — same direction ({direction}) as last signal")
            return

        msg = format_signal(data)
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
        last_direction = direction
        total_signals += 1
        log(f"✅ SIGNAL SENT — {direction} | Conf: {confidence}% | Total: {total_signals}")

    else:
        log(f"⏸ No signal — Conf {confidence}% < {MIN_CONFIDENCE}% atau score rendah")

def run_server():
    log("🚀 XAUUSD M5 Scalping Server Started")
    log(f"⚙️  Min Confidence : {MIN_CONFIDENCE}%")
    log(f"⚙️  Min Score      : {MIN_SCORE}")
    log(f"⚙️  Interval       : {CHECK_INTERVAL} menit")

    while True:
        try:
            check_and_send()
        except Exception as e:
            log(f"⚠️ Error: {e}")
        time.sleep(CHECK_INTERVAL * 60)

# ─────────────────────────────
#  BOT COMMANDS
# ─────────────────────────────
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    bot.send_message(msg.chat.id,
        "🤖 *XAUUSD M5 Scalping Bot*\n\n"
        "Signal otomatis dikirim saat:\n"
        "• Confidence ≥ 60%\n"
        "• Multi-confluence SNR + SMC + ICT\n\n"
        "📋 *Commands:*\n"
        "/signal — Cek sinyal sekarang\n"
        "/status — Status server\n"
        "/help   — Bantuan",
        parse_mode="Markdown")

@bot.message_handler(commands=['signal'])
def cmd_signal(msg):
    bot.send_message(msg.chat.id, "⏳ Analyzing market...")
    if len(price_history) < 30:
        bot.send_message(msg.chat.id,
            f"⏳ Server masih collecting data: {len(price_history)}/30\n"
            f"Tunggu beberapa menit lagi.")
        return
    data = analyze(price_history, high_history, low_history)
    conf = data['confidence']
    if conf >= MIN_CONFIDENCE and data['direction'] != "NEUTRAL":
        bot.send_message(msg.chat.id, format_signal(data), parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id,
            format_wait(conf, data['direction'],
                        data['buy_score'], data['sell_score'], data['price']),
            parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def cmd_status(msg):
    price = price_history[-1] if price_history else "N/A"
    bot.send_message(msg.chat.id,
        f"📡 *Server Status*\n\n"
        f"• Data terkumpul : `{len(price_history)}/200`\n"
        f"• Harga terakhir : `{price}`\n"
        f"• Total signal   : `{total_signals}`\n"
        f"• Last direction : `{last_direction}`\n"
        f"• Min confidence : `{MIN_CONFIDENCE}%`\n"
        f"• Interval cek   : `{CHECK_INTERVAL} menit`",
        parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(msg.chat.id,
        "📋 *Command List*\n\n"
        "/signal — Request sinyal sekarang\n"
        "/status — Cek status server\n"
        "/start  — Info bot\n"
        "/help   — Menu ini\n\n"
        "⚡ Signal otomatis tiap 5 menit\n"
        "🎯 Minimum confidence 60%",
        parse_mode="Markdown")

# ─────────────────────────────
#  RUN
# ─────────────────────────────
if __name__ == "__main__":
    # Server loop di background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    # Bot polling di main thread
    log("🤖 Bot polling started...")
    bot.polling(none_stop=True, interval=0, timeout=20)
