"""
tools.py
--------
السجل المركزي لكل الأدوات. أي أداة جديدة تضيفها للمشروع، تسجلها هنا
في مكان واحد بس، وتلقائيًا هتبقى متاحة للوكيل في كل مكان.

عشان تضيف أداة جديدة:
  1. اعمل ملف جديد في tools_impl/ فيه الدالة + TOOL_SCHEMA
  2. استوردها هنا
  3. ضيفها في TOOL_REGISTRY و TOOL_SCHEMAS
"""

from typing import Any, Callable

from .tools_impl import calculator, files, web, memory_tools

# كل أداة: اسمها -> الدالة اللي بتنفذها فعليًا
TOOL_REGISTRY: dict[str, Callable[..., str]] = {
    "calculator": lambda **kw: calculator.calculate(**kw),
    "read_file": lambda **kw: files.read_file(**kw),
    "write_file": lambda **kw: files.write_file(**kw),
    "list_files": lambda **kw: files.list_files(**kw),
    "web_search": lambda **kw: web.web_search(**kw),
    "open_browser": lambda **kw: web.open_browser(**kw),
    "remember": lambda **kw: memory_tools.remember(**kw),
    "recall": lambda **kw: memory_tools.recall(**kw),
    "list_memories": lambda **kw: memory_tools.list_memories(**kw),
}

# الـ schemas اللي بتتبعت لـ Claude API عشان يعرف الأدوات المتاحة وشكل مدخلاتها
TOOL_SCHEMAS: list[dict[str, Any]] = [
    calculator.TOOL_SCHEMA,
    files.READ_FILE_SCHEMA,
    files.WRITE_FILE_SCHEMA,
    files.LIST_FILES_SCHEMA,
    web.TOOL_SCHEMA,
    web.OPEN_BROWSER_SCHEMA,
    memory_tools.REMEMBER_SCHEMA,
    memory_tools.RECALL_SCHEMA,
    memory_tools.LIST_MEMORIES_SCHEMA,
]

# --- أدوات Gmail: استيراد اختياري ---
# ليه try/except هنا بالذات؟ عشان مكتبات جوجل (google-api-python-client...)
# مش أساسية للمشروع يشتغل، وبعض المستخدمين ممكن يستخدموا جميل والبعض لأ.
# لو مش متثبتة، النظام كله يفضل شغال عادي بدون أدوات جيميل، بدل ما يقع
# بالكامل بسبب import error في مكتبة مش هو محتاجها دلوقتي.
try:
    from .tools_impl import gmail_tool

    TOOL_REGISTRY.update(
        {
            "gmail_search": lambda **kw: gmail_tool.gmail_search(**kw),
            "gmail_archive": lambda **kw: gmail_tool.gmail_archive(**kw),
            "gmail_trash": lambda **kw: gmail_tool.gmail_trash(**kw),
            "gmail_bulk_clean": lambda **kw: gmail_tool.gmail_bulk_clean(**kw),
        }
    )
    TOOL_SCHEMAS.extend(
        [
            gmail_tool.SEARCH_SCHEMA,
            gmail_tool.ARCHIVE_SCHEMA,
            gmail_tool.TRASH_SCHEMA,
            gmail_tool.BULK_CLEAN_SCHEMA,
        ]
    )
except ImportError:
    pass

# --- أدوات إضافية: نظام، أوفيس، تنظيم ملفات، صور (استيراد اختياري) ---
try:
    from .tools_impl import system_control

    TOOL_REGISTRY.update(
        {
            "shutdown_computer": lambda **kw: system_control.shutdown_computer(**kw),
            "list_printers": lambda **kw: system_control.list_printers(**kw),
            "set_default_printer": lambda **kw: system_control.set_default_printer(**kw),
            "print_file": lambda **kw: system_control.print_file(**kw),
            "take_screenshot": lambda **kw: system_control.take_screenshot(**kw),
            "mouse_click": lambda **kw: system_control.mouse_click(**kw),
            "type_text": lambda **kw: system_control.type_text(**kw),
            "press_key": lambda **kw: system_control.press_key(**kw),
            "run_terminal_command": lambda **kw: system_control.run_terminal_command(**kw),
        }
    )
    TOOL_SCHEMAS.extend(
        [
            system_control.SHUTDOWN_SCHEMA,
            system_control.LIST_PRINTERS_SCHEMA,
            system_control.SET_DEFAULT_PRINTER_SCHEMA,
            system_control.PRINT_FILE_SCHEMA,
            system_control.TAKE_SCREENSHOT_SCHEMA,
            system_control.MOUSE_CLICK_SCHEMA,
            system_control.TYPE_TEXT_SCHEMA,
            system_control.PRESS_KEY_SCHEMA,
            system_control.RUN_TERMINAL_COMMAND_SCHEMA,
        ]
    )
