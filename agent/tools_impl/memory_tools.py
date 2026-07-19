"""
memory_tools.py
---------------
دي الأدوات اللي بتخلي الموديل نفسه (مش الكود اللي حواليه) يقرر يحفظ
أو يسترجع معلومة من الذاكرة الدائمة. الفرق عن memory.py: ده الـ "واجهة"
اللي الموديل شايفها كـ tools، وmemory.py هو التخزين الفعلي.
"""

from ..memory import Memory
from ..security import contains_financial_data

_memory = Memory()


def remember(key: str, value: str) -> str:
    if contains_financial_data(value) or contains_financial_data(key):
        return (
            "تم رفض الحفظ: القيمة دي بتحتوي على ما يبدو ببيانات مالية حساسة "
            "(رقم بطاقة، كلمة سر، رقم حساب، أو ما شابه). النظام مُعد بشكل صارم "
            "على عدم تخزين هذا النوع من البيانات في الذاكرة الدائمة، بغض النظر "
            "عن سبب الطلب."
        )
    _memory.remember_fact(key, value)
    return f"تم الحفظ: {key} = {value}"


def recall(key: str) -> str:
    value = _memory.recall_fact(key)
    return value if value is not None else f"مفيش معلومة محفوظة تحت المفتاح: {key}"


def list_memories() -> str:
    facts = _memory.all_facts()
    if not facts:
        return "الذاكرة فاضية دلوقتي."
    return "\n".join(f"- {k}: {v}" for k, v in facts.items())


REMEMBER_SCHEMA = {
    "name": "remember",
    "description": (
        "يحفظ حقيقة دائمة عن المستخدم أو مشروعه في الذاكرة طويلة المدى، "
        "عشان تفتكرها في محادثات جاية. استخدمها كل ما تكتشف معلومة مهمة "
        "ومستقرة (اسم، تفضيل، اسم مشروع، إلخ)، مش معلومات مؤقتة."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "مفتاح قصير يعبر عن نوع المعلومة، مثال: 'user_name'"},
            "value": {"type": "string", "description": "قيمة المعلومة"},
        },
        "required": ["key", "value"],
    },
}

RECALL_SCHEMA = {
    "name": "recall",
    "description": "يسترجع معلومة محددة كانت متخزنة سابقًا في الذاكرة الدائمة عن طريق مفتاحها.",
    "input_schema": {
        "type": "object",
        "properties": {"key": {"type": "string", "description": "المفتاح المطلوب استرجاعه"}},
        "required": ["key"],
    },
}

LIST_MEMORIES_SCHEMA = {
    "name": "list_memories",
    "description": "يعرض كل الحقائق المحفوظة حاليًا في الذاكرة الدائمة.",
    "input_schema": {"type": "object", "properties": {}, "required": []},
}
