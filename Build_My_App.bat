@echo off
echo ==================================================
echo جاري تثبيت المتطلبات وتحويل جارفيس إلى تطبيق احترافي
echo ==================================================

echo 1. تثبيت كافة المكتبات (PyQt6, Gemini, SpeechRecognition, باقِ الأدوات)...
pip install -r requirements-all.txt

echo 2. بناء ملف Jarvis.exe المخفي بدون شاشة سوداء (No Console)...
pyinstaller --noconsole --onefile --name Jarvis gui.py

echo ==================================================
echo تم البناء بنجاح!
echo ستجد ملف Jarvis.exe الحقيقي في مجلد (dist). 
echo يمكنك الآن فتح ملف setup.iss باستخدام برنامج Inno Setup لإنشاء ملف تثبيت Setup.exe احترافي.
echo ==================================================
pause
