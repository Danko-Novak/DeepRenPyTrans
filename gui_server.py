"""
DeepRenPyTrans Web Console Server
Serves a premium HTML/CSS/JS interface for managing translations and APK builds.
Runs locally with zero external dependencies.
"""

import os
import sys
import json
import re
import time
import subprocess
import threading
import webbrowser
try:
    import yaml
except ImportError:
    import subprocess
    import sys
    print("============================================================")
    print("⚠️  Dependency 'PyYAML' is missing. Attempting auto-installation...")
    print("============================================================")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
        import yaml
        print("✅ 'PyYAML' installed successfully!")
    except Exception as e:
        print(f"❌ Failed to install PyYAML automatically: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
from http.server import BaseHTTPRequestHandler, HTTPServer


# Server Configuration
PORT = 8000
HOST = "localhost"

# Global subprocess control
active_process = None
process_lock = threading.Lock()

# Paths resolution
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.path.join(ROOT_DIR, ".."))

# Config file paths
CONFIG_YAML = os.path.join(ROOT_DIR, "config.yaml")
ENV_FILE = os.path.join(ROOT_DIR, ".env")
BAT_FILE = os.path.join(PARENT_DIR, "build_apk.bat")

# Fallback paths if not found in parent
if not os.path.exists(BAT_FILE):
    BAT_FILE = os.path.join(ROOT_DIR, "build_apk.bat")


