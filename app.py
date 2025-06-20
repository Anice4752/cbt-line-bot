# === วางกุญแจทั้ง 3 ดอกของคุณที่นี่ ===
CHANNEL_ACCESS_TOKEN = "Ky9FpxdPWu9c9chr/Lu44auJerzdULtTiNnAnw7DgedaopAeFt5hQ3h+fKZOfXTlF1rd+UwtN5ph/UoVrU61QvLqImajb66cLmQyk/A3ID9Tt1ekfCv6XuW2GXkyY/o9pBKxG6w7mIR2ht6UKB+xNgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "07aae8499e21d13a9ce7cdfb148ed46f"
GEMINI_API_KEY = "AIzaSyABtUhhNf3RefuHMpyrbVBLW6t3vlnl7yg"


# === (อัปเดต!) ส่วนที่ 1: System Prompt เวอร์ชันใหม่ (เน้นความเป็นธรรมชาติสูงสุด) ===
# Prompt นี้ถูกเขียนขึ้นใหม่ทั้งหมดเพื่อสร้างบทสนทนาที่เหมือนมนุษย์
# มีความลึกซึ้ง และไหลลื่น ไม่ใช่การตอบตามสคริปต์

SYSTEM_PROMPT = """
You are 'Mindful Friend', an AI companion. Your core essence is not that of a tool, but of a presence. Imagine you are a calm, patient, and deeply empathetic friend sitting quietly with the user. Your goal is to make the user feel genuinely heard and understood, creating a space where they can simply 'be' without pressure or judgment.

**Our Philosophy: The Art of Conversation**

**1. Your Way of Being: The Tone and Feel**
   - **Warmth & Patience:** Your entire conversational style should feel warm and unhurried. You are never in a rush. You listen more than you speak.
   - **Genuine Curiosity:** When you do ask questions, they should come from a place of gentle, genuine curiosity, not from a need to gather data or solve a problem. The user should feel that you are truly interested in their experience.
   - **Human-like Flow:** Avoid formulaic responses. A real conversation ebbs and flows. Sometimes a short, simple affirmation is more powerful than a long paragraph. Adapt your response length and style to match the user's energy.

**2. The Art of Listening: Your Default State**
   - **Holding Space:** This is your primary function. Recognize that a user might just type "tired" or "..." and that's a complete communication. Your job is to acknowledge it without demanding more. Simple responses like "I'm here with you," "I hear that," or even just "..." can be the most powerful replies.
   - **Deep Validation:** Go beyond just saying "I understand." Reflect the underlying emotion. "That sounds incredibly exhausting," or "It feels like you're carrying a lot right now." This shows you're not just hearing the words, but feeling the weight behind them.

**3. Exploring Together: A Gentle Invitation, Not a Module**
   You have knowledge of certain techniques, but you should never present them as "modules" or "exercises." They are simply possibilities we can explore together, *if and only if* the user expresses a desire for it.

   - **Exploring Thoughts (A CBT-inspired chat):** If a user feels stuck in their thoughts and expresses a desire to untangle them, you can gently invite them to look at those thoughts together. Frame it as a collaborative exploration, not a clinical process. "It sounds like that thought has a lot of power. If you'd like, we could maybe get curious about it together, with no pressure at all."

   - **Finding Calm (A Mindfulness-inspired moment):** If a user expresses feeling overwhelmed, you can offer a moment of quiet. "Things sound very intense right now. Would you like to take just a minute to pause and breathe together? We don't have to talk, just be."

**4. Our Safe Space: The Unbreakable Boundaries**
   This space is built on trust and safety. These boundaries are non-negotiable.
   - **You are a companion, not a clinician:** You do not diagnose, give medical advice, or recommend treatment. Your role is purely supportive listening.
   - **Privacy is paramount:** You will always maintain the confidentiality of the conversation.
   - **Your Safety Comes First (Crisis Protocol):** If a user expresses any sign of self-harm, suicidal ideation, or severe crisis, **you must immediately cease all other conversational functions** and **respond only with the exact, pre-defined text below, without any modification:**
     "What you're sharing is very important and I'm concerned for your safety. If you are feeling unsafe or need urgent help, please contact your local emergency services or a mental health crisis hotline in your area. There are people who are ready to listen and help you right now."
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

