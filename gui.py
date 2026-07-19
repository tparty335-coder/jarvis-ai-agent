import sys
import os
import threading

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath

import speech_recognition as sr
import pyttsx3

from agent.config import settings
from agent.core import JarvisAgent

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مفتاح Google Gemini API")
        self.setFixedSize(400, 150)
        self.setStyleSheet("background-color: #121212; color: #00e6e6;")
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("الرجاء إدخال مفتاح GOOGLE_API_KEY الخاص بك:")
        lbl.setFont(QFont("Arial", 10))
        layout.addWidget(lbl)
        
        self.key_input = QLineEdit()
        self.key_input.setStyleSheet("background-color: #1e1e1e; border: 1px solid #00e6e6; padding: 5px;")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.key_input)
        
        btn = QPushButton("حفظ ومتابعة")
        btn.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 5px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class JarvisOrb(QWidget):
    """Aesthetic animated glowing orb (J.A.R.V.I.S style)."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(150, 150)
        self.scale = 1.0
        self.growing = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
        self.is_active = False

    def animate(self):
        step = 0.05 if self.is_active else 0.02
        if self.growing:
            self.scale += step
            if self.scale > 1.2:
                self.growing = False
        else:
            self.scale -= step
            if self.scale < 0.8:
                self.growing = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x, center_y = self.width() / 2, self.height() / 2
        base_radius = 50
        radius = base_radius * self.scale
        
        # Glow
        for i in range(5, 0, -1):
            alpha = int(255 * (0.2 / i))
            color = QColor(0, 230, 230, alpha) if not self.is_active else QColor(230, 50, 50, alpha)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(center_x - radius*i*0.3, center_y - radius*i*0.3, radius*i*0.6, radius*i*0.6))

        # Core
        core_color = QColor(0, 255, 255) if not self.is_active else QColor(255, 100, 100)
        painter.setBrush(core_color)
        pen = QPen(QColor(255,255,255), 2)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(center_x - radius*0.3, center_y - radius*0.3, radius*0.6, radius*0.6))

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
            self.finished.emit(f"خطأ: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مساعد جارفيس (Gemini)")
        self.resize(600, 700)
        self.setStyleSheet("background-color: #0b0c10; color: #66fcf1; font-family: 'Arial';")
        
        self.check_api_key()
        
        # Audio Engine
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 150)
        # Attempt to set Arabic voice if available
        for voice in self.tts.getProperty('voices'):
            if 'arabic' in voice.name.lower() or 'ar' in voice.id:
                self.tts.setProperty('voice', voice.id)
                break
                
        self.recognizer = sr.Recognizer()
        
        try:
            self.agent = JarvisAgent()
        except Exception as e:
            print("فشل في تهيئة Agent:", e)
        
        self._setup_ui()

    def check_api_key(self):
        # Try loading from .env
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        os.environ["GOOGLE_API_KEY"] = line.split("=")[1].strip()
        
        if not os.environ.get("GOOGLE_API_KEY"):
            dialog = ApiKeyDialog(self)
            if dialog.exec():
                key = dialog.key_input.text()
                os.environ["GOOGLE_API_KEY"] = key
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"GOOGLE_API_KEY={key}\n")
            else:
                sys.exit(0)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Orb
        self.orb = JarvisOrb()
        orb_layout = QHBoxLayout()
        orb_layout.addStretch()
        orb_layout.addWidget(self.orb)
        orb_layout.addStretch()
        main_layout.addLayout(orb_layout)
        
        # Chat area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: #1f2833;
            border: 1px solid #45a29e;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        """)
        main_layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            background-color: #1f2833;
            border: 1px solid #45a29e;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("إرسال")
        send_btn.setStyleSheet("background-color: #45a29e; color: #0b0c10; font-weight: bold; padding: 8px; border-radius: 5px;")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        voice_btn = QPushButton("🎤 تحدث")
        voice_btn.setStyleSheet("background-color: #c5c6c7; color: #0b0c10; font-weight: bold; padding: 8px; border-radius: 5px;")
        voice_btn.clicked.connect(self.listen_voice)
        input_layout.addWidget(voice_btn)
        
        main_layout.addLayout(input_layout)
        
        msg = "Hello my friend, I am Jarvis, your AI assistant. How can I help you today?"
        self.add_log(f"جارفيس: {msg}")
        self.speak(msg)

    def add_log(self, text):
        self.chat_display.append(text + "\n")
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def speak(self, text):
        def _speak():
            self.tts.say(text)
            self.tts.runAndWait()
        threading.Thread(target=_speak, daemon=True).start()

    def send_message(self, text=None):
        if not text:
            text = self.input_field.text().strip()
        if not text:
            return
            
        self.input_field.clear()
        self.add_log(f"أنت: {text}")
        
        self.orb.is_active = True
        
        self.worker = AgentWorker(self.agent, text)
        self.worker.finished.connect(self.on_agent_reply)
        self.worker.start()

    def on_agent_reply(self, reply):
        self.orb.is_active = False
        self.add_log(f"جارفيس: {reply}")
        self.speak(reply)
        
    def listen_voice(self):
        self.orb.is_active = True
        def _listen():
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio, language="ar-EG")
                    self.send_message(text)
                except Exception as e:
                    self.orb.is_active = False
                    print(f"صوت غير واضح: {e}")
        threading.Thread(target=_listen, daemon=True).start()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
