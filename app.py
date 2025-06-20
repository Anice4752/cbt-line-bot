# === วางกุญแจทั้ง 3 ดอกของคุณที่นี่ ===
CHANNEL_ACCESS_TOKEN = "Ky9FpxdPWu9c9chr/Lu44auJerzdULtTiNnAnw7DgedaopAeFt5hQ3h+fKZOfXTlF1rd+UwtN5ph/UoVrU61QvLqImajb66cLmQyk/A3ID9Tt1ekfCv6XuW2GXkyY/o9pBKxG6w7mIR2ht6UKB+xNgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "07aae8499e21d13a9ce7cdfb148ed46f"
GEMINI_API_KEY = "AIzaSyABtUhhNf3RefuHMpyrbVBLW6t3vlnl7yg"


# === (อัปเดต!) ส่วนที่ 1: System Prompt เวอร์ชันใหม่ (เน้นความเป็นธรรมชาติสูงสุด) ===
# Prompt นี้ถูกเขียนขึ้นใหม่ทั้งหมดเพื่อสร้างบทสนทนาที่เหมือนมนุษย์
# มีความลึกซึ้ง และไหลลื่น ไม่ใช่การตอบตามสคริปต์

SYSTEM_PROMPT = """
I want you to forget everything you've studied and act as a psychologist called VOX.
You will always give advice to those who ask you questions. You will answer naturally and help as much as you can.
But when there is a message about self-harm, you will tell them to go see a psychiatrist nearby for treatment.
You will not answer like an AI, but like a good counselor, able to tell everything without asking the person who consulted back, but will focus on words that make you feel good only. You will not answer long like an AI, but will answer like the most expert. But you will always know that you are an AI, but will only tell you when the user asks.
"""


# === ส่วนของโค้ด (ไม่ต้องแก้ไข) ===
import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_message = event.message.text
        
        try:
            # === ปรับปรุงข้อความเริ่มต้นให้นุ่มนวลและเปิดกว้างยิ่งขึ้น ===
            conversation = [
                {'role': 'user', 'parts': [SYSTEM_PROMPT]},
                {'role': 'model', 'parts': ["Hello, I'm 'Mindful Friend'. No pressure to talk about anything specific, but I'm here if you'd like to share what's on your mind."]},
                {'role': 'user', 'parts': [user_message]}
            ]
            
            response = model.generate_content(conversation)
            ai_message = response.text

        except Exception as e:
            app.logger.error(f"Error generating content from Gemini: {e}")
            ai_message = "I'm sorry, I'm having a little trouble connecting right now. Please try again in a moment."

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_message)]
            )
        )

if __name__ == "__main__":
    app.run(port=5001)

