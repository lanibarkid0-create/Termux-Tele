import requests
import random
from datetime import datetime

# ─────────────────────────────
#  PRICE FEED
# ─────────────────────────────
def get_price():
    urls = [
        "https://api.metals.live/v1/spot/gold",
        "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=8)
            d = r.json()
            if "metals.live" in url:
                return float(d[0]['price'])
            else:
                return float(d[0]['spreadProfilePrices'][0]['ask'])
        except:
            continue
    return None

# ─────────────────────────────
#  INDICATORS
# ─────────────────────────────
def calc_rsi(closes, period=7):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100.0
    return round(100 - (100 / (1 + ag / al)), 2)

def calc_ema(closes, period):
    if len(closes) < period:
        return closes[-1]
    k   = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for p in closes[period:]:
        ema = p * k + ema * (1 - k)
    return round(ema, 4)

def calc_stoch(closes, highs, lows, k=5):
    if len(closes) < k:
        return 50.0
    lo = min(lows[-k:])
    hi = max(highs[-k:])
    if hi == lo:
        return 50.0
    return round((closes[-1] - lo) / (hi - lo) * 100, 2)

def calc_atr(highs, lows, closes, period=5):
    if len(closes) < period + 1:
        return 0.5
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(
            highs[i]  - lows[i],
            abs(highs[i]  - closes[i-1]),
            abs(lows[i]   - closes[i-1])
        ))
    return round(sum(trs[-period:]) / period, 2)

def calc_macd(closes):
    if len(closes) < 26:
        return 0.0, 0.0
    m  = calc_ema(closes, 8)  - calc_ema(closes, 21)
    mp = calc_ema(closes[:-1], 8) - calc_ema(closes[:-1], 21) if len(closes) > 26 else m
    return round(m, 4), round(mp, 4)

# ─────────────────────────────
#  SNR
# ─────────────────────────────
def snr_zones(closes, highs, lows, lb=20):
    if len(closes) < lb:
        return None, None
    return round(min(lows[-lb:]), 2), round(max(highs[-lb:]), 2)

# ─────────────────────────────
#  SMC
# ─────────────────────────────
def bos_detect(closes, highs, lows):
    if len(closes) < 6:
        return "NONE"
    ph = max(highs[-6:-1])
    pl = min(lows[-6:-1])
    if closes[-1] > ph: return "BULL_BOS"
    if closes[-1] < pl: return "BEAR_BOS"
    return "NONE"

def choch_detect(closes):
    if len(closes) < 8:
        return "NONE"
    s = closes[-8:]
    if s[3] > s[0] and s[-1] < s[-3]: return "BEAR_CHOCH"
    if s[3] < s[0] and s[-1] > s[-3]: return "BULL_CHOCH"
    return "NONE"

def order_block(closes, highs, lows):
    if len(closes) < 5:
        return None, None
    ob_b = ob_br = None
    for i in range(len(closes)-4, len(closes)-1):
        if closes[i] < closes[i-1] and closes[i+1] > closes[i]:
            ob_b  = round((highs[i] + lows[i]) / 2, 2)
        if closes[i] > closes[i-1] and closes[i+1] < closes[i]:
            ob_br = round((highs[i] + lows[i]) / 2, 2)
    return ob_b, ob_br

# ─────────────────────────────
#  ICT
# ─────────────────────────────
def fvg_detect(highs, lows):
    if len(highs) < 3:
        return None, None
    bf = brf = None
    for i in range(len(highs)-3, len(highs)-1):
        if i > 0:
            if lows[i+1]  > highs[i-1]: bf  = round((lows[i+1]  + highs[i-1]) / 2, 2)
            if highs[i+1] < lows[i-1]:  brf = round((highs[i+1] + lows[i-1])  / 2, 2)
    return bf, brf

