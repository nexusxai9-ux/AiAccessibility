import speech_recognition as sr
import requests
import os
import time
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 170)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id) # Select Zira (female, more natural)
elif len(voices) > 0:
    engine.setProperty('voice', voices[0].id)


def speak(text):
    if not text:
        return

    print(f"[ARIA] {text}")

    engine.say(text)
    engine.runAndWait()


def listen():
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True  # Enable dynamic thresholding for better noise adaptation
    r.pause_threshold = 0.8
    try:
        with sr.Microphone() as source:
            print("\n[ARIA] Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout=10, phrase_time_limit=10)
                print("[ARIA] Recognizing...")
                text = r.recognize_google(audio)
                print(f"[ARIA] Detected: {text}")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                print("[ARIA] Google Recognition service is down or no internet.")
                return None
            except Exception as e:
                print(f"[ARIA] Listen error: {e}")
                return None
    except OSError:
        speak("Error: Microphone is busy. Please close other voice applications.")
        print("[ARIA] OSError: Microphone likely in use by another script.")
        time.sleep(2)
        return None
    except Exception as e:
        print(f"[ARIA] Microphone error: {e}")
        return None


def ask_llama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama3.2", "prompt": prompt, "stream": False}
    try:
        # 90-second timeout to handle llama3.2's processing time
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "No response content.")

    except requests.exceptions.Timeout:
        print("[DEBUG] The AI took too long to respond.")
        return "I'm sorry, that request took too long to process."
    except requests.exceptions.ConnectionError:
        print("[DEBUG] Could not reach Ollama. Is the Ollama app running?")
        return "I can't connect to Ollama. Please check if the application is running."
    except Exception as e:
        print(f"[DEBUG] Unexpected Error: {e}")
        return "An unexpected error occurred."


def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def run():
    print("[ARIA] Checking Ollama connection...")
    if not check_ollama():
        speak("Warning: I cannot detect Ollama running on this system. Please make sure Ollama is started.")
    
    speak("Nexus AI is online. I am listening for your commands.")
    while True:
        user_input = listen()
        if user_input:
            input_lower = user_input.lower()
            
            if "nexus" in input_lower:
                # Clean the input to remove the wake word and everything before it
                wake_index = input_lower.find("nexus")
                clean_query = input_lower[wake_index + 5:].strip()

                # Check for exit commands
                if any(word in clean_query for word in ["exit", "goodbye", "stop", "quit"]):
                    speak("Goodbye!")
                    break

                # If nothing was said after the wake word
                if not clean_query:
                    speak("Yes? I am listening.")
                    continue

                print(f"[ARIA] Processing: {clean_query}")
                reply = ask_llama(clean_query)
                speak(reply)
            elif any(word in input_lower for word in ["go to sleep", "stop listening", "nexus exit"]):
                speak("Moving to background.")
                break


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[ARIA] Shutting down.")