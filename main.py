import os
from flask import Flask, request
from binance.client import Client
import requests

app = Flask(__name__)

# --- إعدادات الحساب (ضعها في Render Environment Variables) ---
BINANCE_API_KEY = os.getenv("XaDvU5yfRLk6cOFtLPmKhUnfGe9LO5c85EGY84gWLyDuwvRn4NbghLUlCdzDh4eT")
BINANCE_SECRET_KEY = os.getenv("jO7OYkZ1Am2QXRxUtZpdZd5qazFD5OFXh1ZkrUAwYYUjUauQZeBWaCFoZYekKD2V")
TELEGRAM_TOKEN = os.getenv("8393656924:AAEdgUPLXXS6bEQWphnmDAQiz_mfsnYO6KI")
CHAT_ID = os.getenv("8393656924")

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
