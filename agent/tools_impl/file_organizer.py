"""
file_organizer.py
------------------
مهم جدًا تفهم الفرق ده: أدوات files.py العادية محصورة في workspace/
كطبقة أمان. الأدوات هنا مختلفة تمامًا وبتوصل لأي مسار على أي بارتشن
بناءً على طلب صريح منك - "الفهرسة والتنظيم لأي بارتشن" اللي طلبته
معناه بالضرورة كسر حدود الـ workspace.

## قرار أمان مهم مطبّق هنا:
  - الفهرسة (index) والبحث (search) للقراءة بس - آمنة تمامًا
  - النقل وإعادة التسمية (organize/move/rename) بتحتاج المسارات تتعرض
    للمستخدم في الرد قبل التنفيذ الفعلي (نفس قاعدة "التأكيد قبل أي
    إجراء لا رجعة فيه" المكتوبة في system_prompt)
  - **مفيش أداة حذف نهائي هنا خالص** - أقصى حاجة move_to_trash بتنقل
    الملف لمجلد "المهملات" الخاص بنظام التشغيل، قابل للاسترجاع
"""

import os
import platform
import shutil
import sqlite3
import time
from pathlib import Path

from ..config import DATA_DIR

INDEX_DB_PATH = DATA_DIR / "file_index.db"

# ---------------------------------------------------------------------------
# حماية إضافية بعد المراجعة: مسارات نظام حساسة ممنوع لمس - سواء كمصدر أو
# كوجهة - بغض النظر عن أي تأكيد. السبب: move_file/organize_by_extension
# كانت بتنفذ فورًا على أي مسار من غير أي فحص، وده باب حقيقي لو حد نجح
# يخلي الموديل ينفذ تعليمة خبيثة جاية من محتوى خارجي (إيميل، صفحة ويب)
# بتقوله "انقل/احذف فلان من مجلد النظام". الفحص ده بيشتغل بغض النظر عن
# قرار الموديل، مش مجرد تعليمات في الـ system prompt.
_SYSTEM = platform.system()
if _SYSTEM == "Windows":
    _PROTECTED_PREFIXES = [
        os.environ.get("WINDIR", "C:\\Windows"),
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\ProgramData",
    ]
elif _SYSTEM == "Darwin":
    _PROTECTED_PREFIXES = ["/System", "/Library", "/usr", "/bin", "/sbin", "/private"]
else:  # Linux
    _PROTECTED_PREFIXES = ["/etc", "/bin", "/sbin", "/usr", "/boot", "/lib", "/lib64", "/sys", "/proc", "/root"]


def _is_protected_path(path: Path) -> bool:
    """بيتحقق هل المسار (أو أي جزء منه) واقع جوه مجلد نظام حساس."""
    try:
        resolved = str(path.resolve()).lower()
    except Exception:
        resolved = str(path).lower()
    return any(resolved.startswith(prefix.lower()) for prefix in _PROTECTED_PREFIXES)


