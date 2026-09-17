from datetime import datetime
from config import SL_PIPS, TP_PIPS, PIP_VALUE, MIN_CONFIDENCE

def bar(score, mx=28):
    f = min(int((score / mx) * 10), 10)
    return "🟩" * f + "⬜" * (10 - f)

def conf_bar(conf):
    f = min(int((conf / 100) * 10), 10)
    return "🔵" * f + "⬛" * (10 - f)

def grade(conf):
    if conf >= 80: return "🏆 PREMIUM"
    if conf >= 70: return "🥇 HIGH"
    if conf >= 60: return "🥈 GOOD"
    return "⚠️ LOW"

def format_signal(data):
    price      = data['price']
    direction  = data['direction']
    buy_score  = data['buy_score']
    sell_score = data['sell_score']
    confidence = data['confidence']
    conf_list  = data['conf_list']

    sl_val = round(SL_PIPS * PIP_VALUE, 1)
    tp_val = round(TP_PIPS * PIP_VALUE, 1)

    if direction == "BUY":
        signal_txt  = "🟢 BUY SCALP"
        entry_low   = round(price - 0.3, 2)
        entry_high  = round(price + 0.3, 2)
        sl          = round(price - sl_val, 2)
        tp          = round(price + tp_val, 2)
        emoji_trend = "📈"
    else:
        signal_txt  = "🔴 SELL SCALP"
        entry_low   = round(price - 0.3, 2)
        entry_high  = round(price + 0.3, 2)
        sl          = round(price + sl_val, 2)
        tp          = round(price - tp_val, 2)
        emoji_trend = "📉"

    hour = datetime.utcnow().hour
    if 7 <= hour < 16:
        session = "🇬🇧 London ⚡"
    elif 12 <= hour < 21:
        session = "🇺🇸 New York ⚡"
    elif 0 <= hour < 8:
        session = "🇯🇵 Tokyo 🐢"
    else:
        session = "🌙 Off Session"

    now       = datetime.utcnow().strftime("%H:%M UTC")
    conf_text = "\n".join(conf_list) if conf_list else "• No confluence"

    msg = f"""
🚨 *XAUUSD M5 SCALPING SIGNAL* 🚨
━━━━━━━━━━━━━━━━━━━━
🕐 *{now}* | {session}
━━━━━━━━━━━━━━━━━━━━
📌 *Signal     :* *{signal_txt}* {emoji_trend}
💰 *Harga      :* `{price}`
🎯 *Entry Zone :* `{entry_low} — {entry_high}`
🛑 *Stop Loss  :* `{sl}` ({SL_PIPS} pips)
✅ *Take Profit:* `{tp}` ({TP_PIPS} pips)
📐 *RR Ratio   :* 1:2
━━━━━━━━━━━━━━━━━━━━
🎯 *CONFIDENCE : {confidence}% {grade(confidence)}*
{conf_bar(confidence)}
━━━━━━━━━━━━━━━━━━━━
🧠 *CONFLUENCE ({len(conf_list)} faktor)*
{conf_text}
━━━━━━━━━━━━━━━━━━━━
📈 Buy  Score : {buy_score}/28 {bar(buy_score)}
📉 Sell Score : {sell_score}/28 {bar(sell_score)}
━━━━━━━━━━━━━━━━━━━━
📊 *INDIKATOR*
- RSI(7)  : `{data['rsi']}`
- Stoch   : `{data['stoch']}`
- EMA8    : `{data['ema8']}`
- EMA21   : `{data['ema21']}`
- MACD    : `{data['macd']}`
- ATR     : `{data['atr']}`
━━━━━━━━━━━━━━━━━━━━
🏛 *SNR*
- Support    : `{data['sup']}`
- Resistance : `{data['res']}`
━━━━━━━━━━━━━━━━━━━━
🏦 *SMC*
- BOS   : `{data['bos']}`
- CHoCH : `{data['choch']}`
- OB ↑  : `{data['ob_b']}`
- OB ↓  : `{data['ob_br']}`
━━━━━━━━━━━━━━━━━━━━
🧿 *ICT*
- FVG ↑      : `{data['fvg_b']}`
- FVG ↓      : `{data['fvg_br']}`
- Liq Sweep  : `{data['sweep']}`
- MSS        : `{data['mss']}`
━━━━━━━━━━━━━━━━━━━━
🕯 *Candle : `{data['candle']}`*
━━━━━━━━━━━━━━━━━━━━
⚠️ _M5 Scalping — DYOR, Not Financial Advice_
"""
    return msg

def format_wait(confidence, direction, buy_score, sell_score, price):
    now = datetime.utcnow().strftime("%H:%M UTC")
    return (
        f"⏸ *XAUUSD — NO SIGNAL* | {now}\n"
        f"💰 Price: `{price}`\n"
        f"📊 Confidence: `{confidence}%` (Min: 60%)\n"
        f"📈 Buy: `{buy_score}` | 📉 Sell: `{sell_score}`\n"
        f"_Menunggu setup yang valid..._"
    )
