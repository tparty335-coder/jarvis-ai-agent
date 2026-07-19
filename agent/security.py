"""
security.py
-----------
طبقة حماية تقنية، مش مجرد تعليمات للموديل يلتزم بيها. الفرق مهم:
لو حطينا القاعدة في system_prompt بس، وموديل بعيد (أو prompt injection
من محتوى خارجي زي إيميل ضار) خلّى الوكيل "ينسى" القاعدة، مفيش حاجة
تمنعه فعليًا. الكود هنا بيمنع فعليًا بغض النظر عن قرار الموديل.

الاستخدام الحالي: فلترة أي محاولة لحفظ بيانات مالية حساسة في الذاكرة
الدائمة (remember tool)، بغض النظر عن نية الطلب.
"""

import re

# أنماط شائعة لبيانات مالية حساسة. القائمة دي مش شاملة 100% (مفيش فلتر
# نصي هيكون كذلك)، لكنها بتغطي الحالات الأكتر شيوعًا وبتضيف طبقة حماية
# حقيقية فوق قاعدة الـ system prompt.
#
# ملاحظة مهمة بعد المراجعة: النمط الأول كان في الأصل بيطابق أي رقم
# متتابع من 13-19 خانة (بمسافات أو شرط اختياريين)، وده كان بيرفض غلط
# أرقام عادية تمامًا زي أرقام تتبع الشحنات أو التليفونات الطويلة. النمط
# الجديد بيطلب تحديدًا الشكل المعروف لأرقام بطاقات الائتمان: مجموعات من
# 4 أرقام (زي 4111 1111 1111 1111) أو 16 رقم متلاصقين بالظبط، مش أي رقم
# طويل عشوائي.
_FINANCIAL_PATTERNS = [
    re.compile(r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,4}\b"),  # شكل بطاقة مقسّم لمجموعات 4-4-4
    re.compile(r"\b\d{16}\b"),                                # 16 رقم متلاصقين (شكل بطاقة شائع)
    re.compile(r"\bcvv\b", re.IGNORECASE),                     # كلمة CVV
    re.compile(r"\b\d{3,4}\b.{0,10}\bcvv\b", re.IGNORECASE),
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),           # نمط IBAN
    re.compile(r"رقم\s*(?:حساب|الحساب|بطاقة|الكارت)"),
    re.compile(r"كلمة\s*(?:سر|المرور)"),
    re.compile(r"\botp\b", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
]

FINANCIAL_KEYWORDS_AR = [
    "تحويل فلوس", "تحويل مبلغ", "ادفع", "دفع", "شراء بالبطاقة",
    "بيتكوين", "محفظة رقمية", "حساب بنكي",
]


def contains_financial_data(text: str) -> bool:
    """بيفحص نص معين ويرجع True لو فيه إشارة قوية لبيانات مالية حساسة."""
    if not text:
        return False
    for pattern in _FINANCIAL_PATTERNS:
        if pattern.search(text):
            return True
    return False


def is_financial_action_request(text: str) -> bool:
    """بيفحص هل النص بيطلب تنفيذ فعل مالي (مش مجرد ذكر رقم)."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in FINANCIAL_KEYWORDS_AR)
