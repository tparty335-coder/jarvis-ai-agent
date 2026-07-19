"""
web.py
------
بحث بسيط في الإنترنت. بنستخدم HTML endpoint بتاع DuckDuckGo لأنه مش محتاج
مفتاح API ولا اشتراك، مناسب كبداية. لو المشروع كبر وحبيت نتائج أدق،
تقدر تستبدلها بـ Brave Search API أو Serper.dev أو حتى بتفعيل أداة
web_search المدمجة في Claude API نفسها (built-in tool من أنثروبيك).
"""

import httpx
from html.parser import HTMLParser


class _ResultParser(HTMLParser):
    """بارسر بسيط يسحب العناوين والروابط من صفحة نتائج DuckDuckGo"""

    def __init__(self):
        super().__init__()
        self.results = []
        self._in_result_link = False
        self._current_href = None
        self._current_text = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "result__a" in attrs_dict.get("class", ""):
            self._in_result_link = True
            self._current_href = attrs_dict.get("href", "")
            self._current_text = []

    def handle_data(self, data):
        if self._in_result_link:
            self._current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_result_link:
            self._in_result_link = False
            title = "".join(self._current_text).strip()
            if title and self._current_href:
                self.results.append({"title": title, "url": self._current_href})


def web_search(query: str, max_results: int = 5) -> str:
    try:
        resp = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (JarvisAgent/1.0)"},
            timeout=10.0,
        )
        resp.raise_for_status()
        parser = _ResultParser()
        parser.feed(resp.text)
        results = parser.results[:max_results]
        if not results:
            return "مفيش نتائج."
        lines = [f"{i+1}. {r['title']} — {r['url']}" for i, r in enumerate(results)]
        return "\n".join(lines)
    except Exception as exc:
        return f"خطأ في البحث: {exc}"


def open_browser(url: str = "https://www.google.com") -> str:
    import webbrowser
    try:
        webbrowser.open(url)
        return f"تم فتح المتصفح على الرابط: {url}"
    except Exception as exc:
        return f"حدث خطأ أثناء محاولة فتح المتصفح: {exc}"

TOOL_SCHEMA = {
    "name": "web_search",
    "description": "يبحث في الإنترنت عن معلومة حديثة أو غير موجودة في معرفة الموديل، ويرجع عناوين وروابط النتائج.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "نص البحث"},
            "max_results": {"type": "integer", "description": "أقصى عدد نتائج، افتراضيًا 5"},
        },
        "required": ["query"],
    },
}

OPEN_BROWSER_SCHEMA = {
    "name": "open_browser",
    "description": "يفتح المتصفح الافتراضي في نظام التشغيل على رابط معين.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "الرابط المراد فتحه"}
        },
        "required": ["url"],
    },
}
