"""
calculator.py
-------------
أداة حسابية آمنة. مش بنستخدم eval() المباشر لأنه بيسمح بتنفيذ أي كود بايثون
(خطر أمني حقيقي لو جالك input غريب). بدل كده بنستخدم مكتبة `ast` عشان نتأكد
إن اللي جاي عبارة عن تعبير رياضي بحت فقط، مفيش استدعاء دوال أو استيراد.
"""

import ast
import operator as op

# العمليات المسموح بيها فقط
ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("قيمة غير مسموح بيها في التعبير")
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"عنصر غير مسموح بيه في التعبير الحسابي: {type(node).__name__}")


def calculate(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except Exception as exc:
        return f"خطأ في حساب التعبير: {exc}"


TOOL_SCHEMA = {
    "name": "calculator",
    "description": "يحسب تعبير رياضي (جمع، طرح، ضرب، قسمة، أس، باقي القسمة). استخدمه لأي حساب دقيق بدل ما تخمّن الرقم.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "التعبير الرياضي كنص، مثال: '(15 + 7) * 3'",
            }
        },
        "required": ["expression"],
    },
}
