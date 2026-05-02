import os
from flask import Flask, request
from binance.client import Client
import requests

app = Flask(__name__)

# --- إعدادات الحساب (ضعها في Render Environment Variables) ---
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ربط باينانس
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # التوقعات من TradingView: {"symbol": "BTCUSDT", "side": "BUY", "amount": 0.001}
    symbol = data.get('symbol')
    side = data.get('side')
    amount = data.get('amount')

    try:
        if side == "BUY":
            order = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=amount)
        else:
            order = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=amount)
        
        send_telegram(f"🚀 تمت تنفيذ صفقة {side} على {symbol} بمقدار {amount}")
    except Exception as e:
        send_telegram(f"⚠️ خطأ في تنفيذ الصفقة: {str(e)}")
    
    return "OK", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
