import speech_recognition as sr
import pyttsx3
import webbrowser
import pyautogui
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
        self.engine.setProperty('rate', 170)
        voices = self.engine.getProperty('voices')
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)
        
        # State
        self.is_running = True
        self.current_window_index = 0
        self.mode = "COMMAND" # COMMAND, DICTATION, MAIL, DIALOG
        
        # Recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.5
        
        # Hardware Setup
        try:
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(EDGE_PATH))
        except:
            print("[KERNEL] Could not register Edge.")

    def speak(self, text):
        print(f"[NEXUS] {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[ERROR] TTS Failed: {e}")

    def listen(self, timeout=5, phrase_limit=5):
        try:
            with sr.Microphone() as source:
                print(f"\n[LISTENING] Mode: {self.mode}...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                    print("[RECOGNIZING...]")
                    query = self.recognizer.recognize_google(audio).lower()
                    print(f"[YOU]: {query}")
                    return query
                except:
                    return ""
        except OSError:
            print("[KERNEL] Microphone busy.")
            return ""
        except Exception as e:
            print(f"[KERNEL] Microphone error: {e}")
            return ""

    # --- ACTION MODULES ---
    
    def process_ai_dialog(self, query):
        wake_index = query.lower().find(WAKE_WORD)
        clean_query = query[wake_index + len(WAKE_WORD):].strip()
        
        if not clean_query:
            self.speak("Yes? I am listening. What can I help you with?")
            clean_query = self.listen(timeout=8)
            if not clean_query: return

        print(f"[AI] Processing: {clean_query}")
        url = "http://localhost:11434/api/generate"
        payload = {"model": "llama3.2", "prompt": clean_query, "stream": False}
        try:
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 200:
                reply = response.json().get("response", "No response.")
                self.speak(reply)
            else:
                self.speak("I'm sorry, I couldn't reach my AI brain. Is Ollama running?")
        except Exception as e:
            self.speak("I'm matching a connection error with my AI modules.")

    def process_system_command(self, query):
        if 'set volume to' in query:
            match = re.search(r'\d+', query)
            if match: self.set_volume(match.group())
        elif 'set brightness to' in query:
            match = re.search(r'\d+', query)
            if match: self.set_brightness(match.group())
        elif 'open' in query:
            app = query.replace("open", "").strip()
            self.speak(f"Launching {app}")
            pyautogui.press('win'); time.sleep(0.5); pyautogui.write(app); pyautogui.press('enter')
        elif 'go to' in query:
            site = query.replace("go to", "").strip()
            if not site.startswith("http"): site = "https://" + site
            webbrowser.get('edge').open(site)
        elif 'scroll down' in query: pyautogui.scroll(-800)
        elif 'scroll up' in query: pyautogui.scroll(800)
        elif 'take a screenshot' in query: self.take_screenshot()
        elif 'close' in query: 
            pyautogui.hotkey('alt', 'f4')
            self.speak("Closed window.")
        elif 'shutdown' in query: 
            self.speak("Shutting down in 5 seconds.")
            os.system("shutdown /s /t 5")
            return False
        return True

    def run_dictation(self):
        self.speak("Dictation mode active. Say stop dictation to exit.")
        while True:
            query = self.listen(timeout=10, phrase_limit=10)
            if "stop dictation" in query:
                self.speak("Stopped dictation.")
                break
            if query:
                pyautogui.write(f"{query} ", interval=0.01)

    def run_mail_flow(self):
        self.speak("Starting email flow.")
        to = ""
        while not to:
            self.speak("Who is the recipient?")
            raw = self.listen()
            if not raw or "cancel" in raw: return
            if "@" in raw or "dot" in raw:
                to = raw.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
            else:
                self.speak(f"I heard {raw}, but that doesn't sound like an email. Please repeat.")
        
        self.speak(f"Subject for {to}?")
        subject = self.listen()
        if not subject: subject = "No Subject"
        
        self.speak("What is the message?")
        body = self.listen(timeout=15, phrase_limit=30)
        if not body: body = "(No content)"
        
        while True:
            self.speak(f"Ready to send to {to}. Say yes to confirm, or no to cancel.")
            confirm = self.listen().lower()
            if any(word in confirm for word in ["yes", "send", "yeah", "sure"]):
                try:
                    outlook = win32com.client.Dispatch("Outlook.Application")
                    mail = outlook.CreateItem(0)
                    mail.To = to
                    mail.Subject = subject
                    mail.Body = body
                    mail.Send()
                    self.speak("Email sent successfully.")
                    break
                except Exception as e:
                    self.speak(f"Failed to send email. {e}")
                    break
            elif any(word in confirm for word in ["no", "cancel", "stop"]):
                self.speak("Email cancelled.")
                break
            elif not confirm:
                continue
            else:
                self.speak("I didn't catch that. Say yes to send or no to cancel.")

    # --- HARDWARE HELPERS ---
    def set_volume(self, level):
        level = max(0, min(100, int(level)))
        device = AudioUtilities.GetDefaultAudioEndpoint(EDataFlow.eRender, ERole.eMultimedia)
        volume = cast(device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        self.speak(f"Volume {level}%")

    def set_brightness(self, level):
        sbc.set_brightness(max(0, min(100, int(level))))
        self.speak(f"Brightness {level}%")

    def take_screenshot(self):
        p = os.path.join(os.path.expanduser("~"), "Desktop", f"snap_{int(time.time())}.png")
        pyautogui.screenshot().save(p)
        self.speak("Screenshot saved.")

    # --- MAIN LOOP ---
    def run(self):
        self.speak("Nexus Kernel Online. All systems unified.")
        while self.is_running:
            query = self.listen()
            if not query: continue

            # Routing Logic
            if "start dictation" in query:
                self.run_dictation()
            elif "send email" in query:
                self.run_mail_flow()
            elif WAKE_WORD in query:
                self.process_ai_dialog(query)
            else:
                if not self.process_system_command(query):
                    break

if __name__ == "__main__":
    Kernel = NexusKernel()
    Kernel.run()
