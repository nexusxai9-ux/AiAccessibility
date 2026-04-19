"""
NEXUS AI — Speech-to-Text Dictation Module
Say "start dictation" → types everything you say.
Say "stop dictation"  → returns to sleep.
Run standalone: python modules/stt_dictation.py
"""
import speech_recognition as sr
import pyautogui
import pyttsx3
import sys


import shared_logger


def speak(text):
    print(f"[STT] {text}")
    shared_logger.log(text)
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(text)
        engine.runAndWait()
    except:
        pass


def run():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("[STT] Speech-to-Text Dictation Online")
    speak("System ready. Say start dictation to begin.")

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            while True:
                # PHASE 1: SLEEPING — wait for wake phrase
                while True:
                    try:
                        audio = recognizer.listen(source, phrase_time_limit=3)
                        text = recognizer.recognize_google(audio).lower()
                        if "start dictation" in text:
                            speak("Started dictation.")
                            break
                    except (sr.UnknownValueError, sr.RequestError):
                        continue

                # PHASE 2: ACTIVE — type everything spoken
                while True:
                    try:
                        print("[STT] Listening...")
                        audio = recognizer.listen(source, phrase_time_limit=5)
                        text = recognizer.recognize_google(audio).lower()
                        if "stop dictation" in text:
                            speak("Stopped dictation.")
                            break
                        print(f"[STT] Typing: {text}")
                        pyautogui.write(f"{text} ", interval=0.01)
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        print(f"[STT] Service error: {e}")
                        break

    except KeyboardInterrupt:
        speak("Shutting down.")
        sys.exit()


if __name__ == "__main__":
    run()