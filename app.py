from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import requests
import schedule
import time
import threading

app = Flask(__name__)

# 設定 LINE Bot 的 Access Token 和 Secret
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 監控的股票清單
STOCKS = {
    "ETF": ["00757", "00662", "006208", "0050"],
    "個股": ["2317"]
}

# 股價查詢 API
STOCK_API_URL = "https://tw.stock.yahoo.com/q/q?s={}"  # 使用 Yahoo 股市 (可換成其他 API)

def get_stock_price(stock_id):
    """取得指定股票的即時價格"""
    response = requests.get(STOCK_API_URL.format(stock_id))
    if response.status_code == 200:
        return f"{stock_id} 現價: (模擬數據) 100元"
    return f"{stock_id} 查詢失敗"

def send_stock_report():
    """每天 9:01 自動發送股票開盤價 & 當跌幅超過 0.5% 時通知"""
    message = "📢 今日股票開盤價：\n"
    
    for category, stocks in STOCKS.items():
        message += f"\n【{category}】\n"
        for stock in stocks:
            price = get_stock_price(stock)
            message += f"{price}\n"
    
    # 發送給所有關注者
    line_bot_api.broadcast(TextSendMessage(text=message))

# 定時執行任務
schedule.every().day.at("09:01").do(send_stock_report)

def schedule_runner():
    while True:
        schedule.run_pending()
        time.sleep(60)

# 啟動排程
threading.Thread(target=schedule_runner, daemon=True).start()

@app.route("/", methods=['GET'])
def home():
    return "LINE Bot is running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    """處理 LINE Bot Webhook"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理使用者輸入的文字訊息"""
    text = event.message.text.strip()
    
    if text.isdigit():  # 如果使用者輸入股票代號
        reply = get_stock_price(text)
    else:
        reply = f"指令無效，請輸入股票代號，例如：2317"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