def read_yaml():
    if not os.path.exists(CONFIG_YAML):
        # Return defaults matching config.py
        return {
            "game_dir": "./MyGame/game",
            "target_language": "Russian",
            "translation_dir": "russian",
            "api": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "temperature": 0.2,
                "batch_size": 40,
                "max_retries": 3,
                "delay": 1.0
            },
            "fonts": {
                "default": "DejaVuSans.ttf",
                "replacements": {}
            },
            "extraction": {
                "skip_prefixes": ["ITM", "ACT", "LOC", "QST"],
                "force_include": ["Q.Save", "Q.Load"],
                "min_length": 2
            }
        }
    try:
        with open(CONFIG_YAML, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error reading config.yaml: {e}")
        return {}


def write_yaml(data):
    try:
        with open(CONFIG_YAML, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error writing config.yaml: {e}")
        return False


def read_env():
    config = {
        "DEEPSEEK_API_KEY": "",
        "OPENAI_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "GROQ_API_KEY": "",
        "NEBIUS_API_KEY": "",
        "DEEPINFRA_API_KEY": "",
        "GEMINI_API_KEY": "",
        "DASHSCOPE_API_KEY": ""
    }
    if not os.path.exists(ENV_FILE):
        return config
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
    except Exception as e:
        print(f"Error reading .env: {e}")
    return config


def write_env(data):
    try:
        lines = []
        keys_written = set()
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line_strip = line.strip()
                    if line_strip and not line_strip.startswith("#") and "=" in line_strip:
                        key, val = line_strip.split("=", 1)
                        key = key.strip()
                        if key in data:
                            lines.append(f"{key}={data[key]}\n")
                            keys_written.add(key)
                            continue
                    lines.append(line)
        
        for key, val in data.items():
            if key not in keys_written:
                lines.append(f"{key}={val}\n")
                
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error writing .env: {e}")
        return False


def read_bat():
    config = {
        "SEVENZ": "C:\\Program Files\\7-Zip\\7z.exe",
        "OLD_APK": "",
        "PC_GAME": "",
        "WORK_DIR": "apk_work",
        "OUTPUT_APK": "",
        "RESTORE_OLD_ASSETS": "1",
        "COMPRESS_AUDIO": "1",
        "COMPRESS_IMAGES": "1",
        "INJECT_TRANSLATION": "1",
        "LANG_FOLDER": "russian",
        "COMPRESSION_LEVEL": "9"
    }
    if not os.path.exists(BAT_FILE):
        return config
    try:
        with open(BAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Match set "KEY=VAL"
        matches = re.findall(r'set\s+"([^"=]+)=([^"]*)"', content)
        for key, val in matches:
            if key in config:
                config[key] = val
        
        # Match set KEY=VAL (no quotes)
        matches_no_quotes = re.findall(r'set\s+([^"\s=]+)=([^\n\r]*)', content)
        for key, val in matches_no_quotes:
            key = key.strip()
            val = val.strip()
            # Strip quotes if present
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            if key in config:
                config[key] = val
                
    except Exception as e:
        print(f"Error reading build_apk.bat: {e}")
    return config


def write_bat(data):
    if not os.path.exists(BAT_FILE):
        return False
    try:
        with open(BAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        for key, val in data.items():
            # Try matching quoted format set "KEY=VAL"
            pattern_quoted = rf'set\s+"{key}=[^"]*"'
            replacement_quoted = f'set "{key}={val}"'
            if re.search(pattern_quoted, content):
                content = re.sub(pattern_quoted, replacement_quoted, content)
            else:
                # Try matching unquoted format set KEY=VAL
                pattern_unquoted = rf'set\s+{key}=[^\r\n]*'
                if re.search(pattern_unquoted, content):
                    content = re.sub(pattern_unquoted, replacement_quoted, content)
                else:
                    # Append it if not found (under CONFIGURATION)
                    content = content.replace(":: CONFIGURATION", f":: CONFIGURATION\nset \"{key}={val}\"")
                    
        with open(BAT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing build_apk.bat: {e}")
        return False


class GUIRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress standard logging to console for cleaner output
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        elif self.path in ["/logo.webp", "/logo.png"]:
            logo_path = None
            for p in [
                os.path.join(ROOT_DIR, "docs", "logo.webp"),
                os.path.join(ROOT_DIR, "logo.png"),
                os.path.join(PARENT_DIR, "docs", "logo.webp"),
                os.path.join(PARENT_DIR, "logo.png")
            ]:
                if os.path.exists(p) and p.endswith(self.path[1:]):
                    logo_path = p
                    break
            if logo_path:
                self.send_response(200)
                mime = "image/webp" if logo_path.endswith(".webp") else "image/png"
                self.send_header("Content-Type", mime)
                self.end_headers()
                with open(logo_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Logo Not Found")
        elif self.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            yaml_data = read_yaml()
            env_data = read_env()
            bat_data = read_bat()
            
            response = {
                "yaml": yaml_data,
                "env": env_data,
                "bat": bat_data,
                "bat_path": BAT_FILE,
                "yaml_path": CONFIG_YAML,
                "env_path": ENV_FILE
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        global active_process
        if self.path == "/api/config":
            content_length = int(self.headers["Content-Length"])
            post_data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            
            success = True
            if "yaml" in post_data:
                success = success and write_yaml(post_data["yaml"])
            if "env" in post_data:
                success = success and write_env(post_data["env"])
            if "bat" in post_data:
                success = success and write_bat(post_data["bat"])
                
            self.send_response(200 if success else 500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode("utf-8"))
            
        elif self.path == "/api/run":
            content_length = int(self.headers["Content-Length"])
            post_data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            task = post_data.get("task", "")
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            
            # Determine command and working dir
            cmd = ""
            cwd = ROOT_DIR
            
            yaml_config = read_yaml()
            game_dir = yaml_config.get("game_dir", "./game")
            translation_dir = yaml_config.get("translation_dir", "russian")
            
            if task == "extract":
                cmd = f'python -m deeprenpytrans extract --game "{game_dir}"'
                self.wfile.write(f"🚀 Running: {cmd}\n\n".encode("utf-8"))
            elif task == "translate":
                dict_path = os.path.join(game_dir, "tl", translation_dir, "dictionary.json")
                cmd = f'python -m deeprenpytrans translate --strings strings_by_file.json --dict "{dict_path}"'
                self.wfile.write(f"🚀 Running: {cmd}\n\n".encode("utf-8"))
            elif task == "inject":
                cmd = f'python -m deeprenpytrans inject --game "{game_dir}" --lang "{translation_dir}"'
                self.wfile.write(f"🚀 Running: {cmd}\n\n".encode("utf-8"))
            elif task == "build_apk":
                cmd = f'"{BAT_FILE}"'
                cwd = os.path.dirname(BAT_FILE)
                self.wfile.write(f"🚀 Running APK Builder Script: {BAT_FILE}\n\n".encode("utf-8"))
            else:
                self.wfile.write(f"❌ Unknown task: {task}\n".encode("utf-8"))
                return
            
            # Run the command and stream output
            with process_lock:
                if active_process and active_process.poll() is None:
                    self.wfile.write("❌ A process is already running!\n".encode("utf-8"))
                    return
                
                # Inherit environment
                env = os.environ.copy()
                # Ensure Python unbuffered output
                env["PYTHONUNBUFFERED"] = "1"
                
                active_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=cwd,
                    env=env,
                    shell=True
                )
                
            # Stream stdout line by line
            for line in iter(active_process.stdout.readline, ""):
                self.wfile.write(line.encode("utf-8"))
                self.wfile.flush()
                
            active_process.stdout.close()
            return_code = active_process.wait()
            
            with process_lock:
                active_process = None
                
            self.wfile.write(f"\n✨ Process completed with exit code: {return_code}\n".encode("utf-8"))
            self.wfile.flush()
            
        elif self.path == "/api/kill":
            success = False
            message = "No active process running"
            
            with process_lock:
                if active_process and active_process.poll() is None:
                    try:
                        # Windows process tree termination
                        subprocess.run(
                            f"taskkill /F /T /PID {active_process.pid}",
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        active_process.terminate()
                        active_process = None
                        success = True
                        message = "Process terminated successfully"
                    except Exception as e:
                        message = f"Error terminating process: {e}"
            
            self.send_response(200 if success else 400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "message": message}).encode("utf-8"))


# Embedded Premium HTML, CSS, and JS Content
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepRenPyTrans Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b071e;
            --sidebar-bg: rgba(15, 11, 28, 0.75);
            --card-bg: rgba(22, 17, 38, 0.65);
            --accent-purple: #7c4dff;
            --accent-pink: #ff007f;
            --accent-cyan: #00e5ff;
            --text-main: #f5f5f7;
            --text-muted: #a09cb0;
            --border-glass: rgba(255, 255, 255, 0.08);
            --glow-purple: rgba(124, 77, 255, 0.4);
            --glow-cyan: rgba(0, 229, 255, 0.4);
            --glow-pink: rgba(255, 0, 127, 0.4);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at top right, #201335, #0b071e 60%);
            background-color: var(--bg-color);
            color: var(--text-main);
            height: 100vh;
            overflow: hidden;
            display: flex;
        }

        /* Sidebar Styling */
        aside {
            width: 260px;
            background: var(--sidebar-bg);
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--border-glass);
            display: flex;
            flex-direction: column;
            padding: 24px;
            z-index: 10;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 40px;
        }

        .logo-area h2 {
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
        }

        .menu-items {
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-grow: 1;
        }

        .menu-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 14px 18px;
            border-radius: 10px;
            text-align: left;
            font-family: inherit;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .menu-btn:hover {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.03);
            transform: translateX(4px);
        }

        .menu-btn.active {
            color: #fff;
            background: linear-gradient(135deg, rgba(124, 77, 255, 0.2), rgba(255, 0, 127, 0.05));
            border: 1px solid rgba(124, 77, 255, 0.3);
            box-shadow: 0 4px 15px rgba(124, 77, 255, 0.15);
        }

        .status-panel {
            padding: 16px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            border: 1px solid var(--border-glass);
            font-size: 13px;
        }

        .status-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }

        .status-row:last-child {
            margin-bottom: 0;
        }

        .indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ff5252;
            box-shadow: 0 0 8px #ff5252;
        }

        .indicator.online {
            background: #00e676;
            box-shadow: 0 0 8px #00e676;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }

        /* Main Workspace */
        main {
            flex-grow: 1;
            padding: 40px;
            display: flex;
            flex-direction: column;
            gap: 30px;
            height: 100vh;
            overflow-y: auto;
            position: relative;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.4s ease;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 6px;
        }

        header p {
            color: var(--text-muted);
            font-size: 15px;
        }

        /* Cards and Grid */
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border-radius: 16px;
            border: 1px solid var(--border-glass);
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        }

        .card h3 {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 12px;
        }

        /* Form Controls */
        .form-group {
            margin-bottom: 20px;
        }

        .form-group:last-child {
            margin-bottom: 0;
        }

        label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .input-wrapper {
            position: relative;
            display: flex;
        }

        input[type="text"], input[type="password"], select, input[type="number"] {
            width: 100%;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border-glass);
            border-radius: 8px;
            padding: 12px 16px;
            color: #fff;
            font-family: inherit;
            font-size: 14px;
            transition: all 0.3s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--accent-purple);
            box-shadow: 0 0 10px rgba(124, 77, 255, 0.2);
            background: rgba(0, 0, 0, 0.35);
        }

        /* Toggles (Switches) */
        .toggle-group {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.02);
            padding: 14px 18px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.03);
            margin-bottom: 12px;
        }

        .toggle-info h4 {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 2px;
        }

        .toggle-info p {
            font-size: 12px;
            color: var(--text-muted);
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 48px;
            height: 24px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.1);
            transition: .4s;
            border-radius: 24px;
            border: 1px solid var(--border-glass);
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 3px;
            bottom: 3px;
            background-color: #fff;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: var(--accent-purple);
        }

        input:checked + .slider:before {
            transform: translateX(24px);
        }

        /* Buttons */
        .btn {
            background: linear-gradient(135deg, var(--accent-purple), #5e35b1);
            border: none;
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(124, 77, 255, 0.3);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(124, 77, 255, 0.4);
            filter: brightness(1.1);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-cyan {
            background: linear-gradient(135deg, var(--accent-cyan), #00b8d4);
            box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
            color: #0c081d;
        }

        .btn-cyan:hover {
            box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4);
        }

        .btn-pink {
            background: linear-gradient(135deg, var(--accent-pink), #c2185b);
            box-shadow: 0 4px 15px rgba(255, 0, 127, 0.3);
        }

        .btn-pink:hover {
            box-shadow: 0 6px 20px rgba(255, 0, 127, 0.4);
        }

        .btn-outline {
            background: transparent;
            border: 1px solid var(--border-glass);
            box-shadow: none;
            color: var(--text-main);
        }

        .btn-outline:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: #fff;
            box-shadow: none;
        }

        /* Dashboard specific styling */
        .dash-actions {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }

        .action-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            transition: all 0.3s;
        }

        .action-card:hover {
            background: rgba(255, 255, 255, 0.04);
            border-color: var(--accent-purple);
            transform: translateY(-4px);
        }

        .action-icon {
            font-size: 32px;
            margin-bottom: 6px;
        }

        .action-card h4 {
            font-size: 15px;
            font-weight: 600;
        }

        .action-card p {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.4;
        }

        /* Terminal Console */
        .terminal-container {
            background: #05030a;
            border: 1px solid #1a1530;
            border-radius: 12px;
            box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8), 0 8px 32px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            height: calc(100vh - 240px);
        }

        .terminal-header {
            background: #110d22;
            padding: 12px 20px;
            border-bottom: 1px solid #1a1530;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: 12px 12px 0 0;
        }

        .terminal-controls {
            display: flex;
            gap: 10px;
        }

        .terminal-body {
            flex-grow: 1;
            padding: 20px;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            line-height: 1.6;
            overflow-y: auto;
            color: #d8d3ec;
        }

        .terminal-line {
            white-space: pre-wrap;
            margin-bottom: 4px;
        }

        .terminal-line.error {
            color: #ff5252;
            text-shadow: 0 0 6px rgba(255, 82, 82, 0.2);
        }

        .terminal-line.success {
            color: #00e676;
            text-shadow: 0 0 6px rgba(0, 230, 118, 0.2);
        }

        .terminal-line.warn {
            color: #ffd700;
            text-shadow: 0 0 6px rgba(255, 215, 0, 0.2);
        }

        .terminal-line.info {
            color: var(--accent-cyan);
        }

        /* Toast notification */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(15, 11, 28, 0.9);
            border: 1px solid var(--accent-purple);
            border-radius: 8px;
            padding: 16px 24px;
            color: #fff;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 15px rgba(124, 77, 255, 0.2);
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 999;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        .toast-icon {
            font-size: 18px;
        }

        .toast.success { border-color: #00e676; }
        .toast.error { border-color: #ff5252; }
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <aside>
        <div class="logo-area">
            <img src="/logo.webp" alt="DeepRenPyTrans Logo" style="height: 38px; border-radius: 6px;" onerror="this.src='/logo.png'; this.onerror=null;">
            <h2 style="font-size: 18px;">DeepRenPyTrans</h2>
        </div>

        <div class="menu-items">
            <button class="menu-btn active" onclick="switchTab('dashboard')">
                <span>📊</span> Dashboard
            </button>
            <button class="menu-btn" onclick="switchTab('translate-settings')">
                <span>🤖</span> AI Translation
            </button>
            <button class="menu-btn" onclick="switchTab('apk-settings')">
                <span>📱</span> APK Builder
            </button>
            <button class="menu-btn" onclick="switchTab('console')">
                <span>🖥️</span> Live Console
            </button>
        </div>

        <div class="status-panel">
            <div class="status-row">
                <span id="backend-status" class="indicator online"></span>
                <span>Console Server: Active</span>
            </div>
            <div class="status-row">
                <span id="process-status" class="indicator"></span>
                <span id="process-status-text">Subprocess: Idle</span>
            </div>
        </div>
    </aside>

    <!-- Main Workspace -->
    <main>
        
        <!-- DASHBOARD TAB -->
        <div id="dashboard" class="tab-content active">
            <header style="margin-bottom: 40px;">
                <h1>Control Dashboard</h1>
                <p>Welcome to the universal visual novel translation control panel.</p>
            </header>

            <div class="card">
                <h3><span>📁</span> Active Directory Status</h3>
                <div class="grid-2" style="margin-bottom: 20px;">
                    <div>
                        <label>Game Directory</label>
                        <p id="dash-game-dir" style="font-family: monospace; font-size: 14px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; border: 1px solid var(--border-glass);">Loading...</p>
                    </div>
                    <div>
                        <label>Build Target APK Path</label>
                        <p id="dash-output-apk" style="font-family: monospace; font-size: 14px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; border: 1px solid var(--border-glass);">Loading...</p>
                    </div>
                </div>
            </div>

            <h3 style="margin-bottom: 16px;">Quick Commands</h3>
            <div class="dash-actions">
                <div class="action-card">
                    <span class="action-icon">🔍</span>
                    <h4>Extract Strings</h4>
                    <p>Scans all game .rpy files and extracts new translation lines.</p>
                    <button class="btn btn-outline" style="width: 100%; margin-top: auto;" onclick="runTask('extract')">Run Extract</button>
                </div>
                <div class="action-card">
                    <span class="action-icon">🤖</span>
                    <h4>Translate Game</h4>
                    <p>Sends extracted game strings to selected LLM in smart batches.</p>
                    <button class="btn btn-outline" style="width: 100%; margin-top: auto;" onclick="runTask('translate')">Run Translate</button>
                </div>
                <div class="action-card">
                    <span class="action-icon">🔌</span>
                    <h4>Inject Hooks</h4>
                    <p>Creates configuration files and runtime hooks inside the game.</p>
                    <button class="btn btn-outline" style="width: 100%; margin-top: auto;" onclick="runTask('inject')">Run Inject</button>
                </div>
                <div class="action-card">
                    <span class="action-icon">📱</span>
                    <h4>Build APK</h4>
                    <p>Invokes batch script to compile, optimize, and sign mobile build.</p>
                    <button class="btn btn-cyan" style="width: 100%; margin-top: auto;" onclick="runTask('build_apk')">Build Android APK</button>
                </div>
            </div>
        </div>

        <!-- TRANSLATION SETTINGS TAB -->
        <div id="translate-settings" class="tab-content">
            <header style="margin-bottom: 30px;">
                <h1>AI Translation Pipeline</h1>
                <p>Configure LLM endpoints, credentials, and translation logic settings.</p>
            </header>

            <div class="card">
                <h3><span>⚙️</span> Core Settings</h3>
                <div class="grid-2">
                    <div class="form-group">
                        <label for="yaml-game-dir">Game Folder Path</label>
                        <input type="text" id="yaml-game-dir">
                    </div>
                    <div class="form-group">
                        <label for="yaml-lang">Target Language</label>
                        <input type="text" id="yaml-lang" placeholder="e.g. Russian">
                    </div>
                    <div class="form-group">
                        <label for="yaml-tl-dir">Translation Subfolder</label>
                        <input type="text" id="yaml-tl-dir" placeholder="e.g. russian">
                    </div>
                    <div class="form-group">
                        <label for="yaml-provider">AI Provider</label>
                        <select id="yaml-provider" onchange="updateModelChoices()">
                            <option value="deepseek">DeepSeek</option>
                            <option value="openai">OpenAI</option>
                            <option value="openrouter">OpenRouter (Aggregator)</option>
                            <option value="groq">Groq (Ultra Fast)</option>
                            <option value="nebius">Nebius AI Studio</option>
                            <option value="deepinfra">DeepInfra</option>
                            <option value="gemini">Google Gemini (Direct)</option>
                            <option value="dashscope">Alibaba DashScope (Qwen Direct)</option>
                            <option value="ollama">Ollama (Local)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="yaml-model">Model Name</label>
                        <select id="yaml-model"></select>
                    </div>
                    <div class="form-group">
                        <label for="env-apikey">API Credentials Key</label>
                        <input type="password" id="env-apikey" placeholder="sk-...">
                    </div>
                </div>
            </div>

            <div class="card">
                <h3><span>⚡</span> Model Performance Parameters</h3>
                <div class="grid-2">
                    <div class="form-group">
                        <label for="yaml-temp">Temperature (Randomness: Lower = Consistent)</label>
                        <input type="number" id="yaml-temp" min="0" max="1" step="0.1">
                    </div>
                    <div class="form-group">
                        <label for="yaml-batch">Batch Size (Strings per Request)</label>
                        <input type="number" id="yaml-batch" min="5" max="150" step="5">
                    </div>
                    <div class="form-group">
                        <label for="yaml-delay">Delay Between Requests (seconds)</label>
                        <input type="number" id="yaml-delay" min="0" max="10" step="0.5">
                    </div>
                    <div class="form-group">
                        <label for="yaml-retries">Max Retries on Failures</label>
                        <input type="number" id="yaml-retries" min="0" max="10">
                    </div>
                </div>
            </div>

            <div style="text-align: right;">
                <button class="btn btn-outline" onclick="loadConfigurations()" style="margin-right: 12px;">Discard Changes</button>
                <button class="btn" onclick="saveTranslationSettings()">Save Translation Config</button>
            </div>
        </div>

        <!-- APK BUILDER SETTINGS TAB -->
        <div id="apk-settings" class="tab-content">
            <header style="margin-bottom: 30px;">
                <h1>Android APK Compiler & Compressor</h1>
                <p>Customize asset compression, translation injection, and package repacking settings.</p>
            </header>

            <div class="grid-2">
                <div>
                    <div class="card">
                        <h3><span>🎛️</span> Compilation Toggle Flags</h3>
                        
                        <div class="toggle-group">
                            <div class="toggle-info">
                                <h4>Restore Compressed Assets</h4>
                                <p>Replaces fresh PC files with compressed copies from old APK.</p>
                            </div>
                            <label class="switch">
                                <input type="checkbox" id="bat-flag-restore">
                                <span class="slider"></span>
                            </label>
                        </div>

                        <div class="toggle-group">
                            <div class="toggle-info">
                                <h4>Compress Audio Assets</h4>
                                <p>Converts large .wav files to mobile-friendly .ogg format.</p>
                            </div>
                            <label class="switch">
                                <input type="checkbox" id="bat-flag-audio">
                                <span class="slider"></span>
                            </label>
                        </div>

                        <div class="toggle-group">
                            <div class="toggle-info">
                                <h4>Optimize Images</h4>
                                <p>Resizes and recompresses new graphics for mobile performance.</p>
                            </div>
                            <label class="switch">
                                <input type="checkbox" id="bat-flag-images">
                                <span class="slider"></span>
                            </label>
                        </div>

                        <div class="toggle-group">
                            <div class="toggle-info">
                                <h4>Inject Translation Hooks</h4>
                                <p>Injects hooks.rpy and translator dictionaries into the game folder.</p>
                            </div>
                            <label class="switch">
                                <input type="checkbox" id="bat-flag-inject">
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>
                </div>

                <div>
                    <div class="card">
                        <h3><span>📁</span> Paths & Build Configurations</h3>
                        <div class="form-group">
                            <label for="bat-old-apk">Old Reference APK Path</label>
                            <input type="text" id="bat-old-apk">
                        </div>
                        <div class="form-group">
                            <label for="bat-output-apk">Output Compiled APK Path</label>
                            <input type="text" id="bat-output-apk">
                        </div>
                        <div class="grid-2">
                            <div class="form-group">
                                <label for="bat-lang-folder">Translation Folder Name</label>
                                <input type="text" id="bat-lang-folder" placeholder="russian">
                            </div>
                            <div class="form-group">
                                <label for="bat-compression-level">Repack Compression (0-9)</label>
                                <input type="number" id="bat-compression-level" min="0" max="9">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="bat-sevenz">7-Zip Executable Path</label>
                            <input type="text" id="bat-sevenz">
                        </div>
                    </div>
                </div>
            </div>

            <div style="text-align: right;">
                <button class="btn btn-outline" onclick="loadConfigurations()" style="margin-right: 12px;">Discard Changes</button>
                <button class="btn btn-cyan" onclick="saveApkSettings()">Save APK Config</button>
            </div>
        </div>

        <!-- LIVE TERMINAL CONSOLE TAB -->
        <div id="console" class="tab-content">
            <header style="margin-bottom: 20px;">
                <h1>Process Console</h1>
                <p>Real-time terminal execution log. Actions will stream logs dynamically.</p>
            </header>

            <div class="terminal-container">
                <div class="terminal-header">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 14px;">📟</span>
                        <span id="active-task-label" style="font-weight: 500; font-size: 14px;">Task: Idle</span>
                    </div>
                    <div class="terminal-controls">
                        <button class="btn btn-outline" style="padding: 6px 12px; font-size: 12px;" onclick="clearConsole()">Clear Logs</button>
                        <button id="kill-btn" class="btn btn-pink" style="padding: 6px 12px; font-size: 12px; display: none;" onclick="killActiveProcess()">Abort Task</button>
                    </div>
                </div>
                <div id="terminal-body" class="terminal-body">
                    <div class="terminal-line info">[Console initialized. Ready for operations.]</div>
                </div>
            </div>
        </div>

    </main>

    <!-- Toast Notification -->
    <div id="toast" class="toast">
        <span id="toast-icon" class="toast-icon">✨</span>
        <span id="toast-msg">Configuration saved successfully!</span>
    </div>

    <!-- JS Functionality -->
    <script>
        let currentConfig = {};
        let isTaskRunning = false;

        const modelOptions = {
            deepseek: [
                { value: 'deepseek-chat', label: 'DeepSeek Chat (Non-Thinking)' },
                { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
                { value: 'deepseek-v4-pro', label: 'DeepSeek V4 Pro' },
                { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner (Thinking)' }
            ],
            openai: [
                { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Recommended)' },
                { value: 'gpt-4o', label: 'GPT-4o' },
                { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
            ],
            openrouter: [
                { value: 'qwen/qwen-2.5-72b-instruct', label: 'Qwen 2.5 72B (Best for Ru/Zh)' },
                { value: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B (High Quality)' },
                { value: 'meta-llama/llama-3.1-8b-instruct', label: 'Llama 3.1 8B (Ultra Cheap)' },
                { value: 'deepseek/deepseek-chat', label: 'DeepSeek V3 (via OpenRouter)' },
                { value: 'google/gemini-3.5-flash', label: 'Gemini 3.5 Flash' },
                { value: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash' }
            ],
            groq: [
                { value: 'llama-3.3-70b-specdec', label: 'Llama 3.3 70B (Fast SpecDec)' },
                { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B (Instant & Cheap)' },
                { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' }
            ],
            nebius: [
                { value: 'Qwen/Qwen2.5-72B-Instruct', label: 'Qwen 2.5 72B (Studio)' },
                { value: 'meta-llama/Meta-Llama-3.1-70B-Instruct', label: 'Llama 3.1 70B (Studio)' },
                { value: 'meta-llama/Meta-Llama-3.1-8B-Instruct', label: 'Llama 3.1 8B (Studio)' }
            ],
            deepinfra: [
                { value: 'Qwen/Qwen2.5-72B-Instruct', label: 'Qwen 2.5 72B' },
                { value: 'meta-llama/Meta-Llama-3.3-70B-Instruct', label: 'Llama 3.3 70B' },
                { value: 'meta-llama/Meta-Llama-3.1-8B-Instruct', label: 'Llama 3.1 8B' }
            ],
            gemini: [
                { value: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash (Recommended)' },
                { value: 'gemini-3.1-pro', label: 'Gemini 3.1 Pro (Reasoning)' },
                { value: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash-Lite' },
                { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
                { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' }
            ],
            dashscope: [
                { value: 'qwen-plus', label: 'Qwen Plus (Balanced)' },
                { value: 'qwen-max', label: 'Qwen Max (High Reasoning)' },
                { value: 'qwen-turbo', label: 'Qwen Turbo (Fast)' }
            ],
            ollama: [
                { value: 'llama3', label: 'Llama 3' },
                { value: 'mistral', label: 'Mistral' },
                { value: 'phi3', label: 'Phi-3' }
            ]
        };

        // Initialize App
        window.addEventListener('DOMContentLoaded', () => {
            loadConfigurations();
        });

        // Tab Switching Logic
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.menu-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            
            // Highlight button
            const btnIdx = {
                'dashboard': 0,
                'translate-settings': 1,
                'apk-settings': 2,
                'console': 3
            };
            document.querySelectorAll('.menu-btn')[btnIdx[tabId]].classList.add('active');
        }

        // Dropdown Auto Updater
        function updateModelChoices(selectedModel = null) {
            const provider = document.getElementById('yaml-provider').value;
            const modelSelect = document.getElementById('yaml-model');
            modelSelect.innerHTML = '';
            
            const options = modelOptions[provider] || [];
            options.forEach(opt => {
                const el = document.createElement('option');
                el.value = opt.value;
                el.textContent = opt.label;
                modelSelect.appendChild(el);
            });

            // Set selected value if available
            if (selectedModel) {
                modelSelect.value = selectedModel;
            }

            // Update API Key field dynamically from env config
            if (currentConfig.env) {
                const apiKeyMap = {
                    deepseek: currentConfig.env.DEEPSEEK_API_KEY || '',
                    openai: currentConfig.env.OPENAI_API_KEY || '',
                    openrouter: currentConfig.env.OPENROUTER_API_KEY || '',
                    groq: currentConfig.env.GROQ_API_KEY || '',
                    nebius: currentConfig.env.NEBIUS_API_KEY || '',
                    deepinfra: currentConfig.env.DEEPINFRA_API_KEY || '',
                    gemini: currentConfig.env.GEMINI_API_KEY || '',
                    dashscope: currentConfig.env.DASHSCOPE_API_KEY || '',
                    ollama: ''
                };
                const keyInput = document.getElementById('env-apikey');
                keyInput.value = apiKeyMap[provider] || '';
                
                // Toggle input state
                if (provider === 'ollama') {
                    keyInput.placeholder = 'Not required for Ollama';
                    keyInput.disabled = true;
                } else {
                    keyInput.placeholder = 'Paste your API key here...';
                    keyInput.disabled = false;
                }
            }
        }

        // Fetch configurations from Python API
        async function loadConfigurations() {
            try {
                const response = await fetch('/api/config');
                if (!response.ok) throw new Error('API config load failed');
                
                const data = await response.json();
                currentConfig = data;
                
                // Dashboard Update
                document.getElementById('dash-game-dir').textContent = data.yaml.game_dir || 'Not Set';
                document.getElementById('dash-output-apk').textContent = data.bat.OUTPUT_APK || 'Not Set';
                
                // AI config tab values
                document.getElementById('yaml-game-dir').value = data.yaml.game_dir || '';
                document.getElementById('yaml-lang').value = data.yaml.target_language || '';
                document.getElementById('yaml-tl-dir').value = data.yaml.translation_dir || '';
                document.getElementById('yaml-provider').value = data.yaml.api?.provider || 'deepseek';
                
                updateModelChoices(data.yaml.api?.model);
                
                document.getElementById('yaml-temp').value = data.yaml.api?.temperature ?? 0.2;
                document.getElementById('yaml-batch').value = data.yaml.api?.batch_size ?? 40;
                document.getElementById('yaml-delay').value = data.yaml.api?.delay ?? 1.0;
                document.getElementById('yaml-retries').value = data.yaml.api?.max_retries ?? 3;
                
                // Env variables
                const provider = data.yaml.api?.provider || 'deepseek';
                const apiKeyMap = {
                    deepseek: data.env.DEEPSEEK_API_KEY || '',
                    openai: data.env.OPENAI_API_KEY || '',
                    openrouter: data.env.OPENROUTER_API_KEY || '',
                    groq: data.env.GROQ_API_KEY || '',
                    nebius: data.env.NEBIUS_API_KEY || '',
                    deepinfra: data.env.DEEPINFRA_API_KEY || '',
                    gemini: data.env.GEMINI_API_KEY || '',
                    dashscope: data.env.DASHSCOPE_API_KEY || '',
                    ollama: ''
                };
                const keyInput = document.getElementById('env-apikey');
                keyInput.value = apiKeyMap[provider] || '';
                if (provider === 'ollama') {
                    keyInput.placeholder = 'Not required for Ollama';
                    keyInput.disabled = true;
                } else {
                    keyInput.placeholder = 'Paste your API key here...';
                    keyInput.disabled = false;
                }
                
                // Bat config values
                document.getElementById('bat-flag-restore').checked = data.bat.RESTORE_OLD_ASSETS === '1';
                document.getElementById('bat-flag-audio').checked = data.bat.COMPRESS_AUDIO === '1';
                document.getElementById('bat-flag-images').checked = data.bat.COMPRESS_IMAGES === '1';
                document.getElementById('bat-flag-inject').checked = data.bat.INJECT_TRANSLATION === '1';
                
                document.getElementById('bat-old-apk').value = data.bat.OLD_APK || '';
                document.getElementById('bat-output-apk').value = data.bat.OUTPUT_APK || '';
                document.getElementById('bat-lang-folder').value = data.bat.LANG_FOLDER || 'russian';
                document.getElementById('bat-compression-level').value = data.bat.COMPRESSION_LEVEL ?? 9;
                document.getElementById('bat-sevenz').value = data.bat.SEVENZ || '';
                
                showToast('✨ Configurations loaded successfully!');
            } catch (err) {
                console.error(err);
                showToast('❌ Failed to load configurations!', 'error');
            }
        }

        // Save AI translation configurations
        async function saveTranslationSettings() {
            try {
                const provider = document.getElementById('yaml-provider').value;
                const apiKey = document.getElementById('env-apikey').value;
                
                // Merge translations configuration
                const updatedYaml = {
                    ...currentConfig.yaml,
                    game_dir: document.getElementById('yaml-game-dir').value,
                    target_language: document.getElementById('yaml-lang').value,
                    translation_dir: document.getElementById('yaml-tl-dir').value,
                    api: {
                        ...currentConfig.yaml.api,
                        provider: provider,
                        model: document.getElementById('yaml-model').value,
                        temperature: parseFloat(document.getElementById('yaml-temp').value),
                        batch_size: parseInt(document.getElementById('yaml-batch').value),
                        delay: parseFloat(document.getElementById('yaml-delay').value),
                        max_retries: parseInt(document.getElementById('yaml-retries').value),
                    }
                };

                const updatedEnv = { ...currentConfig.env };
                if (provider === 'deepseek') {
                    updatedEnv.DEEPSEEK_API_KEY = apiKey;
                } else if (provider === 'openai') {
                    updatedEnv.OPENAI_API_KEY = apiKey;
                } else if (provider === 'openrouter') {
                    updatedEnv.OPENROUTER_API_KEY = apiKey;
                } else if (provider === 'groq') {
                    updatedEnv.GROQ_API_KEY = apiKey;
                } else if (provider === 'nebius') {
                    updatedEnv.NEBIUS_API_KEY = apiKey;
                } else if (provider === 'deepinfra') {
                    updatedEnv.DEEPINFRA_API_KEY = apiKey;
                } else if (provider === 'gemini') {
                    updatedEnv.GEMINI_API_KEY = apiKey;
                } else if (provider === 'dashscope') {
                    updatedEnv.DASHSCOPE_API_KEY = apiKey;
                }

                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ yaml: updatedYaml, env: updatedEnv })
                });

                if (!response.ok) throw new Error('Save failed');
                
                showToast('💾 Translation configurations saved!');
                loadConfigurations(); // Refresh
            } catch (err) {
                console.error(err);
                showToast('❌ Failed to save configurations!', 'error');
            }
        }

        // Save APK configuration flags and variables
        async function saveApkSettings() {
            try {
                const updatedBat = {
                    ...currentConfig.bat,
                    RESTORE_OLD_ASSETS: document.getElementById('bat-flag-restore').checked ? '1' : '0',
                    COMPRESS_AUDIO: document.getElementById('bat-flag-audio').checked ? '1' : '0',
                    COMPRESS_IMAGES: document.getElementById('bat-flag-images').checked ? '1' : '0',
                    INJECT_TRANSLATION: document.getElementById('bat-flag-inject').checked ? '1' : '0',
                    OLD_APK: document.getElementById('bat-old-apk').value,
                    OUTPUT_APK: document.getElementById('bat-output-apk').value,
                    LANG_FOLDER: document.getElementById('bat-lang-folder').value,
                    COMPRESSION_LEVEL: document.getElementById('bat-compression-level').value,
                    SEVENZ: document.getElementById('bat-sevenz').value
                };

                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ bat: updatedBat })
                });

                if (!response.ok) throw new Error('Save failed');
                
                showToast('💾 APK Builder configurations saved!');
                loadConfigurations(); // Refresh
            } catch (err) {
                console.error(err);
                showToast('❌ Failed to save APK settings!', 'error');
            }
        }

        // Run Tasks & Handle Live Logging Streams
        async function runTask(taskName) {
            if (isTaskRunning) {
                showToast('⚠️ A task is already executing. Please abort or wait.', 'error');
                return;
            }
            
            isTaskRunning = true;
            updateSubprocessStatus(true, taskName);
            switchTab('console');
            
            const term = document.getElementById('terminal-body');
            term.innerHTML = `<div class="terminal-line info">[Starting Task: ${taskName}...]</div>`;
            
            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task: taskName })
                });

                if (!response.body) {
                    throw new Error('Readable stream not supported by server response');
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    appendLinesToTerminal(text);
                }
            } catch (err) {
                appendLine('error', `❌ Error executing task: ${err.message}`);
            } finally {
                isTaskRunning = false;
                updateSubprocessStatus(false);
            }
        }

        // Cancel / Kill Active Tasks
        async function killActiveProcess() {
            try {
                const response = await fetch('/api/kill', { method: 'POST' });
                const resData = await response.json();
                if (response.ok) {
                    showToast('🛑 Task terminated!');
                    appendLine('error', `[Process aborted by user request]`);
                } else {
                    showToast(resData.message, 'error');
                }
            } catch (err) {
                showToast('❌ Abort command failed', 'error');
            }
        }

        // Helper: Output log lines
        function appendLinesToTerminal(text) {
            const lines = text.split('\\n');
            lines.forEach((line, index) => {
                if (index === lines.length - 1 && line === '') return;
                
                let type = 'standard';
                const lower = line.toLowerCase();
                
                if (lower.includes('error') || lower.includes('failed') || lower.includes('err:')) {
                    type = 'error';
                } else if (lower.includes('ok') || lower.includes('success') || lower.includes('complete')) {
                    type = 'success';
                } else if (lower.includes('warn') || lower.includes('wait') || lower.includes('limited')) {
                    type = 'warn';
                } else if (lower.startsWith('🚀') || lower.startsWith('step') || lower.startsWith('[')) {
                    type = 'info';
                }
                
                appendLine(type, line);
            });
        }

        function appendLine(type, text) {
            const term = document.getElementById('terminal-body');
            const line = document.createElement('div');
            line.className = `terminal-line ${type === 'standard' ? '' : type}`;
            line.textContent = text;
            term.appendChild(line);
            
            // Auto scroll to bottom
            term.scrollTop = term.scrollHeight;
        }

        function clearConsole() {
            document.getElementById('terminal-body').innerHTML = '<div class="terminal-line info">[Console logs cleared]</div>';
        }

        function updateSubprocessStatus(running, taskName = '') {
            const statusInd = document.getElementById('process-status');
            const statusText = document.getElementById('process-status-text');
            const killBtn = document.getElementById('kill-btn');
            const taskLabel = document.getElementById('active-task-label');
            
            if (running) {
                statusInd.className = 'indicator online';
                statusText.textContent = `Subprocess: Running (${taskName})`;
                killBtn.style.display = 'block';
                taskLabel.textContent = `Task: Running (${taskName})`;
            } else {
                statusInd.className = 'indicator';
                statusText.textContent = 'Subprocess: Idle';
                killBtn.style.display = 'none';
                taskLabel.textContent = 'Task: Idle';
            }
        }

        // Toast notifications
        function showToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            const toastIcon = document.getElementById('toast-icon');
            const toastMsg = document.getElementById('toast-msg');
            
            toast.className = `toast ${type}`;
            toastIcon.textContent = type === 'success' ? '✨' : '❌';
            toastMsg.textContent = msg;
            
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
    </script>
</body>
</html>
"""


def run(server_class=HTTPServer, handler_class=GUIRequestHandler):
    server_address = (HOST, PORT)
    httpd = server_class(server_address, handler_class)
    print(f"============================================================")
    print(f"  🎮 DeepRenPyTrans Web Console started at: http://{HOST}:{PORT}")
    print(f"  Configuration Loaded:")
    print(f"    - Translation Config: {CONFIG_YAML}")
    print(f"    - Environment File:   {ENV_FILE}")
    print(f"    - Batch Script File:  {BAT_FILE}")
    print(f"============================================================")
    print("  Press Ctrl+C in this terminal window to stop the server.")
    print("============================================================")
    
    # Auto-open browser
    def open_browser():
        time.sleep(1)
        webbrowser.open(f"http://{HOST}:{PORT}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Local Web Server...")
        httpd.server_close()
        print("Server stopped. Goodbye!")


if __name__ == "__main__":
    run()
