# Jarvis AI Agent - Architecture Overview

## Introduction
Jarvis is transitioning from a simple text-based conversational wrapper into a true **System Agent**. This document outlines the fundamental architecture necessary to ensure the core logic scales without becoming highly coupled to strict UI implementations or specific LLMs.

## Core Architectural Philosophies
1. **YAGNI (You Aren't Gonna Need It) & Proactiveness**: Keep it simple today, but lay the interfaces for tomorrow.
2. **Safety First (Human-in-the-Loop)**: The AI does not execute high-risk OS functions without explicit user affirmation via UI dialogs.
3. **Decoupled Engine**: The core AI logic, the TTS (Text-to-Speech) module, and the GUI operate autonomously to prevent GUI thread freezes.

---

## 1. Tool Registry Pattern (The "Function Calling" Catalog)

Instead of hardcoding a massive `if-else` chain of tools, Jarvis uses a **Tool Registry**.

### Current Implementation
Tools are stored conceptually under `tools_impl/`:
- `office_tools.py`: Interacting with Word, Excel, PowerPoint.
- `web_tools.py`: Simple search or fetch operations.
- `system_tools.py`: OS-level execution (shutdown, volume control, process killing).

**Evolution:**
The registry should dynamically parse these files. When we initialize the API (e.g. Gemini), we supply a JSON-schema representation of this registry so Gemini knows exactly what it can trigger.

---

## 2. The AI Provider Interface (Agnostic Bridge)

Jarvis currently uses `google-genai`. To ensure longevity, we abstract the AI interaction layer:
```python
class AIProvider:
    def chat(self, prompt: str) -> str:
        pass
    
    def process_function_call(self, tool_name: str, args: dict) -> str:
        pass
```
If Google changes its API drastically, or if we switch to an offline Model (Llama 3), we only write a new `LocalAIProvider` implementing this interface. The core `brain` of Jarvis remains completely untouched.

---

## 3. Human-In-The-Loop Safety (The Shield)

**Problem:** Gemini deciding to run `shutdown_pc()` arbitrarily because it misunderstood "I want to shut down my work" is a massive security risk.

**Solution:**
Within `system_tools.py`, highly destructive functions are flagged `@requires_confirmation`. 
When the LLM triggers such a tool, the Backend halts the execution and emits a `SAFETY_HALT` signal to the GUI. The GUI (PyQt6) triggers a modal `QMessageBox` asking the user. The tool only proceeds upon receiving the `True` callback.

---

## 4. State Management & Memory

Jarvis leverages persistent local memory so Context is preserved across restarts:
1. **Fact Memory (SQLite)**: Core configuration and user facts ("Call me Boss").
2. **Chat Timeline**: Previous interactions loaded at runtime to resume sessions seamlessly.

## 5. UI Dashboard / "Action vs Chat" Separation
The GUI (`gui.py`) is visually split (or conceptually split in future updates):
- **Right Panel**: Chat history (Timeline).
- **Center/Left Panel**: State representation (Orb animation, Tool Execution Indicators, Network Status).

*Document finalized as part of Phase 6 Architecture proactiveness.*
