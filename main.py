import os
import requests
from flask import Flask, request
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

# ========================================================
# 1. إعدادات الوصول (أدخل بياناتك هنا)
# ========================================================
# يُفضل وضع هذه البيانات في Environment Variables على Render
BINANCE_API_KEY = os.getenv("XaDvU5yfRLk6cOFtLPmKhUnfGe9LO5c85EGY84gWLyDuwvRn4NbghLUlCdzDh4eT") or "ضع_API_KEY_هنا"
BINANCE_SECRET_KEY = os.getenv("jO7OYkZ1Am2QXRxUtZpdZd5qazFD5OFXh1ZkrUAwYYUjUauQZeBWaCFoZYekKD2V") or "ضع_SECRET_KEY_هنا"
TELEGRAM_TOKEN = os.getenv("8393656924:AAEdgUPLXXS6bEQWphnmDAQiz_mfsnYO6KI") or "ضع_توكن_التيليجرام_هنا"
CHAT_ID = os.getenv("8393656924") or "ضع_الأيدي_هنا"

# ربط حساب باينانس
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
# ========================================================

def send_telegram_msg(message):
    """دالة لإرسال التنبيهات إلى تيليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

@app.route('/')
def home():
    return "Binance Bot is Live!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال الإشارات من TradingView وتنفيذها"""
    try:
        data = request.json
        symbol = data.get('symbol') # مثل BTCUSDT
        side = data.get('side')     # BUY أو SELL
        quantity = data.get('qty')  # الكمية

        # تنفيذ أمر سوق (Market Order) في الفيوتشرز
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )

        log_msg = f"🚀 **تم تنفيذ صفقة بنجاح!**\n\n" \
                  f"🔹 العملة: {symbol}\n" \
                  f"🔹 النوع: {side}\n" \
                  f"🔹 الكمية: {quantity}"
        send_telegram_msg(log_msg)
        return {"status": "success", "order": str(order)}, 200

    except Exception as e:
        error_msg = f"⚠️ **فشل في تنفيذ الصفقة**\nالسبب: {str(e)}"
        send_telegram_msg(error_msg)
        return {"status": "error", "message": str(e)}, 400

if __name__ == "__main__":
    # تشغيل السيرفر على المنفذ 10000 المخصص لـ Render
    app.run(host='0.0.0.0', port=10000)
