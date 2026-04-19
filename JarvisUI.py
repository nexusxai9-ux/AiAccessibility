import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
import os
import sys
import threading
import time
import math
import subprocess
import shared_logger
import pyttsx3

# ================== CONFIG ==================
ORB_IMAGE_PATH = "nexus_orb.png"
WINDOW_SIZE = 350
STATUS_COLOR = "#00D1FF"

class JarvisHUD(ctk.CTk):
    def __init__(self, controller_callback=None):
        super().__init__()

        self.controller_callback = controller_callback
        
        # Voice Engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        
        # Window Setup
        self.title("JARVIS HUD")
        self.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE + 100}")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#000001") 
        self.configure(fg_color="#000001")
        
        # Position
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{sw - WINDOW_SIZE - 20}+{sh - WINDOW_SIZE - 120}")

        self.is_hovered = False
        self.pulse = 0
        self.last_msg = ""
        
        self.load_assets()
        self.setup_ui()
        self.animate()
        
        # Start log monitoring thread
        threading.Thread(target=self.monitor_logs, daemon=True).start()

        # Dragging support
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<Button-3>", self.show_menu)

    def load_assets(self):
        if not os.path.exists(ORB_IMAGE_PATH):
            self.orb_photo = None
            return
        pil_img = Image.open(ORB_IMAGE_PATH).convert("RGBA")
        pil_img = pil_img.resize((220, 220), Image.Resampling.LANCZOS)
        self.orb_photo = ImageTk.PhotoImage(pil_img)
        self.pil_img_base = pil_img

    def setup_ui(self):
        # Canvas for the Orb
        self.canvas = tk.Canvas(self, width=WINDOW_SIZE, height=WINDOW_SIZE, bg="#000001", highlightthickness=0)
        self.canvas.pack()
        
        self.orb_container = self.canvas.create_image(WINDOW_SIZE/2, WINDOW_SIZE/2, image=self.orb_photo)
        
        # Real-time Status Label
        self.status_label = ctk.CTkLabel(self, text="SYSTEM IDLE", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color=STATUS_COLOR)
        self.status_label.pack(pady=5)
        
        self.sub_status = ctk.CTkLabel(self, text="Awaiting orders...", font=ctk.CTkFont(family="Consolas", size=10), text_color="#718096")
        self.sub_status.pack()

    def monitor_logs(self):
        """Continuously check for new logs and update the UI/Voice."""
        while True:
            try:
                msg = shared_logger.log_queue.get(timeout=0.5)
                self.after(0, lambda m=msg: self.update_status(m))
            except:
                pass

    def update_status(self, msg):
        # Prevent double telling if it's the same
        if msg == self.last_msg:
            return
        self.last_msg = msg
        
        # Update UI
        self.status_label.configure(text=msg.upper())
        self.sub_status.configure(text=f"TIMESTAMP: {time.strftime('%H:%M:%S')}")
        
        # Voice Feedback (in a separate thread to not block UI)
        threading.Thread(target=self.speak, args=(msg,), daemon=True).start()

    def speak(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except:
            pass

    def animate(self):
        self.pulse += 0.05
        brightness = 1.0 + (math.sin(self.pulse) * 0.2)
        
        if hasattr(self, 'pil_img_base'):
            enhancer = ImageEnhance.Brightness(self.pil_img_base)
            pulsed_img = enhancer.enhance(brightness)
            self.orb_photo_anim = ImageTk.PhotoImage(pulsed_img)
            self.canvas.itemconfig(self.orb_container, image=self.orb_photo_anim)

        self.after(50, self.animate)

    def start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def show_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg="#12141C", fg=STATUS_COLOR, activebackground=STATUS_COLOR, activeforeground="black")
        menu.add_command(label="MANUAL REBOOT", command=lambda: self.update_status("System Reboot Initiated"))
        menu.add_separator()
        menu.add_command(label="EXIT", command=sys.exit)
        menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    app = JarvisHUD()
    app.mainloop()
