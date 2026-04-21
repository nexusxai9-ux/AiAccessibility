import speech_recognition as sr
import pyttsx3
import webbrowser
import pyautogui
pyautogui.FAILSAFE = False
import time
import cv2
import pygetwindow as gw
import re
import os
import datetime
import screen_brightness_control as sbc
import requests
import win32com.client
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pycaw.constants import EDataFlow, ERole

# ================== CONFIG ==================
WAKE_WORD = "nexus"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

class NexusKernel:
    def __init__(self):
        # Voice Engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        voices = self.engine.getProperty('voices')
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)
        
        # State
        self.is_running = True
        self.current_window_index = 0
        
        # Recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 400
        self.recognizer.pause_threshold = 0.8
        
        # Hardware Setup
        try:
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(EDGE_PATH))
        except:
            print("[KERNEL] Could not register Edge.")

        # Shared Microphone to prevent repeated [Errno -9988] Stream closed
        self.mic = sr.Microphone()

    def speak(self, text):
        print(f"[NEXUS] {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[ERROR] TTS Failed: {e}")

    def listen(self, timeout=5, phrase_limit=5):
        """Robust listening with retry logic for stream errors."""
        try:
            with self.mic as source:
                print(f"\n[LISTENING]...")
                # Removed repeated ambient noise adjustment to reduce lag
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                    print("[RECOGNIZING...]")
                    query = self.recognizer.recognize_google(audio).lower()
                    print(f"[YOU]: {query}")
                    return query
                except (sr.UnknownValueError, sr.WaitTimeoutError):
                    return ""
                except sr.RequestError as e:
                    print(f"[KERNEL] API Error: {e}")
                    return ""
        except OSError as e:
            if "-9988" in str(e):
                print("[KERNEL] Stream closed error detected. Resetting microphone...")
                time.sleep(1) # Cool down
            else:
                print(f"[KERNEL] Microphone busy or error: {e}")
            return ""
        except Exception as e:
            print(f"[KERNEL] Unexpected audio error: {e}")
            return ""

    # --- ADVANCED WINDOW MANAGEMENT (from OPEN.py) ---
    
    def switch_to_next_window(self):
        windows = [w for w in gw.getAllWindows() if w.title.strip() != "" and w.visible and len(w.title) > 2]
        if not windows:
            self.speak("No valid windows found.")
            return
        self.current_window_index = (self.current_window_index + 1) % len(windows)
        try:
            target = windows[self.current_window_index]
            if target.isMinimized: target.restore()
            target.activate()
            self.speak(f"Switched to {target.title[:20]}")
        except:
            pass

    def close_specific_window(self, target):
        target = target.lower().strip()
        if "currency" in target:
            self.speak("Protection protocol: Cannot close currency page.")
            return
        
        all_windows = gw.getAllWindows()
        matching = [w for w in all_windows if target in w.title.lower()]
        
        if not matching:
            self.speak(f"No window found matching {target}. Closing active window.")
            pyautogui.hotkey('alt', 'f4')
            return

        for win in matching:
            try:
                if win.isMinimized: win.restore()
                win.activate()
                time.sleep(0.3)
                pyautogui.hotkey('alt', 'f4')
            except:
                pass
        self.speak(f"Closed {len(matching)} windows.")

    # --- MODULES ---
    
    def process_ai_dialog(self, query):
        clean_query = query.replace(WAKE_WORD, "").strip()
        if not clean_query:
            self.speak("I'm here. What do you need?")
            clean_query = self.listen(timeout=8)
            if not clean_query: return

        print(f"[AI] Query: {clean_query}")
        url = "http://localhost:11434/api/generate"
        payload = {"model": "llama3.2", "prompt": clean_query, "stream": False}
        try:
            # Check if Ollama is running first
            requests.get("http://localhost:11434/", timeout=2)
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 200:
                reply = response.json().get("response", "No response.")
                self.speak(reply)
            else:
                self.speak("My AI core responded with an error.")
        except requests.exceptions.ConnectionError:
            self.speak("My AI core is unreachable. Please ensure Ollama is running.")
        except Exception as e:
            self.speak("Internal connection error with AI modules.")

    def run_dictation(self):
        self.speak("Dictation mode active. Say 'stop dictation' to exit.")
        while True:
            query = self.listen(timeout=10, phrase_limit=10)
            if "stop dictation" in query or "exit dictation" in query:
                self.speak("Returning to command mode.")
                break
            if query:
                pyautogui.write(f"{query} ", interval=0.01)

    def run_mail_flow(self):
        self.speak("Email system ready. Recipient name or email?")
        to_raw = self.listen()
        if not to_raw or "cancel" in to_raw: return
        recipient = to_raw.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
        
        self.speak(f"Subject for {recipient}?")
        subject = self.listen()
        if not subject or "cancel" in subject: return
        
        self.speak("What is the message?")
        body = self.listen(timeout=15, phrase_limit=30)
        if not body: return
        
        self.speak("Say 'send' to confirm or 'cancel'.")
        confirm = self.listen()
        if any(w in confirm for w in ["send", "yes", "yeah", "confirm"]):
            try:
                outlook = win32com.client.Dispatch("Outlook.Application")
                mail = outlook.CreateItem(0)
                mail.To = recipient
                mail.Subject = subject
                mail.Body = body
                mail.Send()
                self.speak("Message dispatched.")
            except Exception as e:
                self.speak(f"Mail error: {e}")
        else:
            self.speak("Mail cancelled.")

    # --- SYSTEM COMMANDS ---
    def process_system_command(self, query):
        # Navigation
        if 'open' in query:
            app = query.replace("open", "").strip()
            self.speak(f"Launching {app}")
            pyautogui.press('win'); time.sleep(0.5); pyautogui.write(app); pyautogui.press('enter')
        elif 'go to' in query:
            site = query.replace("go to", "").strip()
            if not site.startswith("http"): site = "https://" + site
            webbrowser.get('edge').open(site)
        
        # Hardware
        elif 'set volume to' in query:
            match = re.search(r'\d+', query)
            if match: self.set_volume(match.group())
        elif 'set brightness to' in query:
            match = re.search(r'\d+', query)
            if match: self.set_brightness(match.group())
        elif 'volume up' in query: pyautogui.press('volumeup')
        elif 'volume down' in query: pyautogui.press('volumedown')
        
        # Windows
        elif 'switch app' in query or 'switch window' in query: self.switch_to_next_window()
        elif 'switch to' in query:
            target = query.replace("switch to", "").strip()
            self.switch_to_next_window() # Simple cycle for now, or use specific logic
        elif 'close' in query:
            target = query.replace("close", "").strip()
            if target: self.close_specific_window(target)
            else: pyautogui.hotkey('alt', 'f4')
        
        # Desktop
        elif 'scroll' in query:
            if 'up' in query: pyautogui.scroll(800)
            else: pyautogui.scroll(-800)
        elif 'take a screenshot' in query or 'take screenshot' in query: self.take_screenshot()
        elif 'enter' in query: pyautogui.press('enter')
        elif 'backspace' in query: pyautogui.press('backspace')
        
        # Status/Exit
        elif 'shutdown' in query: 
            self.speak("Shuting down in 5 seconds.")
            os.system("shutdown /s /t 5")
            return False
        return True

    # --- HELPERS ---
    def set_volume(self, level):
        try:
            level = max(0, min(100, int(level)))
            device = AudioUtilities.GetDefaultAudioEndpoint(EDataFlow.eRender, ERole.eMultimedia)
            vol = cast(device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
            vol.SetMasterVolumeLevelScalar(level / 100, None)
            self.speak(f"Vol {level}%")
        except: pass

    def set_brightness(self, level):
        try:
            sbc.set_brightness(max(0, min(100, int(level))))
            self.speak(f"Brightness {level}%")
        except: pass

    def take_screenshot(self):
        desc = os.path.join(os.path.expanduser("~"), "Desktop")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(desc, f"Nexus_Snap_{ts}.png")
        pyautogui.screenshot().save(path)
        self.speak("Snapshot saved to desktop.")

    # --- MAIN LOOP ---
    def run(self):
        self.speak("Nexus Unified Kernel Online.")
        print("[KERNEL] Calibrating microphone...")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        while self.is_running:
            query = self.listen()
            if not query: 
                # Small visual indicator in logs
                print(".", end="", flush=True)
                continue
            print(f"\n[PROCESSED]: {query}")

            if "start dictation" in query:
                self.run_dictation()
            elif "send email" in query or "open mail" in query:
                self.run_mail_flow()
            elif WAKE_WORD in query:
                self.process_ai_dialog(query)
            else:
                if not self.process_system_command(query):
                    break

if __name__ == "__main__":
    NexusKernel().run()
