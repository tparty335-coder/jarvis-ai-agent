import sys
import os
import threading
import traceback
import speech_recognition as sr
import pyttsx3

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QLineEdit, QDialog, QStackedWidget,
    QMessageBox, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF, pyqtSlot
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QIcon, QAction

# Attempt to lazy load the agent to prevent slow startup
# from agent.core import JarvisAgent

class SetupPage(QWidget):
    key_saved = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel("Welcome to J.A.R.V.I.S")
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #45a29e;")
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sub_lbl = QLabel("Please enter your GOOGLE_API_KEY to continue.")
        sub_lbl.setStyleSheet("font-size: 14px; color: #c5c6c7;")
        layout.addWidget(sub_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIzaSy...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setFixedWidth(300)
        self.key_input.setStyleSheet("padding: 8px; border: 1px solid #45a29e; border-radius: 4px; background: #1f2833; color: white;")
        layout.addWidget(self.key_input, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn = QPushButton("Save & Start")
        btn.setFixedWidth(150)
        btn.setStyleSheet("background: #45a29e; color: #0b0c10; font-weight: bold; padding: 10px; border-radius: 4px;")
        btn.clicked.connect(self.save_key)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def save_key(self):
        key = self.key_input.text().strip()
        if key:
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            with open(env_path, "a", encoding="utf-8") as f:
                f.write(f"\nGOOGLE_API_KEY={key}\n")
            os.environ["GOOGLE_API_KEY"] = key
            self.key_saved.emit(key)

class JarvisOrb(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(60, 60)
        self.scale = 1.0
        self.growing = True
        self.mode = "idle" # idle, listening, processing, speaking
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def set_mode(self, mode):
        self.mode = mode

    def animate(self):
        step = 0.05 if self.mode != "idle" else 0.02
        if self.growing:
            self.scale += step
            if self.scale > 1.2: self.growing = False
        else:
            self.scale -= step
            if self.scale < 0.8: self.growing = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = self.width() / 2, self.height() / 2
        radius = 20 * self.scale
        
        if self.mode == "idle":
            color = QColor(69, 162, 158)    # Cyan
        elif self.mode == "listening":
            color = QColor(255, 100, 100)   # Red
        elif self.mode == "processing":
            color = QColor(255, 200, 0)     # Yellow
        elif self.mode == "speaking":
            color = QColor(100, 255, 100)   # Green
        else:
            color = QColor(100, 100, 100)
            
        # Draw Glow
        for i in range(4, 0, -1):
            alpha = int(255 * (0.2 / i))
            glow_color = QColor(color.red(), color.green(), color.blue(), alpha)
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - radius*i*0.4, cy - radius*i*0.4, radius*i*0.8, radius*i*0.8))

        # Core
        painter.setBrush(color)
        painter.setPen(QPen(QColor(255,255,255), 2))
        painter.drawEllipse(QRectF(cx - radius*0.4, cy - radius*0.4, radius*0.8, radius*0.8))

class ChatPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 1. STATUS HEADER
        header_layout = QHBoxLayout()
        self.status_lbl = QLabel("🟢 System Idle")
        self.status_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #45a29e;")
        header_layout.addWidget(self.status_lbl)
        header_layout.addStretch()
        
        self.orb = JarvisOrb()
        header_layout.addWidget(self.orb)
        layout.addLayout(header_layout)
        
        # 2. ACTION TIMELINE
        layout.addWidget(QLabel("Action Timeline"))
        self.timeline_list = QListWidget()
        self.timeline_list.setMaximumHeight(150)
        self.timeline_list.setStyleSheet("""
            QListWidget { background: #121820; border: 1px solid #1f2833; border-radius: 4px; padding: 5px; color: #8a9ba8; font-family: Consolas, monospace; font-size: 13px; }
        """)
        layout.addWidget(self.timeline_list)
        
        # 3. CHAT DISPLAY
        layout.addWidget(QLabel("Conversation"))
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setStyleSheet("""
            QTextEdit { background: #1f2833; border: 1px solid #45a29e; border-radius: 4px; padding: 10px; color: #e8e8e8; font-size: 14px; }
        """)
        layout.addWidget(self.chat)
        
        # 4. INPUT ROW
        row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Send command to Jarvis...")
        self.input_field.setStyleSheet("background: #1f2833; padding: 10px; border: 1px solid #45a29e; border-radius: 4px; color: white;")
        row.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("background: #45a29e; color: #0b0c10; font-weight: bold; padding: 10px; border-radius: 4px;")
        row.addWidget(self.send_btn)
        
        self.voice_btn = QPushButton("🎤 Voice")
        self.voice_btn.setStyleSheet("background: #c5c6c7; color: #0b0c10; font-weight: bold; padding: 10px; border-radius: 4px;")
        row.addWidget(self.voice_btn)
        
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setVisible(False)
        self.stop_btn.setStyleSheet("background: #e74c3c; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        row.addWidget(self.stop_btn)
        
        self.silent_btn = QPushButton("🔇 Silent")
        self.silent_btn.setCheckable(True)
        self.silent_btn.setStyleSheet("background: #1f2833; color: #c5c6c7; font-weight: bold; padding: 10px; border-radius: 4px; border: 1px solid #45a29e;")
        row.addWidget(self.silent_btn)
        
        layout.addLayout(row)

    def log_chat(self, text):
        self.chat.append(text + "\n")
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())
        
    def add_timeline_event(self, event_text, icon="⚡"):
        item = QListWidgetItem(f"{icon} {event_text}")
        self.timeline_list.addItem(item)
        self.timeline_list.scrollToBottom()

class TTSEngine(QThread):
    finished = pyqtSignal()
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.stopped = False
    
    def run(self):
        try:
            tts = pyttsx3.init()
            tts.setProperty('rate', 150)
            for voice in tts.getProperty('voices'):
                if 'arabic' in voice.name.lower() or 'ar' in voice.id:
                    tts.setProperty('voice', voice.id)
                    break
            if not self.stopped:
                tts.say(self.text)
                tts.runAndWait()
        except:
            pass
        self.finished.emit()

    def stop(self):
        self.stopped = True

class STTEngine(QThread):
    transcribed = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio, language="ar-EG")
                self.transcribed.emit(text)
            except Exception as e:
                self.error.emit(str(e))
        self.finished.emit()

class AgentWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, agent, text):
        super().__init__()
        self.agent = agent
        self.text = text
    def run(self):
        try:
            reply = self.agent.run_turn(self.text)
            self.finished.emit(reply)
        except Exception as e:
            self.finished.emit(f"Error: {e}")


class HotwordListener(QThread):
    wake_signal = pyqtSignal()
    sleep_signal = pyqtSignal()
    timeline_signal = pyqtSignal(str, str) # For emitting errors
    
    def run(self):
        import time
        recognizer = sr.Recognizer()
        # Set a high threshold so it doesn't send background noise to Google constantly
        recognizer.energy_threshold = 3000 
        recognizer.dynamic_energy_threshold = True
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            while True:
                try:
                    # Listen for very short bursts
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    try:
                        text = recognizer.recognize_google(audio, language="en-US").lower()
                        if "wake" in text and "jarvis" in text:
                            self.wake_signal.emit()
                            continue
                        elif "sleep" in text and "jarvis" in text:
                            self.sleep_signal.emit()
                            continue
                    except sr.UnknownValueError:
                        pass
                        
                    # Backup Arabic check only if English didn't match and didn't crash on RequestError
                    text_ar = recognizer.recognize_google(audio, language="ar-EG")
                    if "صحى" in text_ar or "افتح" in text_ar:
                        self.wake_signal.emit()
                    elif "نام" in text_ar or "اخفي" in text_ar:
                        self.sleep_signal.emit()
                        
                except sr.WaitTimeoutError:
                    pass # Normal timeout, just loop again
                except sr.RequestError as e:
                    self.timeline_signal.emit(f"Google API rate limit hit. Pausing background listening for 60s.", "🚫")
                    time.sleep(60) # Sleep heavily to allow rate limits to reset
                except Exception as e:
                    pass # Ignore other random errors and keep listening

STYLE = """
QMainWindow, QWidget { background-color: #0b0c10; color: #c5c6c7; font-family: 'Segoe UI', Arial; }
"""