def _get_index_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(INDEX_DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS file_index (
            path TEXT PRIMARY KEY,
            name TEXT,
            extension TEXT,
            size_bytes INTEGER,
            modified_at REAL,
            indexed_at REAL
        )
        """
    )
    return conn


def index_directory(root_path: str, max_files: int = 20000) -> str:
    """يفهرس كل الملفات جوه مسار معين (وأي مجلدات فرعية) في قاعدة بيانات
    محلية، عشان يقدر يبحث فيها بسرعة بعدين من غير ما يمشي على القرص
    كله من الأول في كل مرة."""
    root = Path(root_path)
    if not root.exists():
        return f"المسار مش موجود: {root_path}"

    conn = _get_index_connection()
    count = 0
    now = time.time()
    try:
        for dirpath, _dirnames, filenames in os.walk(root):
            for filename in filenames:
                if count >= max_files:
                    break
                full_path = Path(dirpath) / filename
                try:
                    stat = full_path.stat()
                except (OSError, PermissionError):
                    continue
                conn.execute(
                    """
                    INSERT INTO file_index (path, name, extension, size_bytes, modified_at, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        size_bytes = excluded.size_bytes,
                        modified_at = excluded.modified_at,
                        indexed_at = excluded.indexed_at
                    """,
                    (str(full_path), filename, full_path.suffix.lower(), stat.st_size, stat.st_mtime, now),
                )
                count += 1
            if count >= max_files:
                break
        conn.commit()
        return f"تم فهرسة {count} ملف من {root_path}."
    except Exception as exc:
        return f"خطأ أثناء الفهرسة: {exc}"
    finally:
        conn.close()


def search_index(query: str = "", extension: str = "", min_size_mb: float = 0, limit: int = 50) -> str:
    """يبحث في الفهرس المخزّن (لازم index_directory يتنفذ الأول على
    المسار المطلوب). البحث بالاسم، الامتداد، أو حجم أدنى."""
    conn = _get_index_connection()
    try:
        conditions = []
        params: list = []
        if query:
            conditions.append("name LIKE ?")
            params.append(f"%{query}%")
        if extension:
            conditions.append("extension = ?")
            params.append(extension if extension.startswith(".") else f".{extension}")
        if min_size_mb:
            conditions.append("size_bytes >= ?")
            params.append(min_size_mb * 1024 * 1024)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = conn.execute(
            f"SELECT path, size_bytes, modified_at FROM file_index {where_clause} "
            f"ORDER BY modified_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()

        if not rows:
            return "مفيش نتائج مطابقة في الفهرس (تأكد إنك عملت index_directory على المسار المطلوب الأول)."

        lines = [f"{p} — {round(s / 1024 / 1024, 2)} ميجا" for p, s, _m in rows]
        return "\n".join(lines)
    finally:
        conn.close()


def move_file(source_path: str, destination_path: str) -> str:
    """ينقل أو يعيد تسمية ملف. لازم يتعرض على المستخدم قبل التنفيذ
    لو جزء من عملية تنظيم جماعية."""
    src, dst = Path(source_path), Path(destination_path)

    if _is_protected_path(src) or _is_protected_path(dst):
        return (
            "تم رفض التنفيذ: المسار المصدر أو الوجهة واقع جوه مجلد نظام حساس "
            "(زي مجلدات النظام أو Program Files). العملية دي محظورة على مستوى "
            "الكود لحماية استقرار الجهاز، بغض النظر عن سبب الطلب."
        )

    if not src.exists():
        return f"الملف المصدر مش موجود: {source_path}"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"تم نقل الملف من {source_path} إلى {destination_path}"
    except Exception as exc:
        return f"خطأ في نقل الملف: {exc}"


def move_to_trash(file_path: str) -> str:
    """بينقل الملف لسلة مهملات نظام التشغيل (قابل للاسترجاع)، مش حذف
    نهائي. ده الأداة الوحيدة هنا اللي بتشيل ملفات، وبشكل قابل للتراجع."""
    path = Path(file_path)
    if _is_protected_path(path):
        return (
            "تم رفض التنفيذ: المسار ده واقع جوه مجلد نظام حساس. العملية "
            "دي محظورة على مستوى الكود لحماية استقرار الجهاز."
        )
    try:
        from send2trash import send2trash

        if not path.exists():
            return f"الملف مش موجود: {file_path}"
        send2trash(str(path))
        return f"تم نقل '{path.name}' لسلة مهملات النظام (قابل للاسترجاع)."
    except ImportError:
        return "مكتبة send2trash مش متثبتة. شغّل: pip install -r requirements-files.txt"
    except Exception as exc:
        return f"خطأ في نقل الملف للمهملات: {exc}"


def organize_by_extension(root_path: str, dry_run: bool = True) -> str:
    """يقترح (أو ينفذ لو dry_run=False) تنظيم مجلد بترتيب الملفات في
    مجلدات فرعية حسب النوع (PDFs/, Images/, Documents/, إلخ).
    الافتراضي dry_run=True يعني بيقترح بس من غير تنفيذ فعلي - ده مقصود
    عشان تشوف الخطة قبل ما توافق عليها."""
    root = Path(root_path)
    if not root.exists():
        return f"المسار مش موجود: {root_path}"

    if _is_protected_path(root):
        return (
            "تم رفض التنفيذ: المسار ده واقع جوه مجلد نظام حساس. تنظيم "
            "الملفات في مجلدات النظام محظور على مستوى الكود."
        )

    category_map = {
        ".pdf": "PDFs", ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
        ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
        ".mp4": "Videos", ".mov": "Videos", ".mkv": "Videos",
        ".mp3": "Audio", ".wav": "Audio",
        ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
        ".xlsx": "Spreadsheets", ".xls": "Spreadsheets", ".csv": "Spreadsheets",
        ".pptx": "Presentations", ".ppt": "Presentations",
    }

    plan = []
    for item in root.iterdir():
        if item.is_file():
            category = category_map.get(item.suffix.lower(), "Other")
            plan.append((item, root / category / item.name))

    if not plan:
        return "مفيش ملفات في المجلد ده للتنظيم."

    if dry_run:
        lines = [f"{src.name} → {dst.parent.name}/" for src, dst in plan]
        return f"خطة التنظيم المقترحة ({len(plan)} ملف) - استخدم dry_run=False للتنفيذ الفعلي بعد الموافقة:\n" + "\n".join(lines)

    moved = 0
    for src, dst in plan:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1
        except Exception:
            continue
    return f"تم تنظيم {moved} ملف في {root_path}."


INDEX_DIRECTORY_SCHEMA = {
    "name": "index_directory",
    "description": "يفهرس كل الملفات جوه مسار معين (بما فيه المجلدات الفرعية) في قاعدة بيانات محلية للبحث السريع بعدين.",
    "input_schema": {
        "type": "object",
        "properties": {
            "root_path": {"type": "string", "description": "المسار الكامل للمجلد أو البارتشن المراد فهرسته"},
            "max_files": {"type": "integer", "description": "أقصى عدد ملفات، افتراضيًا 20000"},
        },
        "required": ["root_path"],
    },
}

SEARCH_INDEX_SCHEMA = {
    "name": "search_index",
    "description": "يبحث في الفهرس المخزّن مسبقًا بالاسم أو الامتداد أو الحجم الأدنى.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "جزء من اسم الملف"},
            "extension": {"type": "string", "description": "مثال: '.pdf'"},
            "min_size_mb": {"type": "number", "description": "أقل حجم بالميجا"},
            "limit": {"type": "integer", "description": "أقصى عدد نتائج، افتراضيًا 50"},
        },
        "required": [],
    },
}

MOVE_FILE_SCHEMA = {
    "name": "move_file",
    "description": "ينقل أو يعيد تسمية ملف من مسار لمسار تاني، في أي مكان على الجهاز.",
    "input_schema": {
        "type": "object",
        "properties": {
            "source_path": {"type": "string"},
            "destination_path": {"type": "string"},
        },
        "required": ["source_path", "destination_path"],
    },
}

MOVE_TO_TRASH_SCHEMA = {
    "name": "move_to_trash",
    "description": "ينقل ملف لسلة مهملات نظام التشغيل (قابل للاسترجاع، مش حذف نهائي).",
    "input_schema": {
        "type": "object",
        "properties": {"file_path": {"type": "string"}},
        "required": ["file_path"],
    },
}

ORGANIZE_BY_EXTENSION_SCHEMA = {
    "name": "organize_by_extension",
    "description": (
        "يقترح خطة لتنظيم مجلد بترتيب الملفات في مجلدات فرعية حسب النوع. "
        "افتراضيًا dry_run=True (بيعرض خطة بس من غير تنفيذ) - لازم تعرض الخطة "
        "للمستخدم وتاخد موافقته قبل ما تستدعيها تاني بـ dry_run=False."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "root_path": {"type": "string"},
            "dry_run": {"type": "boolean", "description": "افتراضيًا true (اقتراح بس)"},
        },
        "required": ["root_path"],
    },
}
