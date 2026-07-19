"""
gmail_tool.py
-------------
تكامل رسمي 100% مع Gmail عن طريق Google API - مفيش أي مكتبة غير رسمية
أو محاكاة تسجيل دخول، عشان الحساب متتحظرش وعشان الطريقة دي مدعومة
ومستقرة على المدى الطويل.

## خطوات الإعداد (مرة واحدة بس):

1. روح على https://console.cloud.google.com/
2. اعمل مشروع جديد (أو استخدم موجود)
3. من "APIs & Services" > "Library"، فعّل "Gmail API"
4. من "APIs & Services" > "Credentials"، اعمل "OAuth client ID" من نوع
   "Desktop app"
5. نزّل ملف الـ JSON بتاع الـ credentials، وسمّيه credentials.json
   وحطه في مجلد data/ جوه المشروع
6. أول مرة تشغّل أي أداة من دول، هيفتحلك المتصفح تسجل دخول وتوافق
   على الصلاحيات - ده هيحصل مرة واحدة بس، وبعدها التوكن بيتخزن محليًا

## نطاق الصلاحيات المطلوب (Scope):
gmail.modify يسمح بالقراءة والأرشفة والحذف والتصنيف، لكن مش بالحذف
النهائي الفوري (بيروح للسلة أولاً، زي أي حذف يدوي عادي) - ده مقصود
كطبقة أمان إضافية.
"""

import os
from pathlib import Path
from typing import Optional

from ..config import DATA_DIR

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_PATH = DATA_DIR / "credentials.json"
TOKEN_PATH = DATA_DIR / "gmail_token.json"

_service = None  # كاش للاتصال عشان منعملش OAuth handshake في كل استدعاء


def _get_service():
    global _service
    if _service is not None:
        return _service

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "مكتبات جوجل مش متثبتة. شغّل: pip install google-api-python-client "
            "google-auth-httplib2 google-auth-oauthlib"
        ) from exc

    creds: Optional[Credentials] = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise RuntimeError(
                    f"ملف الاعتماد مش موجود في {CREDENTIALS_PATH}. "
                    "اتبع خطوات الإعداد في أعلى الملف ده."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    _service = build("gmail", "v1", credentials=creds)
    return _service


def _extract_headers(message: dict) -> dict:
    headers = message.get("payload", {}).get("headers", [])
    wanted = {"From", "Subject", "Date"}
    return {h["name"]: h["value"] for h in headers if h["name"] in wanted}


def gmail_search(query: str, max_results: int = 15) -> str:
    """يبحث في جيميل بنفس صيغة البحث بتاعت جيميل نفسها.
    أمثلة: 'is:unread', 'category:promotions older_than:30d',
            'from:noreply older_than:7d'"""
    try:
        service = _get_service()
        result = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = result.get("messages", [])
        if not messages:
            return "مفيش رسايل مطابقة."

        lines = []
        for m in messages:
            full = service.users().messages().get(
                userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = _extract_headers(full)
            snippet = full.get("snippet", "")[:80]
            lines.append(
                f"ID: {m['id']} | من: {headers.get('From', '?')} | "
                f"الموضوع: {headers.get('Subject', '?')} | {snippet}"
            )
        return "\n".join(lines)
    except Exception as exc:
        return f"خطأ في البحث في جيميل: {exc}"


def gmail_archive(message_id: str) -> str:
    """يشيل الرسالة من الـ Inbox من غير حذفها (Archive)."""
    try:
        service = _get_service()
        service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
        ).execute()
        return f"تم أرشفة الرسالة {message_id}."
    except Exception as exc:
        return f"خطأ في الأرشفة: {exc}"


def gmail_trash(message_id: str) -> str:
    """يحط الرسالة في سلة المهملات (مش حذف نهائي، ممكن استرجاعها خلال 30 يوم)."""
    try:
        service = _get_service()
        service.users().messages().trash(userId="me", id=message_id).execute()
        return f"تم نقل الرسالة {message_id} لسلة المهملات."
    except Exception as exc:
        return f"خطأ في نقل الرسالة للمهملات: {exc}"


def gmail_bulk_clean(query: str, action: str = "trash", max_results: int = 50, confirmed: bool = False) -> str:
    """يطبّق إجراء (trash/archive) على كل الرسايل المطابقة لاستعلام معين
    دفعة واحدة. ده الأداة الأساسية لـ 'نظّفلي الإيميل من الرسايل الفاضية'.

    مهم (تحديث بعد المراجعة): قبل كده كانت الحماية هنا معتمدة بالكامل على
    التزام الموديل بقاعدة "اعرض واستنى تأكيد" المكتوبة في system_prompt -
    يعني نفس المشكلة اللي حليناها مع shutdown_computer (حماية سلوكية بس،
    مش كودية). دلوقتي الأداة نفسها بترفض تنفذ فعليًا على أكتر من 5 رسائل
    من غير confirmed=True صريح، بغض النظر عن قرار الموديل."""
    if action == "trash" and max_results > 5 and not confirmed:
        preview = gmail_search(query, max_results=min(max_results, 10))
        return (
            f"تم رفض التنفيذ المباشر: الطلب ده هيأثر على عدد كبير من الرسائل "
            f"({max_results} كحد أقصى) بإجراء trash. اعرض النتائج دي للمستخدم الأول:\n\n"
            f"{preview}\n\n"
            "وبعد موافقته الصريحة، استدعي الأداة تاني بنفس الباراميترات مع confirmed=True."
        )

    try:
        service = _get_service()
        result = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = result.get("messages", [])
        if not messages:
            return "مفيش رسايل مطابقة للتنظيف."

        count = 0
        for m in messages:
            if action == "trash":
                service.users().messages().trash(userId="me", id=m["id"]).execute()
            elif action == "archive":
                service.users().messages().modify(
                    userId="me", id=m["id"], body={"removeLabelIds": ["INBOX"]}
                ).execute()
            else:
                return f"إجراء غير معروف: {action}. استخدم 'trash' أو 'archive'."
            count += 1

        action_ar = "نقل لسلة المهملات" if action == "trash" else "أرشفة"
        return f"تم {action_ar} {count} رسالة مطابقة لـ: {query}"
    except Exception as exc:
        return f"خطأ في التنظيف الجماعي: {exc}"


SEARCH_SCHEMA = {
    "name": "gmail_search",
    "description": "يبحث في صندوق جيميل بصيغة بحث جيميل القياسية، ويرجع قائمة بالرسائل المطابقة مع IDs.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "استعلام بصيغة جيميل، مثال: 'category:promotions older_than:30d'"},
            "max_results": {"type": "integer", "description": "أقصى عدد نتائج، افتراضيًا 15"},
        },
        "required": ["query"],
    },
}

