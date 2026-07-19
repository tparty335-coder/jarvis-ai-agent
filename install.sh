#!/usr/bin/env bash
# install.sh — سكريبت تثبيت أوتوماتيكي لـ Linux / macOS
# التشغيل: bash install.sh

set -e

echo "=== تثبيت Jarvis Agent ==="

# التأكد من وجود Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 مش متثبت. راجع الخطوة 1 في INSTALL.md"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION موجود"

# إنشاء البيئة الافتراضية لو مش موجودة
if [ ! -d "venv" ]; then
    echo "... بيتم إنشاء بيئة افتراضية (venv) ..."
    python3 -m venv venv
fi

# تفعيل البيئة الافتراضية
source venv/bin/activate

echo "... بيتم تثبيت الأساسيات ..."
pip install --upgrade pip -q
pip install -r requirements-core.txt -q
echo "✅ الأساسيات اتثبتت"

# سؤال المستخدم عن التكاملات الاختيارية
echo ""
echo "عايز تثبت أي تكاملات إضافية؟ (اكتب y أو n لكل واحدة)"

read -p "  Gmail؟ [y/n]: " install_gmail
if [ "$install_gmail" = "y" ]; then
    pip install -r requirements-gmail.txt -q
    echo "  ✅ تم تثبيت مكتبات Gmail"
fi

read -p "  بوت تليجرام؟ [y/n]: " install_telegram
if [ "$install_telegram" = "y" ]; then
    pip install -r requirements-telegram.txt -q
    echo "  ✅ تم تثبيت مكتبة تليجرام"
fi

read -p "  حزمة الأوفيس (Word/Excel/PowerPoint)؟ [y/n]: " install_office
if [ "$install_office" = "y" ]; then
    pip install -r requirements-office.txt -q
    echo "  ✅ تم تثبيت مكتبات الأوفيس"
fi

read -p "  تعديل الصور؟ [y/n]: " install_images
if [ "$install_images" = "y" ]; then
    pip install -r requirements-images.txt -q
    echo "  ✅ تم تثبيت مكتبة الصور"
fi

read -p "  نقل ملفات لسلة المهملات بأمان؟ [y/n]: " install_files
if [ "$install_files" = "y" ]; then
    pip install -r requirements-files.txt -q
    echo "  ✅ تم تثبيت مكتبة الملفات"
fi

echo ""
echo "=== التثبيت خلص ✅ ==="
echo ""
echo "الخطوة الجاية: حدد مفتاح Claude API:"
echo "  export ANTHROPIC_API_KEY=\"sk-ant-مفتاحك-هنا\""
echo ""
echo "بعدين افحص الجاهزية:"
echo "  python check_setup.py"
echo ""
echo "وشغّل الوكيل:"
echo "  python cli.py"
