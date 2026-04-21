import speech_recognition as sr
import requests
import os
import time
import pygame
from gtts import gTTS

# Initialize pygame mixer once for efficiency
pygame.mixer.init()


def speak(text):
    if not text:
        return

    print(f"[ARIA] {text}")

    # 1. Generate speech
    filename = "response.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(filename)

    # 2. Play using Pygame
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        # Keep the script running until the audio finishes
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.unload()  # Free the file so it can be deleted
    except Exception as e:
        print(f"[ARIA] Audio Error: {e}")
    finally:
        # 3. Cleanup: Remove the file to keep directory clean
        if os.path.exists(filename):
            os.remove(filename)


def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[ARIA] Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Increased timeout to ensure the listener works
            audio = r.listen(source, timeout=10, phrase_time_limit=10)
            text = r.recognize_google(audio)
            print(f"[ARIA] Detected: {text}")
            return text
        except Exception:
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


def run():
    speak("Nexus AI is online. How can I help you?")
    while True:
        user_input = listen()
        if user_input and "nexus" in user_input.lower():
            # Clean the input to remove the wake word
            clean_query = user_input.lower().replace("nexus", "").strip()

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


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[ARIA] Shutting down.")
        pygame.mixer.quit()