except ImportError:
    pass

try:
    from .tools_impl import office_tools

    TOOL_REGISTRY.update(
        {
            "create_word_document": lambda **kw: office_tools.create_word_document(**kw),
            "append_to_word_document": lambda **kw: office_tools.append_to_word_document(**kw),
            "create_excel_sheet": lambda **kw: office_tools.create_excel_sheet(**kw),
            "add_excel_formula": lambda **kw: office_tools.add_excel_formula(**kw),
            "create_powerpoint": lambda **kw: office_tools.create_powerpoint(**kw),
        }
    )
    TOOL_SCHEMAS.extend(
        [
            office_tools.CREATE_WORD_SCHEMA,
            office_tools.APPEND_WORD_SCHEMA,
            office_tools.CREATE_EXCEL_SCHEMA,
            office_tools.ADD_EXCEL_FORMULA_SCHEMA,
            office_tools.CREATE_PPTX_SCHEMA,
        ]
    )
except ImportError:
    pass

try:
    from .tools_impl import file_organizer

    TOOL_REGISTRY.update(
        {
            "index_directory": lambda **kw: file_organizer.index_directory(**kw),
            "search_index": lambda **kw: file_organizer.search_index(**kw),
            "move_file": lambda **kw: file_organizer.move_file(**kw),
            "move_to_trash": lambda **kw: file_organizer.move_to_trash(**kw),
            "organize_by_extension": lambda **kw: file_organizer.organize_by_extension(**kw),
        }
    )
    TOOL_SCHEMAS.extend(
        [
            file_organizer.INDEX_DIRECTORY_SCHEMA,
            file_organizer.SEARCH_INDEX_SCHEMA,
            file_organizer.MOVE_FILE_SCHEMA,
            file_organizer.MOVE_TO_TRASH_SCHEMA,
            file_organizer.ORGANIZE_BY_EXTENSION_SCHEMA,
        ]
    )
except ImportError:
    pass

try:
    from .tools_impl import image_tools

    TOOL_REGISTRY.update(
        {
            "resize_image": lambda **kw: image_tools.resize_image(**kw),
            "crop_image": lambda **kw: image_tools.crop_image(**kw),
            "rotate_image": lambda **kw: image_tools.rotate_image(**kw),
            "apply_filter": lambda **kw: image_tools.apply_filter(**kw),
            "add_text_to_image": lambda **kw: image_tools.add_text_to_image(**kw),
            "convert_image_format": lambda **kw: image_tools.convert_image_format(**kw),
        }
    )
    TOOL_SCHEMAS.extend(
        [
            image_tools.RESIZE_SCHEMA,
            image_tools.CROP_SCHEMA,
            image_tools.ROTATE_SCHEMA,
            image_tools.FILTER_SCHEMA,
            image_tools.ADD_TEXT_SCHEMA,
            image_tools.CONVERT_FORMAT_SCHEMA,
        ]
    )
except ImportError:
    pass


SAFETY_CONFIRM_CALLBACK = None
TIMELINE_LOG_CALLBACK = None

def execute_tool(name: str, tool_input: dict[str, Any]) -> str:
    """بينفذ أداة بالاسم. لو كانت خطيرة، يطلب تأكيد المستخدم قبل التنفيذ."""
    if TIMELINE_LOG_CALLBACK:
        TIMELINE_LOG_CALLBACK(f"Executing task: {name}", "⚙️")
        
    if name not in TOOL_REGISTRY:
        if TIMELINE_LOG_CALLBACK: TIMELINE_LOG_CALLBACK(f"Failed: {name} not found", "❌")
        return f"خطأ: الأداة '{name}' مش موجودة في السجل."
    
    # جدار الأمان للأدوات الخطيرة
    DANGEROUS_TOOLS = ["shutdown_computer", "restart_computer"]
    if name in DANGEROUS_TOOLS:
        if SAFETY_CONFIRM_CALLBACK:
            approved = SAFETY_CONFIRM_CALLBACK(name, str(tool_input))
            if not approved:
                return f"تم رفض التنفيذ. المستخدم رفض العملية لأسباب أمنية."
        else:
            return "تم الرفض. لم يتم العثور على واجهة التأكيد الأمنية (Safety Callback)."

    try:
        return TOOL_REGISTRY[name](**tool_input)
    except Exception as exc:
        return f"حصل خطأ أثناء تنفيذ الأداة '{name}': {exc}"
