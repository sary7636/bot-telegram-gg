import os
import requests
import time
import pandas as pd
from flask import Flask
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from binance.client import Client

# --- 1. الإعدادات سحب البيانات من Render Environment Variables ---
# يتم وضع هذه القيم في موقع Render في قسم Environment
TELEGRAM_TOKEN = os.getenv("8393656924:AAEdgUPLXXS6bEQWphnmDAQiz_mfsnYO6KI")
CHAT_ID = os.getenv("8393656924")
BINANCE_API_KEY = os.getenv("XaDvU5yfRLk6cOFtLPmKhUnfGe9LO5c85EGY84gWLyDuwvRn4NbghLUlCdzDh4eT")
BINANCE_SECRET_KEY = os.getenv("jO7OYkZ1Am2QXRxUtZpdZd5qazFD5OFXh1ZkrUAwYYUjUauQZeBWaCFoZYekKD2V")

# ربط حساب باينانس (لجلب بيانات السيولة والتمويل)
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

app = Flask('')

@app.route('/')
def home(): 
    return "The Golden Whale Radar is Live and Connected to Binance!"

# --- 2. دالة التقييم الذكي ---
def get_label(val, excel, good):
    if val >= excel: return "💎 ممتاز دخول"
    if val >= good: return "✅ متوسط دخول"
    return "⚪ عادي"

# --- 3. جلب أقوى 50 عملة من باينانس ---
def get_top_symbols():
    try:
        # استخدام API باينانس الرسمي لجلب السيولة
        data = client.futures_ticker()
        top_50 = sorted(data, key=lambda x: float(x['quoteVolume']), reverse=True)[:50]
        return [s['symbol'] for s in top_50 if s['symbol'].endswith('USDT')]
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []

# --- 4. وظيفة الفحص المتقدمة للسيولة والحيتان ---
def analyze_market(symbol):
    try:
        # جلب الشموع (15 دقيقة)
        klines = client.futures_klines(symbol=symbol, interval='15m', limit=60)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        df['c'] = df['c'].astype(float)
        df['v'] = df['v'].astype(float)

        # حساب RSI
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)).iloc[-1]))

        # بيانات العقود والتمويل (Funding Rate)
        funding_info = client.futures_funding_rate(symbol=symbol, limit=1)
        funding = float(funding_info[0]['fundingRate']) * 100

        # فحص انفجار السيولة
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
                f"📊 قوة السيولة: {get_label(vol_ratio, 3.0, 1.5)}\n"
                f"💰 التمويل: {funding:.4f}% {'💎' if funding < 0 else '✅'}\n"
                f"📉 وضع CVD: {status}\n"
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
                f"📊 قوة السيولة: {get_label(vol_ratio, 3.0, 1.5)}\n"
                f"💰 التمويل: {funding:.4f}% {'💎' if funding > 0.01 else '✅'}\n"
                f"📈 نت دلتا بيع: {get_label(vol_ratio, 2.5, 1.2)}\n"
            )
            send_telegram(msg)
    except:
        pass

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main_loop():
    while True:
        symbols = get_top_symbols()
        # فحص متعدد الخيوط (Multithreading) لفحص 50 عملة بسرعة
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(analyze_market, symbols)
        time.sleep(120) # فحص كل دقيقتين

if __name__ == "__main__":
    # تشغيل سيرفر Flask في الخلفية
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    main_loop()
