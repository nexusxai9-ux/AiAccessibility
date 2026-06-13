import customtkinter as ctk
import tkinter as tk
import subprocess
import sys
import threading
import time
import os
import math
from datetime import datetime

# ================== CONFIG ==================

MODULES = {
    "NEXUS KERNEL": "nexus_kernel.py",
    "EYE CURSOR": "eye_cursor.py"
}

ctk.set_appearance_mode("Dark")

class JarvisRotatingHUD(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("NEXUS ROTATOR")
        self.geometry("380x520")
        self.overrideredirect(True)
        self.attributes("-topmost", False)  # Ensure it's not on top
        self.attributes("-alpha", 0.95)
        
        # Move to back (Windows only optimization)
        try:
            import ctypes
            # HWND_BOTTOM = 1
            # SWP_NOSIZE = 1, SWP_NOMOVE = 2, SWP_NOACTIVATE = 16
            ctypes.windll.user32.SetWindowPos(self.winfo_id(), 1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except:
            self.lower()

        self.configure(fg_color="#0A0B10")
        
        # Bottom Right Position
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"+{screen_width - 400}+{screen_height - 580}")

        self.processes = {}
        self.is_running = True
        self.angle = 0

        self.setup_ui()
        self.start_threads()
        
        # Auto-start all modules (DISABLED to prevent PyAudio conflicts)
        self.after(500, self.auto_start_modules)

        # Dragging
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        # ─── HEADER ───
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(15, 0))
        
        ctk.CTkLabel(header, text="NEXUS KERNEL", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00D1FF").pack(side="left")
        
        # Cross Button - Closes ONLY the UI
        self.close_btn = ctk.CTkButton(header, text="✕", width=30, height=30, fg_color="transparent", hover_color="#FF4D4D", command=self.close_ui_only)
        self.close_btn.pack(side="right")

        # ─── ROTATING VISUALIZER ───
        self.canvas = tk.Canvas(self, width=300, height=300, bg="#0A0B10", highlightthickness=0)
        self.canvas.pack(pady=20)
        
        # ─── LOG BOX (Activity) ───
        self.log_frame = ctk.CTkFrame(self, fg_color="#12141C", border_width=1, border_color="#1E222D")
        self.log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.log_box = ctk.CTkTextbox(self.log_frame, fg_color="transparent", font=ctk.CTkFont(family="Consolas", size=10), text_color="#718096")
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.append_log("Systems initialized.")

        # Right-click menu for module control
        self.bind("<Button-3>", self.show_menu)

    def draw_rotating_ui(self):
        self.canvas.delete("jarvis")
        cx, cy = 150, 150
        
        # Rotating Arcs
        self.angle += 2
        colors = ["#004B5C", "#00D1FF", "#00FFAB"]
        
        for i in range(3):
            r = 80 + (i * 15)
            # Offset angles
            start = self.angle * (1 if i%2==0 else -1) + (i * 120)
            self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=start, extent=60, outline=colors[i], width=3, style="arc", tags="jarvis")
            self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=start+180, extent=60, outline=colors[i], width=3, style="arc", tags="jarvis")

        # Inner pulsing core
        pulse = abs(math.sin(time.time() * 2)) * 10
        r_inner = 30 + pulse
        self.canvas.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner, outline="#00D1FF", width=1, tags="jarvis")
        self.canvas.create_text(cx, cy, text="NEXUS", fill="#00D1FF", font=("Segoe UI", 10, "bold"), tags="jarvis")

        if self.is_running:
            self.after(30, self.draw_rotating_ui)

    def show_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg="#12141C", fg="white", activebackground="#00D1FF")
        for name, file in MODULES.items():
            state = "●" if name in self.processes else "○"
            menu.add_command(label=f"{state} {name}", command=lambda n=name, f=file: self.toggle_module(n, f))
        menu.post(event.x_root, event.y_root)

    def auto_start_modules(self):
        for name, file in MODULES.items():
            if name not in self.processes:
                self.toggle_module(name, file)

    def toggle_module(self, name, file):
        if name in self.processes:
            self.processes[name].terminate()
            del self.processes[name]
            self.append_log(f"Terminated {name}")
        else:
            try:
                # Optimized Environment for child processes to prevent OpenBLAS memory errors
                env = os.environ.copy()
                env["OPENBLAS_NUM_THREADS"] = "1"
                env["MKL_NUM_THREADS"] = "1"
                env["OMP_NUM_THREADS"] = "1"
                env["NUMEXPR_NUM_THREADS"] = "1"

                flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                p = subprocess.Popen(
                    [sys.executable, file],
                    creationflags=flags,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env
                )
                self.processes[name] = p
                self.append_log(f"Started {name}")
                threading.Thread(target=self.read_process_output, args=(name, p), daemon=True).start()
            except Exception as e:
                self.append_log(f"Error: {e}")

    def read_process_output(self, name, process):
        for line in iter(process.stdout.readline, ''):
            if line:
                # Use after to safely update UI from thread
                self.after(0, lambda m=f"[{name}] {line.strip()}": self.append_log(m))

    def append_log(self, text):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{t}] {text}\n")
        self.log_box.see("end")

    def start_threads(self):
        self.draw_rotating_ui()

    def close_ui_only(self):
        """Closes the UI window but leaves the main thread/processes alive if possible."""
        self.is_running = False
        self.destroy()
        # On Windows, child processes from Popen with CREATE_NEW_CONSOLE survive the UI Close.
        print("UI Closed. Modules remain active.")

if __name__ == "__main__":
    app = JarvisRotatingHUD()
    app.mainloop()
    /