def liq_sweep(closes, highs, lows):
    if len(closes) < 15:
        return "NONE"
    ph = max(highs[-15:-2])
    pl = min(lows[-15:-2])
    if highs[-1] > ph and closes[-1] < ph: return "SWEEP_HIGH"
    if lows[-1]  < pl and closes[-1] > pl: return "SWEEP_LOW"
    return "NONE"

def mss_detect(closes):
    if len(closes) < 5:
        return "NONE"
    s = closes[-5:]
    if s[-3] < s[-4] and s[-2] < s[-3] and s[-1] > s[-2]: return "BULL_MSS"
    if s[-3] > s[-4] and s[-2] > s[-3] and s[-1] < s[-2]: return "BEAR_MSS"
    return "NONE"

def candle_pattern(closes, highs, lows):
    if len(closes) < 3:
        return "NONE"
    o1, c1 = closes[-3], closes[-2]
    h1, l1 = highs[-2], lows[-2]
    c2      = closes[-1]
    body    = abs(c1 - o1)
    uw      = h1 - max(c1, o1)
    lw      = min(c1, o1) - l1
    if lw > body * 2 and uw < body * 0.5:          return "HAMMER"
    if uw > body * 2 and lw < body * 0.5:          return "SHOOTING_STAR"
    if c2 > o1 and c2 > c1 and closes[-2] < o1:   return "BULL_ENGULF"
    if c2 < o1 and c2 < c1 and closes[-2] > o1:   return "BEAR_ENGULF"
    return "NONE"

# ─────────────────────────────
#  CONFIDENCE CALCULATOR
# ─────────────────────────────
def calc_confidence(buy_score, sell_score, max_score=28):
    dominant = max(buy_score, sell_score)
    if dominant == 0:
        return 0.0
    # base confidence dari score ratio
    raw = (dominant / max_score) * 100
    # bonus kalau gap besar antara buy vs sell
    gap = abs(buy_score - sell_score)
    bonus = min(gap * 1.5, 10)
    conf = min(round(raw + bonus, 1), 95.0)
    return conf

