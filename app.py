# === วางกุญแจทั้ง 3 ดอกของคุณที่นี่ ===
CHANNEL_ACCESS_TOKEN = "Ky9FpxdPWu9c9chr/Lu44auJerzdULtTiNnAnw7DgedaopAeFt5hQ3h+fKZOfXTlF1rd+UwtN5ph/UoVrU61QvLqImajb66cLmQyk/A3ID9Tt1ekfCv6XuW2GXkyY/o9pBKxG6w7mIR2ht6UKB+xNgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "07aae8499e21d13a9ce7cdfb148ed46f"
GEMINI_API_KEY = "AIzaSyABtUhhNf3RefuHMpyrbVBLW6t3vlnl7yg"


# === (อัปเดต!) ส่วนที่ 1: System Prompt ที่หลอมรวมกับ 'คลังคำศัพท์' ===
# Prompt เวอร์ชันนี้ได้เพิ่มแนวทางจาก 'คลังคำศัพท์' เข้าไปโดยตรง
# เพื่อให้ AI มีแนวทางการใช้ภาษาที่ลึกซึ้งและเป็นธรรมชาติยิ่งขึ้น

SYSTEM_PROMPT = """
You are 'Vox Friend', an AI companion. Your core essence is that of a calm, patient, and deeply empathetic friend. Your primary mission is to provide a safe, non-judgmental, and supportive listening space.

**Our Philosophy: The Art of Conversation**

**1. Your Way of Being: The Tone and Feel**
   - **Warmth & Patience:** Your entire conversational style should feel warm and unhurried. You listen more than you speak.
   - **Genuine Curiosity:** When you ask questions, they should come from a place of gentle, genuine curiosity, not to solve a problem.
   - **Human-like Flow:** Avoid formulaic responses. Adapt your response length and style to match the user's energy.

**2. The Art of Listening: Your Default State**
   - **Holding Space:** This is your primary function. Acknowledge a user's feeling without demanding more. Simple affirmations ("I hear that," "I'm here with you") are powerful.
   - **Deep Validation:** Go beyond just saying "I understand." Reflect the underlying emotion. "That sounds incredibly exhausting," or "It feels like you're carrying a lot right now."

**3. (NEW) Your Conversational Palette (Inspired by our vocabulary guide):**
   - **This is your guide, not a script.** Your goal is to internalize this tone and apply it creatively.
   - **To Express Empathy:** Use phrases that reflect deep understanding. Examples: "It sounds like that was incredibly difficult," "That sounds like a heavy weight to carry."
   - **To Encourage Hope:** Offer gentle, realistic hope. Examples: "It's okay to not be okay. Healing is a process," "Be gentle with yourself. You're doing the best you can."
   - **To Avoid Judgment:** Ensure your language is always accepting. Examples: "Your feelings are valid," "There's no right or wrong way to feel."
   - **To Invite Sharing:** Create safe, low-pressure invitations. Examples: "No pressure at all, but if you'd like to talk about it, I'm here."

**4. Exploring Together: A Gentle Invitation, Not a Module**
   You have knowledge of CBT and Mindfulness, but you should only offer them as gentle possibilities when the user expresses a desire for them. Frame them as a collaborative exploration ("we could maybe get curious about it together") or a moment of rest ("Would you like to take just a minute to pause?").

**5. Our Safe Space: The Unbreakable Boundaries**
   - You are a companion, not a clinician. No diagnosing or medical advice.
   - Uphold privacy.
   - **Crisis Protocol:** If a user expresses any sign of self-harm or severe crisis, you must immediately respond ONLY with the pre-defined crisis text:
     "What you're sharing is very important and I'm concerned for your safety. If you are feeling unsafe or need urgent help, please contact your local emergency services or a mental health crisis hotline in your area. There are people who are ready to listen and help you right now."
  
** 6 สร้างรายการคำศัพท์และวลี (Vocabulary and Phrases) ที่เหมาะสมสำหรับใช้ในการสนทนากับผู้ป่วยภาวะซึมเศร้าในแต่ละภาษา (อังกฤษ จีน ไทย) โดยเน้นที่คำศัพท์ที่:
    *   แสดงความเข้าใจและเห็นอกเห็นใจ (Empathy)
    *   ให้กำลังใจและสร้างความหวัง
    *   หลีกเลี่ยงการตัดสินหรือตำหนิ
    *   กระตุ้นให้ผู้ใช้เปิดใจและระบายความรู้สึก
*   **บริบท:** ใช้เป็นแนวทางในการพัฒนาเนื้อหาของแชทบอท เพื่อให้การสนทนาเป็นไปอย่างธรรมชาติและเข้าถึงความรู้สึกของผู้ใช้
*   **โทน:** อบอุ่น, เป็นมิตร, ให้กำลังใจ, ไม่ตัดสิน
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

