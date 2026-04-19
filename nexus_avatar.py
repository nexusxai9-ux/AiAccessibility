import sys
import math
import time
import subprocess
import os
from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient, QAction, QPainterPath

# ================== CONFIG ==================
MODULES = {
    "CORE AI": "OPEN.py",
    "DIALOG": "ai.py",
    "EYE CURSOR": "eye_cursor.py",
    "DICTATION": "DICTATION.py",
    "MAIL": "mail.py"
}

class NexusAvatar(QWidget):
    def __init__(self):
        super().__init__()
        
        # Setup frameless and always on top, and click-through only allowed if we don't want menus
        # But we want menus, so keep it clickable.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # Transparent background for the widget
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Bottom Right Positioning
        screen = QApplication.primaryScreen().geometry()
        size = 350
        self.setGeometry(screen.width() - size - 50, screen.height() - size - 100, size, size)
        
        self.angle = 0
        self.pulse = 0
        self.dragging = False
        self.drag_position = QPoint()
        
        self.processes = {}
        
        # Animation loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30) # ~33fps
        
    def animate(self):
        self.angle += 3
        if self.angle >= 360:
            self.angle -= 360
        self.pulse += 0.1
        self.update() # triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.width() / 2
        cy = self.height() / 2
        
        # 1. Draw glowing center aura (pulsing)
        pulse_radius = 45 + math.sin(self.pulse) * 12
        grad = QRadialGradient(cx, cy, pulse_radius)
        grad.setColorAt(0, QColor(0, 209, 255, 150)) # Bright cyan core
        grad.setColorAt(0.5, QColor(0, 100, 255, 80)) # Bleeding blue
        grad.setColorAt(1, QColor(0, 209, 255, 0))    # Transparent edge
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(pulse_radius), int(pulse_radius))
        
        # 2. Draw sharp inner core
        painter.setBrush(QColor(0, 0, 0, 200))
        painter.setPen(QPen(QColor(0, 209, 255, 255), 2))
        core_radius = 30 + math.sin(self.pulse * 1.5) * 3
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(core_radius), int(core_radius))
        
        # Draw text in the center
        painter.setPen(QColor(0, 255, 255, 255))
        font = painter.font()
        font.setFamily("Consolas")
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(int(cx - 18), int(cy + 4), "NEXUS")

        # 3. Draw rotating high-tech outer rings
        # Ring settings: [radius_offset, color, speed_multiplier, dash_pattern]
        rings = [
            (80, QColor(0, 255, 171, 200), 1, None),          # Inner cyan-green
            (100, QColor(0, 209, 255, 255), -1.5, [10, 10]),   # Middle broken blue
            (120, QColor(0, 75, 150, 150), 0.5, [40, 20, 10, 20]), # Outer slow dark blue
        ]
        
        for r_offset, color, speed, dash in rings:
            pen = QPen(color)
            pen.setWidthF(3.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            
            if dash:
                pen.setDashPattern(dash)
                
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Apply individual rotation speed
            current_angle = self.angle * speed
            
            # Draw arcs
            # For drawing, QRectF is required
            rect = QRectF(cx - r_offset, cy - r_offset, r_offset * 2, r_offset * 2)
            
            # PyQt arc span is in 1/16ths of a degree
            painter.drawArc(rect, int(current_angle * 16), 120 * 16)
            painter.drawArc(rect, int((current_angle + 180) * 16), 120 * 16)

        painter.end()

    # --- Interaction logic (Drag & Right Click Menu) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # Style the menu to match a sleek cyberpunk/AI vibe
        menu.setStyleSheet('''
            QMenu {
                background-color: rgba(10, 11, 16, 240);
                color: #00D1FF;
                border: 1px solid #00D1FF;
                font-family: Consolas;
                font-size: 13px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 25px;
            }
            QMenu::item::selected {
                background-color: rgba(0, 209, 255, 60);
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #1E222D;
                margin: 5px 15px;
            }
        ''')
        
        # Add module toggles
        for name, file in MODULES.items():
            state = "🔵 RUNNING" if name in self.processes else "⚪ STOPPED"
            action = QAction(f"{state} - {name}", self)
            action.triggered.connect(lambda checked, n=name, f=file: self.toggle_module(n, f))
            menu.addAction(action)
            
        menu.addSeparator()
        exit_action = QAction("🛑 SHUTDOWN NEXUS", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        
        menu.exec(event.globalPos())

    def toggle_module(self, name, file):
        if name in self.processes:
            self.processes[name].terminate()
            del self.processes[name]
            print(f"[{name}] module terminated.")
        else:
            try:
                # launch detached so it survives UI restarts if necessary, 
                # or bound to UI if we keep the handles.
                flags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                p = subprocess.Popen([sys.executable, file], creationflags=flags)
                self.processes[name] = p
                print(f"[{name}] module instantiated.")
            except Exception as e:
                print(f"[{name}] Initialization Error: {e}")

    def closeEvent(self, event):
        # Gracefully shut down all running subprocesses when the avatar closes
        for name, p in self.processes.items():
            try:
                p.terminate()
                print(f"Terminated {name}")
            except:
                pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Enable high DPI scaling for crisp visuals
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
    nexus = NexusAvatar()
    nexus.show()
    sys.exit(app.exec())