ARCHIVE_SCHEMA = {
    "name": "gmail_archive",
    "description": "يؤرشف رسالة واحدة محددة بالـ ID (يشيلها من Inbox من غير حذف).",
    "input_schema": {
        "type": "object",
        "properties": {"message_id": {"type": "string", "description": "ID الرسالة"}},
        "required": ["message_id"],
    },
}

TRASH_SCHEMA = {
    "name": "gmail_trash",
    "description": "ينقل رسالة واحدة محددة بالـ ID لسلة المهملات (قابلة للاسترجاع).",
    "input_schema": {
        "type": "object",
        "properties": {"message_id": {"type": "string", "description": "ID الرسالة"}},
        "required": ["message_id"],
    },
}

BULK_CLEAN_SCHEMA = {
    "name": "gmail_bulk_clean",
    "description": (
        "يطبّق أرشفة أو نقل-لسلة-المهملات على كل الرسائل المطابقة لاستعلام معين دفعة واحدة. "
        "استخدمها بعد ما تتأكد بـ gmail_search من الرسائل المستهدفة. لو action='trash' وعدد "
        "الرسائل أكبر من 5، لازم تستدعيها الأول من غير confirmed (هترجع معاينة)، تعرضها "
        "للمستخدم، وبعد موافقته الصريحة تستدعيها تاني بـ confirmed=True."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "استعلام بصيغة جيميل يحدد الرسائل المستهدفة"},
            "action": {"type": "string", "enum": ["trash", "archive"], "description": "الإجراء المطلوب"},
            "max_results": {"type": "integer", "description": "أقصى عدد رسائل يتم التعامل معها، افتراضيًا 50"},
            "confirmed": {"type": "boolean", "description": "لازم true للتنفيذ الفعلي لو أكتر من 5 رسائل بإجراء trash"},
        },
        "required": ["query", "action"],
    },
}
