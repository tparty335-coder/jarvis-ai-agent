"""
files.py
--------
قراءة/كتابة ملفات، لكن محصورة داخل مجلد workspace/ فقط.
ده قرار تصميمي مقصود: أي وكيل AI عنده صلاحية كتابة ملفات لازم يكون
محدود بمساحة معروفة، عشان ميعملش تعديل في مكان حساس بالغلط أو بسبب
prompt injection من محتوى خارجي.
"""

from pathlib import Path

from ..config import BASE_DIR

WORKSPACE = BASE_DIR / "workspace"
WORKSPACE.mkdir(exist_ok=True)


def _safe_path(relative_path: str) -> Path:
    """يتأكد إن المسار النهائي لسه جوه الـ workspace ومش طالع منه بـ '../'"""
    target = (WORKSPACE / relative_path).resolve()
    if WORKSPACE.resolve() not in target.parents and target != WORKSPACE.resolve():
        raise ValueError("مش مسموح بالوصول لمسار خارج مساحة العمل (workspace)")
    return target


def read_file(relative_path: str) -> str:
    try:
        path = _safe_path(relative_path)
        if not path.exists():
            return f"الملف مش موجود: {relative_path}"
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"خطأ في قراءة الملف: {exc}"


def write_file(relative_path: str, content: str) -> str:
    try:
        path = _safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"تم الحفظ بنجاح في: {relative_path}"
    except Exception as exc:
        return f"خطأ في كتابة الملف: {exc}"


def list_files(relative_dir: str = ".") -> str:
    try:
        path = _safe_path(relative_dir)
        if not path.is_dir():
            return f"المسار مش مجلد: {relative_dir}"
        items = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
        return "\n".join(items) if items else "(مجلد فاضي)"
    except Exception as exc:
        return f"خطأ في عرض المجلد: {exc}"


READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": "يقرأ محتوى ملف نصي من مساحة العمل (workspace).",
    "input_schema": {
        "type": "object",
        "properties": {"relative_path": {"type": "string", "description": "المسار النسبي للملف داخل workspace"}},
        "required": ["relative_path"],
    },
}

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": "يكتب أو ينشئ ملف نصي داخل مساحة العمل (workspace).",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string", "description": "المسار النسبي للملف داخل workspace"},
            "content": {"type": "string", "description": "المحتوى المراد كتابته بالكامل"},
        },
        "required": ["relative_path", "content"],
    },
}

LIST_FILES_SCHEMA = {
    "name": "list_files",
    "description": "يعرض محتويات مجلد داخل مساحة العمل (workspace).",
    "input_schema": {
        "type": "object",
        "properties": {"relative_dir": {"type": "string", "description": "المسار النسبي للمجلد، افتراضيًا الجذر"}},
        "required": [],
    },
}
