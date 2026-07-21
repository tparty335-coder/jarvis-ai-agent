"""
launch_jarvis.pyw
-----------------
Silent launcher for Jarvis AI Agent.
Uses .pyw extension so Windows runs it with pythonw.exe (no console window).
Automatically installs missing dependencies before launching.
"""
import sys
import os
import subprocess

# Set working directory to this script's folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

VENV_PYTHON = os.path.join(SCRIPT_DIR, "venv", "Scripts", "pythonw.exe")
VENV_PIP    = os.path.join(SCRIPT_DIR, "venv", "Scripts", "pip.exe")
VENV_DIR    = os.path.join(SCRIPT_DIR, "venv")

def ensure_venv():
    """Create venv if it doesn't exist."""
    if not os.path.exists(VENV_PYTHON):
        python = sys.executable.replace("pythonw.exe", "python.exe")
        subprocess.run([python, "-m", "venv", VENV_DIR], check=True)

def install_deps():
    """Install core requirements once (skips if already installed)."""
    marker = os.path.join(VENV_DIR, ".deps_installed")
    if os.path.exists(marker):
        return
    req_file = os.path.join(SCRIPT_DIR, "requirements-core.txt")
    if os.path.exists(req_file):
        subprocess.run(
            [VENV_PIP, "install", "-q", "-r", req_file],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    # Mark as done
    with open(marker, "w") as f:
        f.write("ok")

def load_env():
    """Load .env file into environment variables."""
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

def main():
    ensure_venv()
    install_deps()
    load_env()

    # Launch the GUI using the venv's pythonw (silent, no console)
    gui_path = os.path.join(SCRIPT_DIR, "gui.py")
    subprocess.Popen(
        [VENV_PYTHON, gui_path],
        cwd=SCRIPT_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

if __name__ == "__main__":
    main()
