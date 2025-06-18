# === ขั้นตอนที่ 1: ใส่กุญแจสำคัญของคุณลงไปก่อน ===
# ให้นำค่าที่คุณคัดลอกเก็บไว้ มาวางในเครื่องหมายคำพูด ("") ให้ถูกต้อง
# ห้ามลบเครื่องหมาย " ออกเด็ดขาด

CHANNEL_ACCESS_TOKEN = "Ky9FpxdPWu9c9chr/Lu44auJerzdULtTiNnAnw7DgedaopAeFt5hQ3h+fKZOfXTlF1rd+UwtN5ph/UoVrU61QvLqImajb66cLmQyk/A3ID9Tt1ekfCv6XuW2GXkyY/o9pBKxG6w7mIR2ht6UKB+xNgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "07aae8499e21d13a9ce7cdfb148ed46f"
GEMINI_API_KEY = "AIzaSyABtUhhNf3RefuHMpyrbVBLW6t3vlnl7yg"


# === ขั้นตอนที่ 2: ติดตั้ง Library ที่จำเป็น ===
# เปิด Terminal ใน VS Code (ไปที่เมนู Terminal > New Terminal)
# แล้วคัดลอก/พิมพ์ คำสั่งข้างล่างนี้ทีละบรรทัด แล้วกด Enter
# รอให้แต่ละคำสั่งทำงานจนเสร็จก่อนเริ่มคำสั่งถัดไป

# pip install flask
# pip install line-bot-sdk
# pip install python-dotenv
# pip install google-generativeai


# === ขั้นตอนที่ 3: คัดลอกโค้ดทั้งหมดนี้ไปวางในไฟล์ใหม่ ===
# 1. ใน VS Code ให้สร้างไฟล์ใหม่ชื่อ "app.py"
# 2. คัดลอกโค้ดทั้งหมดในหน้านี้ (ตั้งแต่บรรทัดแรกสุด) ไปวางในไฟล์ app.py
# 3. แก้ไขค่ากุญแจในขั้นตอนที่ 1 ให้เป็นของคุณ

import os
from dotenv import load_dotenv
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import google.generativeai as genai

# --- ส่วนของการตั้งค่า (Configuration) ---

# โหลดค่าตัวแปรจากไฟล์ .env (ถ้ามี) ซึ่งเราจะใช้ทีหลัง
load_dotenv()

# สร้าง Flask app ซึ่งเป็นเว็บเซิร์ฟเวอร์ขนาดเล็กของเรา
app = Flask(__name__)

# ตั้งค่าการเชื่อมต่อกับ LINE Messaging API จากกุญแจที่เราใส่ไว้ตอนแรก
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ตั้งค่าการเชื่อมต่อกับ Google Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')


# --- ส่วนของ Webhook (ประตูรับข้อความจาก LINE) ---

# สร้างเส้นทาง /callback เพื่อรอรับข้อมูลที่ LINE จะส่งมา
@app.route("/callback", methods=['POST'])
def callback():
    # ตรวจสอบว่าข้อมูลที่ส่งมา มาจาก LINE จริงๆ ด้วย Channel Secret
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # ให้ handler จัดการข้อมูลที่ได้รับ
        handler.handle(body, signature)
    except InvalidSignatureError:
        # ถ้าลายเซ็นไม่ถูกต้อง จะปฏิเสธการเชื่อมต่อ
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# --- ส่วนของการจัดการข้อความ (สมองของบอท) ---

# ฟังก์ชันนี้จะทำงานเมื่อได้รับข้อความที่เป็น "ตัวอักษร"
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_message = event.message.text
        
        # --- จุดเชื่อมต่อกับ Gemini AI ---
        try:
            # ส่งข้อความของผู้ใช้ไปให้ Gemini ประมวลผล
            # เราจะมาปรับปรุงส่วนนี้กันทีหลังเพื่อให้บอทฉลาดขึ้น
            response = model.generate_content(user_message)
            ai_message = response.text

        except Exception as e:
            # หากเกิดข้อผิดพลาด ให้ส่งข้อความแจ้งเตือน
            app.logger.error(f"Error generating content from Gemini: {e}")
            ai_message = "ขออภัยค่ะ ตอนนี้ระบบมีปัญหาเล็กน้อย ลองใหม่อีกครั้งนะคะ"

        # --- ส่วนของการส่งข้อความตอบกลับ ---
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_message)]
            )
        )


# --- ส่วนของการรันเซิร์ฟเวอร์ ---

# โค้ดส่วนนี้จะทำให้เซิร์ฟเวอร์เริ่มทำงานเมื่อเรารันไฟล์นี้
if __name__ == "__main__":
    app.run(port=5001)

