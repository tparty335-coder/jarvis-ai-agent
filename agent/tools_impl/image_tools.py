"""
image_tools.py
--------------
ليه مش Paint فعليًا؟ برنامج mspaint.exe (وبرامج الرسم المشابهة) مالوش
أي Command-Line Interface ولا API - الطريقة الوحيدة "للتحكم" فيه هي
محاكاة حركة الماوس والكيبورد (GUI automation)، وده:
  - هش جدًا (أي تغيير بسيط في مكان زرار بيكسر السكريبت كله)
  - بطيء
  - مش قابل للتكرار بدقة (فرق بكسل واحد ممكن يخرب النتيجة)

البديل هنا (Pillow / PIL) بيدّيك نفس النتائج (قص، تكبير، تدوير، فلاتر،
كتابة نص، دمج صور) لكن بدقة رياضية وسرعة، وشغال حتى من غير أي واجهة
رسومية مفتوحة أصلاً. ده معيار الصناعة الفعلي لمعالجة الصور بالكود.

التثبيت: pip install -r requirements-images.txt
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


def resize_image(relative_path: str, output_path: str, width: int, height: int) -> str:
    try:
        from PIL import Image

        src = _safe_path(relative_path)
        dst = _safe_path(output_path)
        img = Image.open(src)
        resized = img.resize((width, height))
        dst.parent.mkdir(parents=True, exist_ok=True)
        resized.save(dst)
        return f"تم تغيير الحجم إلى {width}x{height} وحفظه في {output_path}"
    except ImportError:
        return "مكتبة Pillow مش متثبتة. شغّل: pip install -r requirements-images.txt"
    except Exception as exc:
        return f"خطأ في تغيير حجم الصورة: {exc}"


def crop_image(relative_path: str, output_path: str, left: int, top: int, right: int, bottom: int) -> str:
    try:
        from PIL import Image

        src = _safe_path(relative_path)
        dst = _safe_path(output_path)
        img = Image.open(src)
        cropped = img.crop((left, top, right, bottom))
        dst.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dst)
        return f"تم قص الصورة وحفظها في {output_path}"
    except ImportError:
        return "مكتبة Pillow مش متثبتة."
    except Exception as exc:
        return f"خطأ في قص الصورة: {exc}"


def rotate_image(relative_path: str, output_path: str, degrees: float) -> str:
    try:
        from PIL import Image

        src = _safe_path(relative_path)
        dst = _safe_path(output_path)
        img = Image.open(src)
        rotated = img.rotate(-degrees, expand=True)  # سالب عشان الدوران يبقى مع عقارب الساعة زي المتوقع بديهيًا
        dst.parent.mkdir(parents=True, exist_ok=True)
        rotated.save(dst)
        return f"تم تدوير الصورة {degrees} درجة وحفظها في {output_path}"
    except ImportError:
        return "مكتبة Pillow مش متثبتة."
    except Exception as exc:
        return f"خطأ في تدوير الصورة: {exc}"


def apply_filter(relative_path: str, output_path: str, filter_name: str) -> str:
    """filter_name: 'blur', 'sharpen', 'grayscale', 'contour', 'emboss'"""
    try:
        from PIL import Image, ImageFilter

        filter_map = {
            "blur": ImageFilter.BLUR,
            "sharpen": ImageFilter.SHARPEN,
            "contour": ImageFilter.CONTOUR,
            "emboss": ImageFilter.EMBOSS,
        }

        src = _safe_path(relative_path)
        dst = _safe_path(output_path)
        img = Image.open(src)

        if filter_name == "grayscale":
            result = img.convert("L")
        elif filter_name in filter_map:
            result = img.filter(filter_map[filter_name])
        else:
            return f"فلتر غير معروف: {filter_name}. الخيارات: blur, sharpen, grayscale, contour, emboss"

        dst.parent.mkdir(parents=True, exist_ok=True)
        result.save(dst)
        return f"تم تطبيق فلتر {filter_name} وحفظه في {output_path}"
    except ImportError:
        return "مكتبة Pillow مش متثبتة."
    except Exception as exc:
        return f"خطأ في تطبيق الفلتر: {exc}"


def add_text_to_image(relative_path: str, output_path: str, text: str, x: int, y: int, font_size: int = 24) -> str:
    try:
        from PIL import Image, ImageDraw, ImageFont

        src = _safe_path(relative_path)
        dst = _safe_path(output_path)
        img = Image.open(src).convert("RGBA")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        draw.text((x, y), text, fill="white", font=font, stroke_width=2, stroke_fill="black")
        dst.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(dst)
        return f"تم إضافة النص وحفظه في {output_path}"
    except ImportError:
        return "مكتبة Pillow مش متثبتة."
    except Exception as exc:
        return f"خطأ في إضافة النص للصورة: {exc}"


def convert_image_format(relative_path: str, output_path: str) -> str:
    """يحوّل صيغة الصورة بناءً على امتداد output_path (مثال: من .png لـ .jpg)"""
    try:
        from PIL import Image

        src = _safe_path(relative_path)
        dst = _safe_path(output_path)
        img = Image.open(src)
        if dst.suffix.lower() in (".jpg", ".jpeg"):
            img = img.convert("RGB")
        dst.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst)
        return f"تم تحويل الصيغة وحفظها في {output_path}"
    except ImportError:
        return "مكتبة Pillow مش متثبتة."
    except Exception as exc:
        return f"خطأ في تحويل صيغة الصورة: {exc}"


RESIZE_SCHEMA = {
    "name": "resize_image",
    "description": "يغيّر حجم صورة لأبعاد محددة.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"}, "output_path": {"type": "string"},
            "width": {"type": "integer"}, "height": {"type": "integer"},
        },
        "required": ["relative_path", "output_path", "width", "height"],
    },
}

CROP_SCHEMA = {
    "name": "crop_image",
    "description": "يقص جزء من صورة بإحداثيات (left, top, right, bottom).",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"}, "output_path": {"type": "string"},
            "left": {"type": "integer"}, "top": {"type": "integer"},
            "right": {"type": "integer"}, "bottom": {"type": "integer"},
        },
        "required": ["relative_path", "output_path", "left", "top", "right", "bottom"],
    },
}

ROTATE_SCHEMA = {
    "name": "rotate_image",
    "description": "يدوّر صورة بعدد درجات معين.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"}, "output_path": {"type": "string"},
            "degrees": {"type": "number"},
        },
        "required": ["relative_path", "output_path", "degrees"],
    },
}

FILTER_SCHEMA = {
    "name": "apply_filter",
    "description": "يطبّق فلتر على صورة: blur, sharpen, grayscale, contour, emboss.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"}, "output_path": {"type": "string"},
            "filter_name": {"type": "string", "enum": ["blur", "sharpen", "grayscale", "contour", "emboss"]},
        },
        "required": ["relative_path", "output_path", "filter_name"],
    },
}

ADD_TEXT_SCHEMA = {
    "name": "add_text_to_image",
    "description": "يضيف نص فوق صورة في إحداثيات محددة.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string"}, "output_path": {"type": "string"},
            "text": {"type": "string"}, "x": {"type": "integer"}, "y": {"type": "integer"},
            "font_size": {"type": "integer"},
        },
        "required": ["relative_path", "output_path", "text", "x", "y"],
    },
}

CONVERT_FORMAT_SCHEMA = {
    "name": "convert_image_format",
    "description": "يحوّل صيغة صورة بناءً على امتداد الملف الناتج (مثال: PNG إلى JPG).",
    "input_schema": {
        "type": "object",
        "properties": {"relative_path": {"type": "string"}, "output_path": {"type": "string"}},
        "required": ["relative_path", "output_path"],
    },
}
