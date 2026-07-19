#!/usr/bin/env python3
"""
cli.py
------
واجهة سطر أوامر بسيطة للمحادثة مع Jarvis. دي مجرد "غلاف" فوق الـ
JarvisAgent، مفيش أي منطق ذكاء هنا خالص - كل المنطق في agent/core.py.

لما تحب تضيف واجهة تانية (تليجرام، واتساب، صوت)، هتعمل ملف زي ده بالظبط
بيستدعي agent.run_turn() ويوصل الرد للقناة المناسبة، مش هتلمس core.py.

التشغيل:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python cli.py
"""

import sys

# إصلاح مشكلة عرض العربي على ويندوز: Command Prompt بيستخدم ترميز نصوص
# قديم (codepage) بشكل افتراضي، وده بيخرب أي نص عربي بيتطبع. السطرين
# دول بيجبروا بايثون يستخدم UTF-8 في الإدخال والإخراج بغض النظر عن
# إعدادات الترمينال نفسه - حل تقني مباشر بدل ما نعتمد على المستخدم
# يظبط إعدادات الترمينال يدويًا.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

from agent.core import JarvisAgent
from agent.config import settings


def main() -> None:
    try:
        agent = JarvisAgent()
    except RuntimeError as exc:
        print(f"خطأ في الإعداد: {exc}")
        sys.exit(1)

    print("I am your friend Jarvis. How can I help you, my friend?")
    print(f"(اكتب 'exit' أو 'خروج' للخروج)")

    while True:
        try:
            user_input = input("أنت: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nمع السلامة.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "خروج"}:
            print("مع السلامة.")
            break

        reply = agent.run_turn(user_input)
        print(f"{settings.agent_name}: {reply}\n")


if __name__ == "__main__":
    main()
