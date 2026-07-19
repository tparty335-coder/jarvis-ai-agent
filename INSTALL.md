# دليل التثبيت — Jarvis Agent

الملف ده مخصص للتثبيت على جهاز جديد من الصفر، خطوة بخطوة. مش لازم
خبرة برمجة عميقة، بس لازم تنفذ الخطوات بالترتيب.

---

## الخطوة ١: تأكد إن Python متثبت

افتح الترمينال (أو Command Prompt على ويندوز) واكتب:

```bash
python3 --version
```

لو ظهرلك رقم إصدار **3.10 أو أحدث** (مثال: `Python 3.11.4`)، تمام كمّل.
لو ظهر خطأ "command not found" أو رقم إصدار أقدم من 3.10:

- **ويندوز**: نزّل من https://www.python.org/downloads/ (تأكد تعلّم
  خانة "Add Python to PATH" وقت التثبيت)
- **Mac**: `brew install python3` (لو عندك Homebrew)، أو نزّل من نفس الرابط
- **Linux**: `sudo apt install python3 python3-pip python3-venv` (Ubuntu/Debian)

---

## الخطوة ٢: فك ضغط المشروع

فك ضغط ملف `jarvis_agent.zip` في أي مكان مناسب، مثلاً سطح المكتب.
افتح الترمينال وادخل على المجلد:

```bash
cd المسار/إلى/jarvis_agent
```

---

## الخطوة ٣: اعمل بيئة افتراضية (Virtual Environment)

ده بيمنع تعارض المكتبات مع أي برامج بايثون تانية على الجهاز:

```bash
python3 -m venv venv
```

بعدين فعّلها:

```bash
# على Linux / Mac:
source venv/bin/activate

# على ويندوز (Command Prompt):
venv\Scripts\activate.bat

# على ويندوز (PowerShell):
venv\Scripts\Activate.ps1
```

لو اتفعّلت صح، هتلاقي `(venv)` ظاهرة في أول السطر في الترمينال.

**ملحوظة**: كل مرة تفتح ترمينال جديد وتيجي تشغّل المشروع، لازم تعمل
الخطوة دي (تفعيل venv) تاني الأول.

---

## الخطوة ٤: ثبّت المكتبات

### الطريقة السريعة (سكريبت أوتوماتيكي):

```bash
# على Linux / Mac:
bash install.sh

# على ويندوز:
install.bat
```

### أو يدويًا لو حبيت تتحكم في اللي بيتركب بالظبط:

```bash
pip install -r requirements-core.txt          # لازم دايمًا

pip install -r requirements-gmail.txt          # اختياري: تنظيف Gmail
pip install -r requirements-telegram.txt       # اختياري: بوت تليجرام
pip install -r requirements-office.txt         # اختياري: Word/Excel/PowerPoint
pip install -r requirements-files.txt          # اختياري: نقل ملفات لسلة المهملات
pip install -r requirements-images.txt         # اختياري: تعديل صور
```

---

## الخطوة ٥: حط مفتاح Claude API

لو معندكش مفتاح، اعمله من https://console.anthropic.com

```bash
# Linux / Mac:
export ANTHROPIC_API_KEY="sk-ant-مفتاحك-هنا"

# ويندوز (Command Prompt):
set ANTHROPIC_API_KEY=sk-ant-مفتاحك-هنا

# ويندوز (PowerShell):
$env:ANTHROPIC_API_KEY="sk-ant-مفتاحك-هنا"
```

⚠️ **ده بيفضل شغال بس في الترمينال المفتوح ده**. لو قفلت الترمينال
وفتحته تاني، لازم تكرر الأمر ده. لو عايز يبقى دائم، ضيفه في ملف
`~/.bashrc` أو `~/.zshrc` (Linux/Mac) أو Environment Variables
(ويندوز، من إعدادات النظام).

---

## الخطوة ٦: افحص إن كل حاجة جاهزة

```bash
python check_setup.py
```

هيديك تقرير واضح: إيه الشغال ✅ وإيه الناقص ❌ وإيه بالظبط تعمله.

---

## الخطوة ٧: شغّل الوكيل

```bash
python cli.py
```

المفروض تشوف:
```
I am your friend Jarvis. How can I help you, my friend?
```

اكتب أي حاجة وجرب. اكتب `exit` أو `خروج` للخروج.

---

## تفعيل تكاملات إضافية (Gmail، تليجرام)

دي محتاجة خطوات إعداد منفصلة (تسجيل دخول حسابك، إنشاء توكنات).
راجع قسم **"التكاملات الحالية"** في ملف `README.md` للتفاصيل الكاملة
خطوة بخطوة.

---

## حل المشاكل الشائعة

| المشكلة | الحل |
|---|---|
| `ModuleNotFoundError: No module named 'anthropic'` | نسيت تفعّل الـ venv، أو نسيت `pip install -r requirements-core.txt` |
| `ANTHROPIC_API_KEY مش متحدد` | راجع الخطوة ٥، وتأكد إنك في نفس الترمينال اللي عملت فيه export |
| `command not found: python3` | Python مش متثبت أو مش في PATH، راجع الخطوة ١ |
| البرنامج بطيء أول مرة | طبيعي، عمليات الشبكة (API calls) بتاخد وقت حسب سرعة النت |
| كتابة مبهمة/غريبة لما تشغّل `.bat` | تأكد إنك مستخدم أحدث نسخة من الملفات المرفقة - فيها إصلاح لباج قديم في `cmd.exe` بيبوظ مع النصوص العربي جوه ملفات batch |
| الترمينال بيقفل فجأة من غير ما تقرأ الخطأ | كل نسخة محدّثة من `install.bat` و`Jarvis.bat` بتوقف بـ `pause` قبل أي خروج - لو لسه بيقفل فورًا، يبقى معاك نسخة قديمة، حمّل الملفات الجديدة تاني |
