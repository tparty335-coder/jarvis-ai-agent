"""
office_tools.py
----------------
تعامل حقيقي مع حزمة الأوفيس - مش عن طريق "التحكم" في برنامج Word أو
Excel نفسه (ده هش وبطيء ومحتاج البرنامج يكون متثبت ومفتوح)، لكن عن
طريق مكتبات بتقرأ وتكتب صيغ الملفات (.docx, .xlsx, .pptx) مباشرة.
ده أوثق وأسرع وبيشتغل حتى لو الأوفيس نفسه مش متثبت على الجهاز.

المكتبات المستخدمة:
  - python-docx  لملفات Word
  - openpyxl      لملفات Excel
  - python-pptx    لملفات PowerPoint

التثبيت: pip install -r requirements-office.txt
"""

from pathlib import Path

from ..config import BASE_DIR

WORKSPACE = BASE_DIR / "workspace"
WORKSPACE.mkdir(exist_ok=True)


def _safe_path(relative_path: str) -> Path:
    target = (WORKSPACE / relative_path).resolve()
    if WORKSPACE.resolve() not in target.parents and target != WORKSPACE.resolve():
        raise ValueError("مش مسموح بالوصول لمسار خارج مساحة العمل (workspace)")
    return target


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------

def create_word_document(relative_path: str, title: str, paragraphs: list[str]) -> str:
    """ينشئ مستند Word جديد بعنوان رئيسي وقائمة فقرات. لو عايز تنسيق أكثر
    تفصيلاً (جداول، صور، تنسيق متقدم)، استخدم edit_word_document بعدها."""
    try:
        from docx import Document

        doc = Document()
        doc.add_heading(title, level=1)
        for para in paragraphs:
            doc.add_paragraph(para)

        path = _safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(path))
        return f"تم إنشاء مستند Word في: {relative_path}"
    except ImportError:
        return "مكتبة python-docx مش متثبتة. شغّل: pip install -r requirements-office.txt"
    except Exception as exc:
        return f"خطأ في إنشاء مستند Word: {exc}"


def append_to_word_document(relative_path: str, text: str, style: str = "Normal") -> str:
    """يضيف فقرة لمستند Word موجود بالفعل. الـ style ممكن يكون
    'Normal', 'Heading 1', 'Heading 2', 'Heading 3'، إلخ."""
    try:
        from docx import Document

        path = _safe_path(relative_path)
        if not path.exists():
            return f"الملف مش موجود: {relative_path}. استخدم create_word_document الأول."

        doc = Document(str(path))
        doc.add_paragraph(text, style=style if style != "Normal" else None)
        doc.save(str(path))
        return f"تم الإضافة لمستند Word: {relative_path}"
    except ImportError:
        return "مكتبة python-docx مش متثبتة."
    except Exception as exc:
        return f"خطأ في التعديل على مستند Word: {exc}"


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

