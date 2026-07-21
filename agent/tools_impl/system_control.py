"""
system_control.py
-----------------
أدوات التحكم النظامية الخطيرة (مثل إغلاق الجهاز، إعادة التشغيل).
هذه الأدوات تتطلب "تأكيد صريح" من المستخدم عبر واجهة الأمان.
"""

import os
import subprocess
import pyautogui
from PIL import ImageGrab
import time
import tempfile

# القائمة التي تحدد الأدوات التي تتطلب تأكيد
REQUIRES_CONFIRMATION = [
    "shutdown_computer",
    "restart_computer",
    "run_terminal_command"
]

RUN_TERMINAL_COMMAND_SCHEMA = {
    "name": "run_terminal_command",
    "description": "ينفذ أوامر في موجه الأوامر (Terminal/CMD). أداة أساسية لتثبيت مكتبات بايثون عبر 'pip install' أو تنفيذ أي أوامر نظام بدون أن تطلب من المستخدم فعل ذلك يدوياً. سيتم تنفيذ الأمر وجمع النتيجة.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "الأمر المراد تنفيذه (مثل: 'pip install python-docx' أو 'dir')."
            }
        },
        "required": ["command"]
    }
}

SHUTDOWN_SCHEMA = {
    "name": "shutdown_computer",
    "description": "يقوم بإيقاف تشغيل الكمبيوتر (Shutdown) أو إعادة تشغيله (Restart). لا تستخدمها إلا إذا طلب المستخدم بوضوح.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "mode": {
                "type": "STRING",
                "description": "نوع العملية: 'shutdown' للإغلاق، 'restart' لإعادة التشغيل",
            }
        },
        "required": ["mode"]
    }
}

# (The schemas for printers mentioned in tools.py are ignored for now to keep it minimal)
LIST_PRINTERS_SCHEMA = {
    "name": "list_printers",
    "description": "يعرض قائمة بالطابعات المتصلة بالجهاز.",
    "parameters": {"type": "OBJECT", "properties": {}}
}

SET_DEFAULT_PRINTER_SCHEMA = {
    "name": "set_default_printer",
    "description": "يعين طابعة كافتراضية.",
    "parameters": {
        "type": "OBJECT", 
        "properties": {"printer_name": {"type": "STRING"}},
        "required": ["printer_name"]
    }
}

PRINT_FILE_SCHEMA = {
    "name": "print_file",
    "description": "يطبع ملف معين.",
    "parameters": {
        "type": "OBJECT", 
        "properties": {"file_path": {"type": "STRING"}},
        "required": ["file_path"]
    }
}

TAKE_SCREENSHOT_SCHEMA = {
    "name": "take_screenshot",
    "description": "Takes a screenshot of the entire computer screen and returns the image to you automatically. Use this when you need eyes to see what is on the screen.",
    "parameters": {"type": "OBJECT", "properties": {}}
}

MOUSE_CLICK_SCHEMA = {
    "name": "mouse_click",
    "description": "Clicks the mouse on the screen. Give it x and y coordinates if you know them, otherwise it clicks at the current position.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "x": {"type": "INTEGER", "description": "X coordinate on screen"},
            "y": {"type": "INTEGER", "description": "Y coordinate on screen"},
            "button": {"type": "STRING", "description": "'left', 'right', or 'middle'"},
            "clicks": {"type": "INTEGER", "description": "Number of clicks"}
        }
    }
}

TYPE_TEXT_SCHEMA = {
    "name": "type_text",
    "description": "Types text using the keyboard.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {"type": "STRING"},
            "press_enter": {"type": "BOOLEAN", "description": "If true, presses enter after typing"}
        },
        "required": ["text"]
    }
}

PRESS_KEY_SCHEMA = {
    "name": "press_key",
    "description": "Presses a specific keyboard key (e.g., 'enter', 'win', 'space', 'esc', 'tab', 'down', 'up').",
    "parameters": {
        "type": "OBJECT",
        "properties": {"key": {"type": "STRING"}},
        "required": ["key"]
    }
}



def shutdown_computer(mode="shutdown"):
    """دالة الإغلاق الفعلية (يجب أن تكون قد اجتازت التأكيد)."""
    if os.name == 'nt':
        flag = "/s" if mode == "shutdown" else "/r"
        subprocess.run(["shutdown", flag, "/t", "0"])
        return f"جاري {mode} الجهاز الآن..."
    else:
        return "هذه العملية مدعومة على نظام ويندوز فقط حالياً."

def list_printers():
    return "لا توجد طابعات متاحة (mock)."

def set_default_printer(printer_name=""):
    return f"تم تعيين {printer_name} (mock)."

def print_file(file_path=""):
    return f"تم طباعة {file_path} (mock)."

def take_screenshot() -> str:
    """Takes a screenshot of the entire screen and returns it for visual context."""
    screenshot = ImageGrab.grab()
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"jarvis_vision_{int(time.time())}.png")
    screenshot.save(file_path, "PNG")
    return f"[IMAGE_ATTACH] {file_path}"
    
def mouse_click(x: int = None, y: int = None, button: str = 'left', clicks: int = 1) -> str:
    try:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return f"Clicked {button} mouse button {clicks} times at ({x}, {y})."
        else:
            pyautogui.click(button=button, clicks=clicks)
            return f"Clicked {button} mouse button {clicks} times at current position."
    except Exception as e:
        return f"Failed to click: {e}"

def type_text(text: str, press_enter: bool = False) -> str:
    try:
        pyautogui.typewrite(text, interval=0.01)
        if press_enter:
            pyautogui.press('enter')
        return f"Typed text: '{text}'"
    except Exception as e:
        return f"Failed to type text: {e}"

def press_key(key: str) -> str:
    try:
        pyautogui.press(key)
        return f"Pressed key: '{key}'"
    except Exception as e:
        return f"Failed to press key: {e}"

def run_terminal_command(command: str) -> str:
    """Runs a shell command and returns output. For pip install, etc."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace')
        output = result.stdout
        if result.stderr:
            output += f"\n[Errors/Warnings]:\n{result.stderr}"
        if not output.strip():
            output = "[No output]"
        return f"Command executed.\nExit code: {result.returncode}\nOutput:\n{output}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 120 seconds."
    except Exception as e:
        return f"Failed to execute command: {str(e)}"
