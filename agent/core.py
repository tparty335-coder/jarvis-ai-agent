"""
core.py
-------
نواة تشغيل Jarvis باستخدام Google Gemini API (الحزمة الجديدة google-genai),
تدعم استدعاء الأدوات بشكل متكرر حتى إتمام المهمة.
"""

from google import genai
from google.genai import types

from .config import settings
from .memory import Memory
from .tools import TOOL_SCHEMAS, execute_tool


def convert_schema(a_schema: dict) -> types.FunctionDeclaration:
    """تحويل بنية أدوات (Anthropic-style) إلى بنية أدوات Gemini الجديدة"""
    input_schema = a_schema.get("input_schema", {"type": "object", "properties": {}})
    return types.FunctionDeclaration(
        name=a_schema["name"],
        description=a_schema["description"],
        parameters=input_schema
    )


class JarvisAgent:
    def __init__(self):
        if not settings.google_api_key:
            raise RuntimeError("مفتاح GOOGLE_API_KEY غير متوفر. الرجاء إدخاله أولاً.")
        
        self.client = genai.Client(api_key=settings.google_api_key)
        
        funcs = [convert_schema(s) for s in TOOL_SCHEMAS]
        self.gemini_tool = types.Tool(function_declarations=funcs)
        
        self.memory = Memory()

    def _build_system_prompt(self) -> str:
        base = settings.rendered_system_prompt()
        facts_block = self.memory.facts_as_context_block()
        if facts_block:
            return f"{base}\n\n{facts_block}"
        return base

    def run_turn(self, user_message: str) -> str:
        self.memory.log_message("user", user_message)

        # استرجاع الرسائل السابقة وتحويلها لسياق نصي
        raw_history = self.memory.recent_history(limit=10)
        
        context_str = ""
        if raw_history:
            context_str = "السياق السابق للمحادثة لمساعدتك:\n"
            for msg in raw_history:
                role = "model" if msg["role"] == "assistant" else "user"
                content = msg["content"]
                if isinstance(content, list):
                    clean_text = " ".join([str(c) for c in content if isinstance(c, (str, int, float))])
                    content = clean_text or ""
                if not str(content).strip():
                    content = "---"
                context_str += f"{role}: {content}\n"
            context_str += "\nالرسالة الحالية:\n"
            
        current_msg = context_str + user_message
        
        # بناء محتوى المحادثة
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=current_msg)])]
        
        config = types.GenerateContentConfig(
            system_instruction=self._build_system_prompt(),
            tools=[self.gemini_tool],
            max_output_tokens=settings.max_tokens,
        )
        
        import time
        
        # قائمة الموديلات للتجربة بالترتيب (fallback)
        models_to_try = [
            settings.model,         # gemini-3.5-flash
            "gemini-3-flash-preview",
            "gemini-3.1-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ]
        # إزالة التكرارات مع الحفاظ على الترتيب
        seen = set()
        models_to_try = [m for m in models_to_try if m not in seen and not seen.add(m)]
        
        final_text_parts = []
        
        for _ in range(settings.max_agent_turns):
            response = None
            last_error = None
            for model_name in models_to_try:
                for attempt in range(2):  # محاولتين لكل موديل
                    try:
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=config,
                        )
                        break  # نجح!
                    except Exception as exc:
                        last_error = exc
                        err_str = str(exc)
                        if "429" in err_str or "503" in err_str:
                            if attempt == 0 and "503" in err_str:
                                time.sleep(3)  # انتظر قبل إعادة المحاولة
                                continue
                            break  # جرب الموديل التالي
                        else:
                            return f"حصل خطأ أثناء التواصل مع سيرفر Gemini: {exc}"
                if response:
                    break
            
            if not response:
                return f"عذراً، جميع الموديلات مشغولة حالياً. حاول مرة تانية بعد دقيقة.\nالتفاصيل: {last_error}"
            
            # جمع النصوص من الرد
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        final_text_parts.append(part.text)
            
            # فحص هل فيه استدعاءات أدوات
            function_calls = []
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
            
            if not function_calls:
                break
                
            # تنفيذ الأدوات وإرسال النتائج
            # إضافة رد الموديل للمحادثة
            contents.append(response.candidates[0].content)
            
            # تنفيذ كل أداة وجمع النتائج
            function_response_parts = []
            for fc in function_calls:
                tool_name = fc.name
                tool_input = dict(fc.args) if fc.args else {}
                result_str = execute_tool(tool_name, tool_input)
                
                if isinstance(result_str, str) and result_str.startswith("[IMAGE_ATTACH]"):
                    img_path = result_str.split("\n", 1)[0].replace("[IMAGE_ATTACH]", "").strip()
                    try:
                        import PIL.Image
                        img = PIL.Image.open(img_path)
                        # Must return function_response to close the AI's call
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name=tool_name, 
                                response={"result": "Screenshot captured successfully. I have attached the image for you to see."}
                            )
                        )
                        # Attach the image directly alongside the response
                        function_response_parts.append(types.Part.from_image(img))
                    except Exception as e:
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name=tool_name, 
                                response={"result": f"Failed to attach image: {e}"}
                            )
                        )
                else:
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name, 
                            response={"result": str(result_str)[:2000]}
                        )
                    )
            
            # إضافة نتائج الأدوات كرسالة user
            contents.append(types.Content(role="user", parts=function_response_parts))
            
        final_answer = "\n".join(final_text_parts).strip() or "(أتممت المهمة دون تعليق)"
        self.memory.log_message("assistant", final_answer)
        return final_answer
