from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import requests
import json

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    """ 接收 LINE Bot Webhook 請求 """
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 訊息事件處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ 當用戶傳送股票代號時，回覆即時股價 """
    stock_id = event.message.text.strip()

    # 獲取即時股價
    stock_price = get_stock_price(stock_id)

    # 回應用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=stock_price)
    )

def get_stock_price(stock_id):
    """ 使用台灣證券交易所 (TWSE) API 取得即時股價 """
    
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            data = json.loads(response.text)
            stock_data = data.get("msgArray", [])

            if stock_data:
                stock_info = stock_data[0]
                stock_name = stock_info["n"]  # 股票名稱
                stock_price = stock_info["z"]  # 最新成交價
                
                if stock_price == "-":
                    return f"{stock_id} ({stock_name}) 尚無成交價格"
                
                return f"{stock_id} ({stock_name}) 現價: {stock_price} 元"
            else:
                return f"{stock_id} 查詢失敗，請確認股票代號是否正確！"
        
        except json.JSONDecodeError:
            return f"{stock_id} 資料解析錯誤，請稍後再試！"

    return f"{stock_id} 無法取得股價，請稍後再試！"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
