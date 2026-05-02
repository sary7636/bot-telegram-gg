import requests
import time
import pandas as pd
from flask import Flask
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

# --- 1. الإعدادات ---
TELEGRAM_TOKEN = "8393656924:AAEdgUPLXXS6bEQWphnmDAQiz_mfsnYO6KI"
CHAT_ID = "8393656924"

app = Flask('')

@app.route('/')
def home(): return "The Golden Whale Radar is Live!"

# --- 2. دالة التقييم الذكي ---
def get_label(val, excel, good):
    if val >= excel: return "💎 ممتاز دخول"
    if val >= good: return "✅ متوسط دخول"
    return "⚪ عادي"

# --- 3. جلب أقوى 50 عملة (سيولة الفيوتشرز) ---
def get_top_symbols():
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        data = requests.get(url, timeout=10).json()
        # ترتيب حسب حجم تداول USDT
        top_50 = sorted(data, key=lambda x: float(x['quoteVolume']), reverse=True)[:50]
        return [s['symbol'] for s in top_50 if s['symbol'].endswith('USDT')]
    except: return []

# --- 4. وظيفة الفحص المتقدمة ---
def analyze_market(symbol):
    try:
        # جلب البيانات (15 دقيقة)
        resp = requests.get(f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m&limit=60", timeout=5).json()
        df = pd.DataFrame(resp, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        df['c'] = df['c'].astype(float)
        df['v'] = df['v'].astype(float)

        # حساب RSI
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)).iloc[-1]))

        # بيانات العقود (OI & Funding)
        oi = float(requests.get(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}").json()['openInterest'])
        funding = float(requests.get(f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}").json()['lastFundingRate']) * 100

        # فحص السيولة (CVD/Delta)
        last_vol = df['v'].iloc[-1]
        avg_vol = df['v'].tail(20).mean()
        vol_ratio = last_vol / avg_vol

        # --- فلتر الشراء (Long) ---
        if rsi <= 30:
            status = "🆘 CVD في قاع تاريخي - ارتداد نفاث" if vol_ratio > 3.5 else get_label(vol_ratio, 2.5, 1.2)
            msg = (
                f"🟢 **إشارة LONG قوية** 🟢\n"
                f"● العملة: #{symbol}\n"
                f"● RSI: {rsi:.1f}\n"
                f"● السعر: {df['c'].iloc[-1]}\n"
                f"------------------------\n"
                f"📊 الفائدة المفتوحة: {get_label(vol_ratio, 3.0, 1.5)}\n"
                f"💰 التمويل: {funding:.4f}% {'💎' if funding < 0 else '✅'}\n"
                f"📉 CVD والسيولة: {status}\n"
                f"📈 نت دلتا شراء: {get_label(vol_ratio, 4.0, 2.0)}\n"
            )
            send_telegram(msg)

        # --- فلتر البيع (Short) ---
        elif rsi >= 70:
            msg = (
                f"🔴 **إشارة SHORT قوية** 🔴\n"
                f"● العملة: #{symbol}\n"
                f"● RSI: {rsi:.1f}\n"
                f"● السعر: {df['c'].iloc[-1]}\n"
                f"------------------------\n"
                f"📊 الفائدة المفتوحة: {get_label(vol_ratio, 3.0, 1.5)}\n"
                f"💰 التمويل: {funding:.4f}% {'💎' if funding > 0.01 else '✅'}\n"
                f"📉 CVD والسيولة: {get_label(vol_ratio, 2.5, 1.2)}\n"
                f"📈 نت دلتا بيع: {get_label(vol_ratio, 4.0, 2.0)}\n"
            )
            send_telegram(msg)

    except: pass

def main_loop():
    while True:
        symbols = get_top_symbols()
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(analyze_market, symbols)
        time.sleep(120) # فحص كل دقيقتين

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    main_loop()
