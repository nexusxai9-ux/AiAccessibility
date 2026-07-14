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
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pycaw.constants import EDataFlow, ERole


class NexusAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.current_window_index = 0
        import json

        with open("config.json") as f:
            data = json.load(f)

        self.edge_path = data["browser"]
        try:
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(self.edge_path))
        except Exception as e:
            print(f"Could not register Edge: {e}")

    def speak(self, text):
        print(f"[NEXUS] {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def switch_to_next_window(self):
        windows = [w for w in gw.getAllWindows() if w.title.strip() != "" and w.visible and len(w.title) > 2]
        if not windows:
            self.speak("No valid windows found to switch to.")
            return
        for _ in range(len(windows)):
            self.current_window_index = (self.current_window_index + 1) % len(windows)
            try:
                target = windows[self.current_window_index]
                if target.isMinimized: target.restore()
                target.activate()
                self.speak(f"Switched to {target.title[:15]}")
                return
            except Exception:
                continue
        self.speak("Could not switch to any available window.")

    def switch_to_specific_window(self, app_name):
        app_name = app_name.strip()
        windows = gw.getAllWindows()
        target_window = None
        for w in windows:
            if app_name.lower() in w.title.lower():
                target_window = w
                break
        if target_window:
            try:
                if target_window.isMinimized: target_window.restore()
                target_window.activate()
                self.speak(f"Switched to {target_window.title[:15]}")
            except Exception as e:
                self.speak(f"I found the window but couldn't focus it. Error: {e}")
        else:
            self.speak(f"I couldn't find an open window containing {app_name}")

    # --- HARDWARE CONTROLS ---
    def set_system_volume(self, level):
        try:
            level = max(0, min(100, int(level)))
            device = AudioUtilities.GetDefaultAudioEndpoint(EDataFlow.eRender, ERole.eMultimedia)
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            self.speak(f"Volume set to {level} percent.")
        except Exception as e:
            self.speak("I could not set the volume.")

    def set_brightness(self, level):
        try:
            level = max(0, min(100, int(level)))
            sbc.set_brightness(level)
            self.speak(f"Brightness set to {level} percent.")
        except Exception as e:
            self.speak("Brightness error.")

    # --- ACTIONS ---
    def take_screenshot(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(desktop_path, f"screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        self.speak("Screenshot captured and saved to your desktop.")

    def perform_shutdown(self):
        self.speak("Shutting down the system in 5 seconds.")
        self.speak("Do you want to shutdown?")
        confirm = self.listen()

        if "yes" in confirm:
            os.system("shutdown /s /t 5")
        return False

    def close_target(self, target):
        """Finds and closes ALL matching windows, ignoring the currency page."""
        target = target.lower().strip()

        # 1. Protection check for the keyword
        if "currency" in target:
            self.speak("I cannot close the currency page. It is protected.")
            return True

        try:
            # 2. Find ALL windows matching the target
            all_windows = gw.getAllWindows()
            matching_windows = [w for w in all_windows if target in w.title.lower()]

            if not matching_windows:
                return False

            count = 0
            for win in matching_windows:
                # 3. Double safety check: Ensure we don't close the currency page if it happens to be in the list
                if "currency" in win.title.lower():
                    continue

                    # 4. Close the window
                if win.isMinimized: win.restore()
                win.activate()
                time.sleep(0.3)
                pyautogui.hotkey('alt', 'f4')
                count += 1

            if count > 0:
                self.speak(f"Closed {count} window(s) for {target}.")
                return True
            return False
        except Exception as e:
            return False

    # --- OPTIMIZED LISTENING ---
    def listen(self):
        r = sr.Recognizer()
        r.dynamic_energy_threshold = True

        with sr.Microphone() as source:
            print("\n[LISTENING...]")
            r.adjust_for_ambient_noise(source, duration=0.8)
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                query = r.recognize_google(audio).lower()
                print(f"[YOU SAID]: {query}")
                return query
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                return ""
            except Exception:
                return ""

    # --- MAIN ENGINE ---
    def process_command(self, query):
        print(f"[COMMAND] {query}")

        # 1. VOLUME/BRIGHTNESS
        if 'set volume to' in query:
            match = re.search(r'\d+', query)
            if match: self.set_system_volume(match.group())

        elif 'set brightness to' in query:
            match = re.search(r'\d+', query)
            if match: self.set_brightness(match.group())


        # 2. KEYBOARD
        elif 'enter' in query:
            pyautogui.press('enter');
            self.speak("Enter pressed.")
        elif 'backspace' in query or 'delete' in query:
            pyautogui.press('backspace');
            self.speak("Backspace pressed.")
        elif 'volume up' in query or 'louder' in query:
            pyautogui.press('volumeup')
        elif 'volume down' in query or 'quieter' in query:
            pyautogui.press('volumedown')
        elif 'brightness up' in query:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(current + 10)
        elif 'brightness down' in query:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(current - 10)

        # 3. NAVIGATION
        elif 'go to' in query or 'open website' in query:
            site = query.replace("go to", "").replace("open website", "").strip()
            if site:
                if not site.startswith("http"): site = "https://" + site
                self.speak(f"Opening {site}")
                webbrowser.get('edge').open(site)

        # 4. SCROLLING
        elif 'scroll down' in query:
            pyautogui.scroll(-800)
        elif 'scroll up' in query:
            pyautogui.scroll(800)

        # 5. APPS
        elif 'open' in query and 'website' not in query:
            app = query.replace("open", "").strip()
            self.speak(f"Launching {app}")
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app)
            pyautogui.press('enter')

        # 6. EDITING, SELECTION & SWITCHING
        elif 'switch to' in query:
            app_name = query.replace("switch to", "").strip()
            if app_name:
                self.switch_to_specific_window(app_name)
            else:
                self.speak("Please specify which app to switch to.")

        elif 'switch app' in query:
            self.switch_to_next_window()

        elif 'select all' in query:
            pyautogui.hotkey('ctrl', 'a')
            self.speak("Text selected.")

        elif 'select word' in query:
            pyautogui.hotkey('ctrl', 'shift', 'right')
            self.speak("Word selected.")

        elif 'select line' in query:
            pyautogui.press('home')
            pyautogui.hotkey('shift', 'end')
            self.speak("Line selected.")

        elif 'copy' in query:
            pyautogui.hotkey('ctrl', 'c')
            self.speak("Copied.")

        elif 'cut' in query:
            pyautogui.hotkey('ctrl', 'x')
            self.speak("Cut.")

        elif 'paste' in query:
            pyautogui.hotkey('ctrl', 'v')
            self.speak("Pasted.")

        elif 'deselect' in query or 'cancel selection' in query:
            pyautogui.press('right')
            self.speak("Deselected.")

        # 7. SEARCH
        elif 'search' in query:
            search_query = query.replace("search for", "").replace("search", "").strip()
            if search_query:
                self.speak(f"Searching for {search_query}")
                webbrowser.get('edge').open(f"https://www.google.com/search?q={search_query}")

        # 8. VISION / SCREENSHOT
        elif 'take a screenshot' in query or 'take screenshot' in query:
            self.take_screenshot()
        elif 'analyze screen' in query:
            img_path = "temp_analysis.png"
            pyautogui.screenshot().save(img_path)
            img = cv2.imread(img_path)
            cv2.imshow("Nexus Vision", img)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()

        # 9. CLOSING
        elif 'close' in query:
            target = query.replace("close", "").strip()
            if "tab" in target:
                pyautogui.hotkey('ctrl', 'w')
                self.speak("Closing tab.")
            elif target:
                if not self.close_target(target):
                    self.speak(f"Could not find {target}. Closing active window.")
                    pyautogui.hotkey('alt', 'f4')
            else:
                pyautogui.hotkey('alt', 'f4')
                self.speak("Closing current window.")

        # 10. SYSTEM
        elif 'shutdown' in query:
            return self.perform_shutdown()
        return True

    def run(self):
        self.speak("Nexus systems online. All modules active.")
        while True:
            query = self.listen()
            if not query: continue
            if not self.process_command(query):
                break


if __name__ == "__main__":
    nexus = NexusAssistant()
    nexus.run()