# ─────────────────────────────
#  MAIN ANALYZE
# ─────────────────────────────
def analyze(price_history, high_history, low_history):
    closes = price_history
    highs  = high_history
    lows   = low_history
    price  = closes[-1]

    rsi          = calc_rsi(closes, 7)
    ema8         = calc_ema(closes, 8)
    ema21        = calc_ema(closes, 21)
    ema8_p       = calc_ema(closes[:-1], 8)  if len(closes) > 8  else ema8
    ema21_p      = calc_ema(closes[:-1], 21) if len(closes) > 21 else ema21
    stoch        = calc_stoch(closes, highs, lows, 5)
    macd, macd_p = calc_macd(closes)
    atr          = calc_atr(highs, lows, closes, 5)
    sup, res     = snr_zones(closes, highs, lows, 20)
    bos          = bos_detect(closes, highs, lows)
    choch        = choch_detect(closes)
    ob_b, ob_br  = order_block(closes, highs, lows)
    fvg_b, fvg_br= fvg_detect(highs, lows)
    sweep        = liq_sweep(closes, highs, lows)
    mss          = mss_detect(closes)
    candle       = candle_pattern(closes, highs, lows)

    buy_score = sell_score = 0
    conf_list = []

    # RSI
    if rsi < 30:   buy_score  += 3; conf_list.append("✅ RSI Extreme Oversold")
    elif rsi < 40: buy_score  += 1; conf_list.append("✅ RSI Oversold")
    elif rsi > 70: sell_score += 3; conf_list.append("✅ RSI Extreme Overbought")
    elif rsi > 60: sell_score += 1; conf_list.append("✅ RSI Overbought")

    # Stoch
    if stoch < 20:   buy_score  += 2; conf_list.append("✅ Stoch Oversold")
    elif stoch > 80: sell_score += 2; conf_list.append("✅ Stoch Overbought")

    # EMA
    if ema8 > ema21 and ema8_p <= ema21_p:
        buy_score  += 3; conf_list.append("✅ EMA8 Cross Above EMA21")
    elif ema8 < ema21 and ema8_p >= ema21_p:
        sell_score += 3; conf_list.append("✅ EMA8 Cross Below EMA21")
    elif ema8 > ema21:
        buy_score  += 1; conf_list.append("✅ EMA Bullish Alignment")
    else:
        sell_score += 1; conf_list.append("✅ EMA Bearish Alignment")

    # MACD
    if macd > 0 and macd_p <= 0:   buy_score  += 2; conf_list.append("✅ MACD Bullish Cross")
    elif macd < 0 and macd_p >= 0: sell_score += 2; conf_list.append("✅ MACD Bearish Cross")

    # SNR
    if sup and abs(price - sup) < atr * 1.5:
        buy_score  += 2; conf_list.append("✅ SNR: At Support Zone")
    if res and abs(price - res) < atr * 1.5:
        sell_score += 2; conf_list.append("✅ SNR: At Resistance Zone")

    # SMC BOS
    if bos == "BULL_BOS":   buy_score  += 2; conf_list.append("✅ SMC: Bullish BOS")
    elif bos == "BEAR_BOS": sell_score += 2; conf_list.append("✅ SMC: Bearish BOS")

    # SMC CHoCH
    if choch == "BULL_CHOCH":   buy_score  += 3; conf_list.append("✅ SMC: Bullish CHoCH ⭐")
    elif choch == "BEAR_CHOCH": sell_score += 3; conf_list.append("✅ SMC: Bearish CHoCH ⭐")

    # SMC OB
    if ob_b  and abs(price - ob_b)  < atr: buy_score  += 2; conf_list.append("✅ SMC: Bullish OB")
    if ob_br and abs(price - ob_br) < atr: sell_score += 2; conf_list.append("✅ SMC: Bearish OB")

    # ICT FVG
    if fvg_b  and abs(price - fvg_b)  < atr: buy_score  += 2; conf_list.append("✅ ICT: Bullish FVG")
    if fvg_br and abs(price - fvg_br) < atr: sell_score += 2; conf_list.append("✅ ICT: Bearish FVG")

    # ICT Liq Sweep
    if sweep == "SWEEP_LOW":    buy_score  += 3; conf_list.append("✅ ICT: Liq Sweep Low ⭐")
    elif sweep == "SWEEP_HIGH": sell_score += 3; conf_list.append("✅ ICT: Liq Sweep High ⭐")

    # ICT MSS
    if mss == "BULL_MSS":   buy_score  += 3; conf_list.append("✅ ICT: Bullish MSS ⭐")
    elif mss == "BEAR_MSS": sell_score += 3; conf_list.append("✅ ICT: Bearish MSS ⭐")

    # Candle
    if candle in ["HAMMER","BULL_ENGULF"]:
        buy_score  += 2; conf_list.append(f"✅ Candle: {candle}")
    elif candle in ["SHOOTING_STAR","BEAR_ENGULF"]:
        sell_score += 2; conf_list.append(f"✅ Candle: {candle}")

    confidence = calc_confidence(buy_score, sell_score, 28)
    direction  = "BUY" if buy_score > sell_score else "SELL" if sell_score > buy_score else "NEUTRAL"

    return {
        "price":      price,
        "direction":  direction,
        "buy_score":  buy_score,
        "sell_score": sell_score,
        "confidence": confidence,
        "conf_list":  conf_list,
        "rsi":        rsi,
        "stoch":      stoch,
        "ema8":       ema8,
        "ema21":      ema21,
        "macd":       macd,
        "atr":        atr,
        "sup":        sup,
        "res":        res,
        "bos":        bos,
        "choch":      choch,
        "ob_b":       ob_b,
        "ob_br":      ob_br,
        "fvg_b":      fvg_b,
        "fvg_br":     fvg_br,
        "sweep":      sweep,
        "mss":        mss,
        "candle":     candle,
    }
