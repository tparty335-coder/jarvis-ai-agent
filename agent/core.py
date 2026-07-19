"""
core.py
-------
نواة تشغيل Jarvis باستخدام Google Gemini API بدلًا من Anthropic,
تدعم استدعاء الأدوات بشكل متكرر حتى إتمام المهمة.
"""

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

from .config import settings
from .memory import Memory
from .tools import TOOL_SCHEMAS, execute_tool

def convert_schema(a_schema: dict) -> FunctionDeclaration:
    # نقوم بتحويل بنية أدوات Anthropic القديمة إلى بنية أدوات Gemini (OpenAPI)
    input_schema = a_schema.get("input_schema", {"type": "object", "properties": {}})
    return FunctionDeclaration(
        name=a_schema["name"],
        description=a_schema["description"],
        parameters=input_schema
    )

class JarvisAgent:
    def __init__(self):
        if not settings.google_api_key:
            raise RuntimeError("مفتاح GOOGLE_API_KEY غير متوفر. الرجاء إدخاله أولاً.")
        genai.configure(api_key=settings.google_api_key)
        
        funcs = [convert_schema(s) for s in TOOL_SCHEMAS]
        self.gemini_tool = Tool(function_declarations=funcs)
        
        self.memory = Memory()
        # يتم بناء الموديل مع إعطائه الـ system_instruction (التي تتغير مع الذاكرة) عند كل محادثة
        # لتفادي تكرار التجهيز، سنقوم بإنشاء המודل عند start_turn

    def _build_system_prompt(self) -> str:
        base = settings.rendered_system_prompt()
        facts_block = self.memory.facts_as_context_block()
        if facts_block:
            return f"{base}\n\n{facts_block}"
        return base

    def run_turn(self, user_message: str) -> str:
        self.memory.log_message("user", user_message)

        # استرجاع الرسائل السابقة وتحويلها لتلائم صيغة Gemini
        raw_history = self.memory.recent_history(limit=10)
        formatted_history = []
        for msg in raw_history:
            role = "model" if msg["role"] == "assistant" else "user"
            content = msg["content"]
            if isinstance(content, list):
                # تنظيف الرسائل المعقدة الناتجة من جلسات سابقة
                clean_text = " ".join([str(c) for c in content if isinstance(c, (str, int, float))])
                content = clean_text or ""
            if not content.strip():
                content = "---"
            formatted_history.append({"role": role, "parts": [{"text": str(content)}]})

        model = genai.GenerativeModel(
            model_name=settings.model,
            system_instruction=self._build_system_prompt(),
            tools=[self.gemini_tool]
        )
        
        chat = model.start_chat()
        # No history passed to chat explicitly because history from previous turns might contain Anthropic formats or tool calls that Gemini strict history validation rejects.
        # Instead, we just inject the history directly in the first prompt for context, to avoid Gemini rejection on strict schema validations.
        
        context_str = ""
        if formatted_history:
            context_str = "السياق السابق للمحادثة لمساعدتك:\n"
            for h in formatted_history:
                context_str += f"{h['role']}: {h['parts'][0]['text']}\n"
            context_str += "\nالرسالة الحالية:\n"
            
        current_msg = context_str + user_message
        
        final_text_parts = []
        
        for _ in range(settings.max_agent_turns):
            try:
                response = chat.send_message(current_msg)
            except Exception as exc:
                return f"حصل خطأ أثناء التواصل مع سيرفر Gemini: {exc}"
            
            if response.parts:
                for part in response.parts:
                    if hasattr(part, "text") and part.text:
                        final_text_parts.append(part.text)
                        
            if not response.function_calls:
                break
                
            # إذا تطلب الأمر أدوات
            function_responses = []
            for fc in response.function_calls:
                tool_name = fc.name
                tool_input = dict(fc.args) if fc.args else {}
                result_str = execute_tool(tool_name, tool_input)
                function_responses.append(
                    genai.types.Part.from_function_response(
                        name=tool_name, 
                        response={"result": str(result_str)[:2000]} # Limit result length to prevent token overflow
                    )
                )
            
            current_msg = function_responses
            
        final_answer = "\n".join(final_text_parts).strip() or "(أتممت المهمة دون تعليق)"
        self.memory.log_message("assistant", final_answer)
        return final_answer
