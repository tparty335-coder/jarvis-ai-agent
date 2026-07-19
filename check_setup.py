#!/usr/bin/env python3
"""
check_setup.py
--------------
سكريبت تشخيصي واحد يفحص كل مكوّن في المشروع ويديك تقرير واضح:
إيه الشغال، إيه الناقص، وإيه بالظبط لازم تعمله عشان تكمل.

الفكرة: بدل ما تكتشف إن مكتبة ناقصة أو مفتاح مش متحدد لما البرنامج
يوقع فجأة في نص المحادثة، تشغّل السكريبت ده الأول وتاخد الصورة كاملة.

التشغيل:
    python check_setup.py
"""

import importlib.util
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CHECK_MARK = "✅"
CROSS_MARK = "❌"
WARN_MARK = "⚠️ "


def check_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def report(ok: bool, label: str, fix_hint: str = "") -> None:
    mark = CHECK_MARK if ok else CROSS_MARK
    print(f"  {mark} {label}")
    if not ok and fix_hint:
        print(f"      → {fix_hint}")


def main() -> None:
    print("جاري فحص جاهزية Jarvis Agent...")

    # ---------- الأساسيات ----------
    section("الأساسيات (لازم تكون شغالة عشان أي حاجة تشتغل)")

    has_anthropic = check_module("anthropic")
    report(has_anthropic, "مكتبة anthropic متثبتة", "pip install -r requirements-core.txt")

    has_httpx = check_module("httpx")
    report(has_httpx, "مكتبة httpx متثبتة", "pip install -r requirements-core.txt")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    report(bool(api_key), "متغير ANTHROPIC_API_KEY محدد", "export ANTHROPIC_API_KEY='sk-ant-...'")

    core_ready = has_anthropic and has_httpx and bool(api_key)
    if core_ready:
        print(f"\n  {CHECK_MARK} الأساسيات جاهزة - cli.py هيشتغل.")
    else:
        print(f"\n  {CROSS_MARK} الأساسيات ناقصة - المشروع مش هيشتغل خالص من غيرها.")

    # ---------- Gmail ----------
    section("Gmail")
    has_gmail_libs = all(
        check_module(m) for m in ["googleapiclient", "google_auth_oauthlib", "google.auth"]
    )
    report(has_gmail_libs, "مكتبات Gmail متثبتة", "pip install -r requirements-gmail.txt")

    creds_path = DATA_DIR / "credentials.json"
    report(creds_path.exists(), f"ملف credentials.json موجود في data/", "راجع خطوات إعداد Gmail في README.md")

    token_path = DATA_DIR / "gmail_token.json"
    if token_path.exists():
        print(f"  {CHECK_MARK} فيه توكن مخزّن بالفعل (تم تسجيل الدخول قبل كده)")
    else:
        print(f"  {WARN_MARK}أول استخدام لأداة Gmail هيفتح المتصفح لتسجيل الدخول")

    # ---------- تليجرام ----------
    section("بوت تليجرام")
    has_telegram_lib = check_module("telegram")
    report(has_telegram_lib, "مكتبة python-telegram-bot متثبتة", "pip install -r requirements-telegram.txt")
    report(bool(os.environ.get("TELEGRAM_BOT_TOKEN")), "متغير TELEGRAM_BOT_TOKEN محدد")
    allowed_chat = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "")
    if allowed_chat:
        print(f"  {CHECK_MARK} TELEGRAM_ALLOWED_CHAT_ID محدد (البوت محمي)")
    elif os.environ.get("TELEGRAM_BOT_TOKEN"):
        print(f"  {WARN_MARK}TELEGRAM_ALLOWED_CHAT_ID مش محدد - البوت هيرد على أي حد لو شغّلته كده!")

    # ---------- الأوفيس ----------
    section("حزمة الأوفيس (Word / Excel / PowerPoint)")
    report(check_module("docx"), "python-docx متثبتة (Word)", "pip install -r requirements-office.txt")
    report(check_module("openpyxl"), "openpyxl متثبتة (Excel)", "pip install -r requirements-office.txt")
    report(check_module("pptx"), "python-pptx متثبتة (PowerPoint)", "pip install -r requirements-office.txt")

    # ---------- الصور ----------
    section("تعديل الصور")
    report(check_module("PIL"), "Pillow متثبتة", "pip install -r requirements-images.txt")

    # ---------- تنظيم الملفات ----------
    section("تنظيم وفهرسة الملفات")
    report(check_module("send2trash"), "send2trash متثبتة (لنقل الملفات لسلة المهملات بأمان)", "pip install -r requirements-files.txt")

    # ---------- النظام ----------
    section("التحكم في النظام (إغلاق + طابعة)")
    import platform
    print(f"  {CHECK_MARK} نظام التشغيل المكتشف: {platform.system()} (مفيش متطلبات إضافية)")

    # ---------- الملخص ----------
    section("الملخص")
    if core_ready:
        print(f"  {CHECK_MARK} تقدر تشغّل: python cli.py")
    else:
        print(f"  {CROSS_MARK} لازم تظبط الأساسيات الأول قبل أي حاجة تانية.")

    print("\nراجع README.md لتفاصيل إعداد أي تكامل ناقص.")


if __name__ == "__main__":
    main()