def create_excel_sheet(relative_path: str, sheet_name: str, headers: list[str], rows: list[list]) -> str:
    """ينشئ ملف Excel جديد بشيت واحد، صف عناوين، وصفوف بيانات."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True)

        for row_idx, row_data in enumerate(rows, start=2):
            for col_idx, value in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # عرض أعمدة تلقائي تقريبي حسب أطول قيمة
        for col_idx, header in enumerate(headers, start=1):
            max_len = max([len(str(header))] + [len(str(r[col_idx - 1])) for r in rows if col_idx - 1 < len(r)])
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max_len + 4

        path = _safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(path))
        return f"تم إنشاء ملف Excel في: {relative_path}"
    except ImportError:
        return "مكتبة openpyxl مش متثبتة. شغّل: pip install -r requirements-office.txt"
    except Exception as exc:
        return f"خطأ في إنشاء ملف Excel: {exc}"


def add_excel_formula(relative_path: str, sheet_name: str, cell: str, formula: str) -> str:
    """يضيف معادلة لخلية معينة، مثال: formula='=SUM(A2:A10)'"""
    try:
        from openpyxl import load_workbook

        path = _safe_path(relative_path)
        if not path.exists():
            return f"الملف مش موجود: {relative_path}"

        wb = load_workbook(str(path))
        ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
        ws[cell] = formula
        wb.save(str(path))
        return f"تم إضافة المعادلة {formula} في الخلية {cell}."
    except ImportError:
        return "مكتبة openpyxl مش متثبتة."
    except Exception as exc:
        return f"خطأ في إضافة المعادلة: {exc}"


# ---------------------------------------------------------------------------
# PowerPoint
# ---------------------------------------------------------------------------

def create_powerpoint(relative_path: str, slides: list[dict]) -> str:
    """ينشئ عرض PowerPoint. كل عنصر في slides عبارة عن
    {'title': '...', 'bullets': ['...', '...']}"""
    try:
        from pptx import Presentation

        prs = Presentation()
        title_layout = prs.slide_layouts[0]
        bullet_layout = prs.slide_layouts[1]

        for idx, slide_data in enumerate(slides):
            layout = title_layout if idx == 0 else bullet_layout
            slide = prs.slides.add_slide(layout)
            slide.shapes.title.text = slide_data.get("title", "")

            bullets = slide_data.get("bullets", [])
            if bullets and len(slide.placeholders) > 1:
                body = slide.placeholders[1].text_frame
                body.text = bullets[0]
                for bullet in bullets[1:]:
                    p = body.add_paragraph()
                    p.text = bullet

        path = _safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(path))
        return f"تم إنشاء عرض PowerPoint في: {relative_path} ({len(slides)} شريحة)"
    except ImportError:
        return "مكتبة python-pptx مش متثبتة. شغّل: pip install -r requirements-office.txt"
    except Exception as exc:
        return f"خطأ في إنشاء عرض PowerPoint: {exc}"


CREATE_WORD_SCHEMA = {
    "name": "create_word_document",
    "description": "ينشئ مستند Word جديد بعنوان وفقرات نصية، داخل مساحة العمل.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string", "description": "المسار النسبي، مثال: 'reports/report1.docx'"},
            "title": {"type": "string", "description": "عنوان المستند"},
            "paragraphs": {"type": "array", "items": {"type": "string"}, "description": "قائمة الفقرات"},
        },
        "required": ["relative_path", "title", "paragraphs"],
    },
}

APPEND_WORD_SCHEMA = {
    "name": "append_to_word_document",
    "description": "يضيف فقرة أو عنوان لمستند Word موجود بالفعل.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"},
            "text": {"type": "string"},
            "style": {"type": "string", "description": "'Normal', 'Heading 1', 'Heading 2', 'Heading 3'"},
        },
        "required": ["relative_path", "text"],
    },
}

CREATE_EXCEL_SCHEMA = {
    "name": "create_excel_sheet",
    "description": "ينشئ ملف Excel جديد بصف عناوين وصفوف بيانات، داخل مساحة العمل.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string", "description": "المسار النسبي، مثال: 'data/sheet1.xlsx'"},
            "sheet_name": {"type": "string"},
            "headers": {"type": "array", "items": {"type": "string"}},
            "rows": {"type": "array", "items": {"type": "array"}, "description": "كل صف عبارة عن مصفوفة قيم"},
        },
        "required": ["relative_path", "sheet_name", "headers", "rows"],
    },
}

ADD_EXCEL_FORMULA_SCHEMA = {
    "name": "add_excel_formula",
    "description": "يضيف معادلة Excel لخلية معينة في ملف موجود بالفعل.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"},
            "sheet_name": {"type": "string"},
            "cell": {"type": "string", "description": "مثال: 'B10'"},
            "formula": {"type": "string", "description": "مثال: '=SUM(A2:A10)'"},
        },
        "required": ["relative_path", "sheet_name", "cell", "formula"],
    },
}

CREATE_PPTX_SCHEMA = {
    "name": "create_powerpoint",
    "description": "ينشئ عرض PowerPoint من قائمة شرائح، كل شريحة فيها عنوان ونقاط.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string", "description": "المسار النسبي، مثال: 'presentations/deck1.pptx'"},
            "slides": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "bullets": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
        "required": ["relative_path", "slides"],
    },
}
