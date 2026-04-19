import subprocess
import sys
import time

files = [
    "OPEN.py",
    "ai.py",
    "DICTATION.py",
    "EYE _CURSOR.py",
    "mail.py"
]

processes = []

for file in files:
    try:
        p = subprocess.Popen([sys.executable, file])
        processes.append(p)
        print(f"Started: {file}")
        time.sleep(1)  # prevents system overload
    except Exception as e:
        print(f"Error starting {file}: {e}")

# keep script alive (optional)
try:
    while True:
        pass
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
    print("All processes stopped.")