"""
Voice-Controlled Outlook Email Sender
--------------------------------------
Requirements:
    pip install speechrecognition pywin32 pyttsx3 pyaudio openai-whisper

How to use:
    1. Run the script
    2. Say: "Send to abc@example.com"
    3. Say what the email is about (topic/subject)
    4. Dictate the email body
    5. Review the generated email and confirm to send
"""

import speech_recognition as sr
import pyttsx3
import win32com.client
import re
import time

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.5

engine = pyttsx3.init()
engine.setProperty("rate", 170)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)
elif len(voices) > 0:
    engine.setProperty('voice', voices[0].id)


def speak(text: str):
    """Convert text to speech and print it."""
    print(f"\n[MAIL] Assistant: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except: ...


def listen(prompt: str = "", timeout: int = 8, phrase_limit: int = 15) -> str:
    """
    Listen via microphone and return recognized text.
    Returns empty string on failure.
    """
    if prompt: speak(prompt)

    try:
        with sr.Microphone() as source:
            print("[MAIL] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            except sr.WaitTimeoutError:
                return ""
    except OSError:
        print("[MAIL] Microphone busy.")
        return ""
    except Exception as e:
        print(f"[MAIL] Mic error: {e}")
        return ""

    try:
        print("[MAIL] Recognizing...")
        text = recognizer.recognize_google(audio)
        print(f"[MAIL] You said: {text}")
        return text.strip()
    except sr.UnknownValueError:
        print("[MAIL] Recognition failed.")
        return ""
    except sr.RequestError:
        print("[MAIL] Service unavailable.")
        return ""


# ─────────────────────────────────────────────
# EMAIL EXTRACTION HELPERS
# ─────────────────────────────────────────────

def extract_email(text: str) -> str:
    """Pull an email address from spoken text."""
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if match: return match.group(0)

    spoken = text.lower()
    spoken = re.sub(r"\bat\b", "@", spoken)
    spoken = re.sub(r"\bdot\b", ".", spoken)
    spoken = re.sub(r"\s+", "", spoken)

    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", spoken)
    return match.group(0) if match else ""


def build_subject(topic: str) -> str:
    return topic.strip().capitalize()


def compose_email_body(topic: str, body_text: str) -> str:
    return (
        f"Dear Recipient,\n\n"
        f"{body_text.strip()}\n\n"
        f"Best regards"
    )


# ─────────────────────────────────────────────
# OUTLOOK SEND
# ─────────────────────────────────────────────

def send_outlook_email(to: str, subject: str, body: str):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.Subject = subject
        mail.Body = body
        mail.Send()
        return True
    except Exception as e:
        speak(f"Failed to send email. Error: {e}")
        print(f"[MAIL] Outlook error: {e}")
        return False


# ─────────────────────────────────────────────
# MAIN FLOW
# ─────────────────────────────────────────────

def main():
    speak("Voice Email Assistant is ready. Say 'send email' to begin, or 'quit' to exit.")

    while True:
        command = listen(timeout=10, phrase_limit=5)
        if not command: continue
        if "quit" in command.lower() or "exit" in command.lower():
            speak("Goodbye!")
            break

        if "send" in command.lower() and "email" in command.lower():
            run_email_flow()
        else:
            speak("Say 'send email' to start, or 'quit' to exit.")


def run_email_flow():
    to_email = ""
    attempts = 0
    while not to_email and attempts < 3:
        raw = listen(prompt="Who do you want to send the email to? Say the email address.", timeout=8, phrase_limit=10)
        to_email = extract_email(raw)
        if not to_email: speak(f"I heard '{raw}' but couldn't find a valid email. Try again.")
        attempts += 1

    if not to_email:
        speak("I couldn't get a valid email address. Cancelling.")
        return

    speak(f"Got it. Sending to {to_email}.")

    topic = ""
    while not topic:
        topic = listen(prompt="What is this email about? Say the subject or topic.", timeout=8, phrase_limit=12)

    subject = build_subject(topic)
    speak(f"Subject will be: {subject}.")

    body_text = ""
    while not body_text:
        body_text = listen(prompt="Now dictate the email body. Speak clearly.", timeout=15, phrase_limit=60)

    body = compose_email_body(topic, body_text)

    review = (
        f"\n{'─'*50}\n"
        f" EMAIL PREVIEW\n"
        f"{'─'*50}\n"
        f"To      : {to_email}\n"
        f"Subject : {subject}\n"
        f"Body    :\n{body}\n"
        f"{'─'*50}\n"
    )
    print(review)

    while True:
        speak(f"Ready to send to {to_email}. Say 'yes' to send, 'no' to cancel, or 'review' to hear it again.")
        confirm = listen(timeout=8, phrase_limit=5).lower()

        if any(word in confirm for word in ["yes", "send", "okay", "yeah", "sure", "confirmed"]):
            speak("Sending your email now.")
            success = send_outlook_email(to_email, subject, body)
            if success:
                speak("Your email has been sent successfully!")
                print("[MAIL] Email sent!")
            else:
                speak("I encountered an error while sending the email. Please check Outlook.")
                print("[MAIL] Email failed to send.")
            break
        elif any(word in confirm for word in ["no", "cancel", "stop", "don't"]):
            speak("Email cancelled. Say 'send email' to start again.")
            print("[MAIL] Cancelled.")
            break
        elif "review" in confirm:
            speak(f"Reviewing. Recipient: {to_email}. Subject: {subject}. Body: {body_text}.")
            continue
        elif not confirm:
            continue
        else:
            speak("I didn't quite catch that. Please say 'yes' to send or 'no' to cancel.")


if __name__ == "__main__":
    main()