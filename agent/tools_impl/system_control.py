"""
system_control.py
------------------
أدوات تتعامل مباشرة مع نظام التشغيل. دي أخطر فئة أدوات في المشروع كله
لأنها مش محصورة في مجلد workspace زي أدوات الملفات العادية - عشان كده:

  - shutdown_computer لازم confirm=True صريح، تاني حاجة بعد ما الموديل
    يعرض للمستخدم إيه اللي هيحصل وياخد موافقة (نفس القاعدة المكتوبة
    في system_prompt بتاع config.py)
  - مفيش "تعريف طابعة من الصفر" لأن ده مرتبط بتعريفات (drivers) خاصة
    بكل هاردوير، مش حاجة عامة تتبرمج. اللي بنعمله هو اكتشاف الطابعات
    المتاحة فعليًا على النظام وتحديد/تغيير الافتراضية والطباعة عليها.
"""

import platform
import subprocess


def shutdown_computer(confirm: bool = False, delay_seconds: int = 0) -> str:
    """يقفل الجهاز فعليًا. لازم confirm=True وإلا هيرفض التنفيذ - ده
    خط دفاع تاني بعد تأكيد المستخدم الكلامي، عشان مفيش استدعاء بالغلط
    يقفل جهاز حد وهو شغال."""
    if not confirm:
        return (
            "تم رفض التنفيذ: إغلاق الجهاز عملية لا رجعة فيها. "
            "لازم تتأكد من المستخدم صراحة الأول، وبعدها تستدعي الأداة بـ confirm=True."
        )

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["osascript", "-e", "tell app \"System Events\" to shut down"], check=True)
        elif system == "Linux":
            subprocess.run(["shutdown", "-h", f"+{max(1, delay_seconds // 60)}"], check=True)
        else:
            return f"نظام التشغيل غير مدعوم للإغلاق التلقائي: {system}"
        return f"جاري إغلاق الجهاز خلال {delay_seconds} ثانية."
    except subprocess.CalledProcessError as exc:
        return f"فشل إغلاق الجهاز (يمكن يحتاج صلاحيات مدير/Administrator): {exc}"
    except Exception as exc:
        return f"خطأ غير متوقع أثناء محاولة الإغلاق: {exc}"


def list_printers() -> str:
    """يكتشف الطابعات المتاحة فعليًا على النظام (المُعرّفة مسبقًا فقط -
    ده مش نفس حاجة 'تنصيب طابعة جديدة')."""
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["powershell", "-Command", "Get-Printer | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, check=True,
            )
            printers = [p.strip() for p in result.stdout.splitlines() if p.strip()]
        else:  # Linux / macOS بيستخدموا CUPS
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, check=True)
            printers = [
                line.split()[1] for line in result.stdout.splitlines() if line.startswith("printer")
            ]

        if not printers:
            return "مفيش طابعات معرّفة على الجهاز حاليًا. لازم تتنصب من إعدادات النظام أولاً."
        return "الطابعات المتاحة:\n" + "\n".join(f"- {p}" for p in printers)
    except FileNotFoundError:
        return "مقدرش أوصل لنظام الطباعة (لازم CUPS متثبت على Linux/Mac، أو PowerShell على ويندوز)."
    except Exception as exc:
        return f"خطأ في اكتشاف الطابعات: {exc}"


def set_default_printer(printer_name: str) -> str:
    system = platform.system()
    try:
        if system == "Windows":
            # مهم: كنا بنحط printer_name جوه f-string ونمرره كنص واحد
            # لـ PowerShell -Command - ده ثغرة حقن أوامر حقيقية (لو الاسم
            # فيه علامة اقتباس أو ; ممكن ينفذ أي أمر PowerShell عشوائي).
            # الحل: نمرر القيمة عن طريق متغير بيئة (env var) بدل تضمينها
            # في نص الأمر نفسه، فمفيش أي جزء من كلام المستخدم بيتفسر كـ كود.
            import os as _os

            env = _os.environ.copy()
            env["JARVIS_PRINTER_NAME"] = printer_name
            subprocess.run(
                ["powershell", "-Command",
                 "(New-Object -ComObject WScript.Network).SetDefaultPrinter($env:JARVIS_PRINTER_NAME)"],
                check=True, env=env,
            )
        else:
            subprocess.run(["lpoptions", "-d", printer_name], check=True)
        return f"تم تعيين '{printer_name}' كطابعة افتراضية."
    except Exception as exc:
        return f"خطأ في تعيين الطابعة الافتراضية: {exc}"


def print_file(file_path: str, printer_name: str = "") -> str:
    """يطبع ملف موجود فعليًا على المسار المحدد. يدعم أي نوع ملف الطابعة
    ونظام التشغيل بيقدروا يتعاملوا معاه (PDF, docx, صور, نصوص...)."""
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return f"الملف مش موجود: {file_path}"

    system = platform.system()
    try:
        if system == "Windows":
            import os
            # نفس مبدأ الإصلاح فوق: تمرير المسار عن طريق متغير بيئة بدل
            # تضمينه في نص أمر PowerShell، عشان نمنع حقن الأوامر لو
            # المسار فيه علامات اقتباس أو رموز خاصة.
            if printer_name:
                env = os.environ.copy()
                env["JARVIS_PRINT_PATH"] = str(path)
                subprocess.run(
                    ["powershell", "-Command", "Start-Process -FilePath $env:JARVIS_PRINT_PATH -Verb Print"],
                    check=True, env=env,
                )
            else:
                os.startfile(str(path), "print")
        else:
            cmd = ["lp"]
            if printer_name:
                cmd += ["-d", printer_name]
            cmd.append(str(path))
            subprocess.run(cmd, check=True)
        return f"تم إرسال '{path.name}' للطباعة" + (f" على {printer_name}" if printer_name else "") + "."
    except Exception as exc:
        return f"خطأ في الطباعة: {exc}"


SHUTDOWN_SCHEMA = {
    "name": "shutdown_computer",
    "description": (
        "يقفل الجهاز فعليًا. عملية لا رجعة فيها - يجب عرض تأكيد واضح للمستخدم "
        "والحصول على موافقة صريحة قبل الاستدعاء بـ confirm=True."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "confirm": {"type": "boolean", "description": "لازم تكون true وإلا هيترفض التنفيذ"},
            "delay_seconds": {"type": "integer", "description": "تأخير الإغلاق بالثواني، افتراضيًا 0 (فوري)"},
        },
        "required": ["confirm"],
    },
}

LIST_PRINTERS_SCHEMA = {
    "name": "list_printers",
    "description": "يعرض الطابعات المُعرّفة فعليًا على الجهاز حاليًا.",
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

SET_DEFAULT_PRINTER_SCHEMA = {
    "name": "set_default_printer",
    "description": "يعيّن طابعة معينة (من ضمن الطابعات المعرّفة مسبقًا) كطابعة افتراضية.",
    "input_schema": {
        "type": "object",
        "properties": {"printer_name": {"type": "string", "description": "اسم الطابعة بالظبط زي ما يظهر في list_printers"}},
        "required": ["printer_name"],
    },
}

PRINT_FILE_SCHEMA = {
    "name": "print_file",
    "description": "يطبع ملف محدد بالمسار الكامل. لو مفيش printer_name، بيستخدم الطابعة الافتراضية.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "المسار الكامل للملف المراد طباعته"},
            "printer_name": {"type": "string", "description": "اسم طابعة محددة (اختياري)"},
        },
        "required": ["file_path"],
    },
}
