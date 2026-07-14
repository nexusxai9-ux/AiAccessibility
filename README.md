# 🚀 AI Accessibility System

An **AI-powered accessibility system** designed to help people with physical disabilities (especially users without hands) operate a computer using **voice commands, eye tracking, and automation**.

The AI in this project is mainly used for **conversation and understanding user commands**, making interaction simple and natural.

---

## 🌟 Features

* 🎙️ **Voice Control System**
  Control your computer using natural speech

* 👁️ **Eye Cursor Tracking**
  Move and control the cursor using eye movements

* 💬 **AI Conversation Assistant**
  Understands user input and responds / processes commands

* ⌨️ **Hands-Free Interaction**
  No need for keyboard or mouse

* 🧩 **Modular System**
  Each feature works independently (you can run files individually)

---

## 🧠 Problem Statement

Millions of people struggle to use traditional input devices like:

* Keyboard
* Mouse
* Touch interfaces

This creates a major accessibility gap.

---

## 💡 Solution

This project solves the problem by combining:

* Voice recognition
* Eye tracking
* AI-based command understanding

To create a **fully assistive, hands-free computing system**.

---

## 🏗️ Project Structure

```bash
AiAccessibility/
│
├── ai.py              # AI conversation + command understanding
├── open.py            # Executes system commands (open apps, etc.)
├── eye_cursor.py      # Eye tracking & cursor control
├── dictation.py       # Speech-to-text / voice input
├── utils/             # Helper functions (optional)
└── README.md
```

---

## ⚠️ Important Note (How to Run)

👉 **Each file works independently**

You can run modules individually based on your need:

* Run **eye tracking only** → `eye_cursor.py`
* Run **voice dictation only** → `dictation.py`
* Run **AI assistant** → `ai.py`
* Run **command execution** → `open.py`

⚠️ Full integration of all modules is still in progress.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/nexusxai9-ux/AiAccessibility.git
cd AiAccessibility
```

---

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

---

### 3. Activate Environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Mac/Linux:**

```bash
source .venv/bin/activate
```

---

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run any module individually:

```bash
python ai.py
```

or

```bash
python eye_cursor.py
```

or

```bash
python dictation.py
```

or

```bash
python open.py
```

---

## 🔗 How It Works

1. User gives input (voice or eye movement)
2. AI processes and understands the command
3. System executes the action

---

## 📌 Current Status

* ✅ Core features built
* ✅ Individual modules working
* ⚠️ Full system integration pending
* ⚠️ Needs dependency setup

---

## 🚧 Future Improvements

* 🔗 Full integration of all modules
* 🌐 Cross-platform support (currently more Windows-focused)
* 🤖 Improved AI conversation capabilities
* 🎯 Better accuracy in eye tracking

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Make changes
4. Submit a Pull Request

##

---

## 👨‍💻 Author

**Aarav Jhamb**

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---

## 🔥 Important (For Developers)

👉 Make sure to create a `requirements.txt` file

If running fails, install dependencies manually:

```bash
pip install opencv-python mediapipe pyautogui speechrecognition pyaudio
```

(Modify based on your actual libraries)

---

## 🎯 Vision

To make computers **accessible for everyone**, regardless of physical limitations.