class MainWindow(QMainWindow):
    safety_request_signal = pyqtSignal(str, str)
    timeline_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.safety_event = threading.Event()
        self.safety_response = False
        
        self.safety_request_signal.connect(self.handle_safety_request)
        self.timeline_signal.connect(self.handle_timeline_update)
        
        # Patch tools.py
        try:
            import agent.tools as agent_tools
            agent_tools.SAFETY_CONFIRM_CALLBACK = self.safety_callback_wrapper
            agent_tools.TIMELINE_LOG_CALLBACK = self.timeline_callback_wrapper
        except Exception:
            pass

        self.setWindowTitle("J.A.R.V.I.S — Live Command Center")
        self.resize(720, 820)
        self.setStyleSheet(STYLE)
        
        # System Tray Setup
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "jarvis.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback to standard icon
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
        tray_menu = QMenu()
        show_action = QAction("Open Jarvis", self)
        show_action.triggered.connect(self.wake_up)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
        
        # Start Background Hotword Listener
        self.hotword_thread = HotwordListener()
        self.hotword_thread.wake_signal.connect(self.wake_up)
        self.hotword_thread.sleep_signal.connect(self.go_to_sleep)
        self.hotword_thread.timeline_signal.connect(self.handle_timeline_update)
        self.hotword_thread.start()
        
        self.agent = None
        self._tts = None
        self._stt = None
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.setup_page = SetupPage()
        self.chat_page = ChatPage()
        self.stack.addWidget(self.setup_page)
        self.stack.addWidget(self.chat_page)
        
        self.setup_page.key_saved.connect(self._init_agent_and_go)
        self.chat_page.send_btn.clicked.connect(self.send_message)
        self.chat_page.voice_btn.clicked.connect(self.start_listening)
        self.chat_page.stop_btn.clicked.connect(self.stop_speaking)
        self.chat_page.silent_btn.toggled.connect(self._toggle_silent)
        self.chat_page.input_field.returnPressed.connect(self.send_message)
        
        self.silent_mode = False
        
        self._load_existing_key()

    def _load_existing_key(self):
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        if key:
                            os.environ["GOOGLE_API_KEY"] = key
                            self._init_agent_and_go()
                            return
        self.stack.setCurrentIndex(0)

    def safety_callback_wrapper(self, name, args):
        self.timeline_signal.emit(f"Security override requested for: {name}", "🛡️")
        self.safety_event.clear()
        self.safety_request_signal.emit(name, str(args))
        self.safety_event.wait()
        return self.safety_response
        
    def timeline_callback_wrapper(self, msg, icon="⚡"):
        self.timeline_signal.emit(msg, icon)

    @pyqtSlot(str, str)
    def handle_timeline_update(self, msg, icon):
        self.chat_page.add_timeline_event(msg, icon)

    @pyqtSlot(str, str)
    def handle_safety_request(self, tool_name, tool_args):
        reply = QMessageBox.question(
            self, "Security Alert 🛡️",
            f"Jarvis is attempting a restricted action:\n\nTool: {tool_name}\nArgs: {tool_args}\n\nAllow execution?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        self.safety_response = (reply == QMessageBox.StandardButton.Yes)
        status_msg = "Authorized" if self.safety_response else "Denied"
        self.chat_page.add_timeline_event(f"{tool_name} execution {status_msg}", "🔒")
        self.safety_event.set()

    def _init_agent_and_go(self):
        init_error = None
        try:
            from agent.core import JarvisAgent
            self.agent = JarvisAgent()
        except Exception as e:
            init_error = e
            self.agent = None
            
        self.stack.setCurrentIndex(1)
        if self.agent:
            self.chat_page.add_timeline_event("Agent initialized successfully.", "🌐")
            past_messages = self.agent.memory.recent_history(limit=50)
            if past_messages:
                self.chat_page.log_chat("─── [History] ───")
                for msg in past_messages:
                    name = "👤 You" if msg["role"] == "user" else "🧠 Jarvis"
                    self.chat_page.log_chat(f"{name}:\n{msg['content']}\n")
            else:
                greeting = "مرحباً! أنا جارفيس، كيف أقدر أساعدك؟"
                self.chat_page.log_chat(f"🧠 Jarvis:\n{greeting}")
                if not self.silent_mode:
                    self.speak(greeting)
        else:
            self.chat_page.add_timeline_event(f"Failed to load agent: {init_error}", "❌")
            
    def _toggle_silent(self, checked):
        self.silent_mode = checked
        if checked:
            self.chat_page.silent_btn.setStyleSheet("background: #e74c3c; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
            self.chat_page.silent_btn.setText("🔇 Silent ON")
            self.chat_page.add_timeline_event("Silent mode ON — no voice output.", "🔇")
        else:
            self.chat_page.silent_btn.setStyleSheet("background: #1f2833; color: #c5c6c7; font-weight: bold; padding: 10px; border-radius: 4px; border: 1px solid #45a29e;")
            self.chat_page.silent_btn.setText("🔇 Silent")
            self.chat_page.add_timeline_event("Silent mode OFF — voice output enabled.", "🔊")

    def speak(self, text):
        if self.silent_mode:
            return  # Skip TTS entirely in silent mode
        self.chat_page.orb.set_mode("speaking")
        self.chat_page.status_lbl.setText("🔊 Speaking...")
        self.chat_page.stop_btn.setVisible(True)
        self._tts = TTSEngine(text)
        self._tts.finished.connect(self._tts_done)
        self._tts.start()

    def _tts_done(self):
        self.chat_page.orb.set_mode("idle")
        self.chat_page.status_lbl.setText("🟢 System Idle")
        self.chat_page.stop_btn.setVisible(False)

    def stop_speaking(self):
        if self._tts and self._tts.isRunning():
            self._tts.stop()
            self.chat_page.add_timeline_event("TTS interrupted by user.", "🔇")
        self._tts_done()

    def start_listening(self):
        self.chat_page.orb.set_mode("listening")
        self.chat_page.status_lbl.setText("🎤 Listening...")
        self.chat_page.voice_btn.setEnabled(False)
        self.chat_page.send_btn.setEnabled(False)
        self._stt = STTEngine()
        self._stt.transcribed.connect(self.send_message)
        self._stt.error.connect(lambda e: self.chat_page.add_timeline_event(f"STT Error: {e}", "⚠️"))
        self._stt.finished.connect(self._stt_done)
        self._stt.start()

    def _stt_done(self):
        self.chat_page.orb.set_mode("idle")
        self.chat_page.voice_btn.setEnabled(True)
        self.chat_page.send_btn.setEnabled(True)
        if "🎤" in self.chat_page.status_lbl.text():
            self.chat_page.status_lbl.setText("🟢 System Idle")

    def send_message(self, text=None):
        if not isinstance(text, str) or not text.strip():
            text = self.chat_page.input_field.text().strip()
        if not text: return
        
        self.chat_page.input_field.clear()
        self.chat_page.log_chat(f"👤 You:\n{text}")
        self.chat_page.add_timeline_event(f"Received prompt: {text[:20]}...", "💬")
        
        self.chat_page.orb.set_mode("processing")
        self.chat_page.status_lbl.setText("🟡 Thinking...")
        for btn in (self.chat_page.send_btn, self.chat_page.voice_btn): btn.setEnabled(False)
        self.chat_page.input_field.setEnabled(False)

        if self.agent is None:
            self.chat_page.add_timeline_event("Agent not loaded.", "❌")
            self._unlock()
            return

        self._worker = AgentWorker(self.agent, text)
        self._worker.finished.connect(self._on_reply)
        self._worker.start()

    def _on_reply(self, reply):
        self._unlock()
        self.chat_page.add_timeline_event("Response generated.", "✅")
        self.chat_page.log_chat(f"🧠 Jarvis:\n{reply}")
        self.speak(reply)

    def _unlock(self):
        self.chat_page.orb.set_mode("idle")
        self.chat_page.status_lbl.setText("🟢 System Idle")
        for btn in (self.chat_page.send_btn, self.chat_page.voice_btn): btn.setEnabled(True)
        self.chat_page.input_field.setEnabled(True)



    def closeEvent(self, event):
        event.ignore()
        self.go_to_sleep()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.wake_up()

    @pyqtSlot()
    def wake_up(self):
        self.showNormal()
        self.activateWindow()
        self.chat_page.add_timeline_event("Jarvis Woken Up", "👁️")

    @pyqtSlot()
    def go_to_sleep(self):
        self.hide()
        self.tray_icon.showMessage(
            "J.A.R.V.I.S",
            "I'm going to sleep. Say 'Wake up Jarvis' to call me.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

def main():
    try:
        app = QApplication(sys.argv)
        win = MainWindow()
        win.show()
        sys.exit(app.exec())
    except Exception:
        with open("error_crash.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    main()
