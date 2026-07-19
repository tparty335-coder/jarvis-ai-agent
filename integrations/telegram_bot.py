"""
telegram_bot.py
---------------
بوت تليجرام كـ "واجهة" فوق JarvisAgent - نفس مبدأ cli.py بالظبط،
بس القناة هنا تليجرام بدل الترمينال، وده بيخليك تتحكم في الوكيل من
موبايلك من أي مكان.

## نقطة أمان حرجة:
البوت ده هيبقى عنده صلاحية يقرأ ويحذف إيميلاتك ويشتغل بملفاتك.
لو سبته من غير تقييد، أي حد يعرف اسم البوت في تليجرام هيقدر يكلمه
ويتحكم في حاجاتك. عشان كده لازم تحدد ALLOWED_CHAT_ID بتاعك انت بس.

## الإعداد:
1. كلّم @BotFather في تليجرام، ابعتله /newbot، هيديك TOKEN
2. كلّم البوت بتاعك أي رسالة، وبعدين افتح الرابط ده في المتصفح
   (حط التوكن بتاعك مكان TOKEN):
   https://api.telegram.org/botTOKEN/getUpdates
   هتلاقي "chat":{"id": 123456789} - ده الـ chat_id بتاعك
3. صدّر المتغيرين:
   export TELEGRAM_BOT_TOKEN="التوكن بتاعك"
   export TELEGRAM_ALLOWED_CHAT_ID="الـ chat_id بتاعك"
4. شغّل: python integrations/telegram_bot.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from agent.core import JarvisAgent
from agent.config import settings

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "")

if not BOT_TOKEN:
    print("خطأ: متغير TELEGRAM_BOT_TOKEN مش محدد.")
    sys.exit(1)

if not ALLOWED_CHAT_ID:
    print(
        "تحذير أمان: TELEGRAM_ALLOWED_CHAT_ID مش محدد. "
        "البوت هيرد على أي حد يكلمه، ده خطر لأنه عنده صلاحيات على إيميلك وملفاتك. "
        "شوف تعليمات الإعداد في أعلى الملف ده."
    )

agent = JarvisAgent()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
        return
    await update.message.reply_text("I am your friend Jarvis. How can I help you, my friend?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)

    if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
        # نتجاهل أي حد غير صاحب الحساب تمامًا - حتى مفيش رد بيدل إن البوت شغال
        return

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # run_turn بيعمل network calls بلوكينج، فبنشغّلها في thread منفصل
    # عشان منوقفش الـ event loop بتاع البوت كله وهو بيستنى الرد
    reply = await asyncio.to_thread(agent.run_turn, user_text)

    await update.message.reply_text(reply)


def main() -> None:
    print(f"=== بوت {settings.agent_name} على تليجرام شغّال... ===")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
