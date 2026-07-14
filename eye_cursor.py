import os
import sys
import time
import urllib.request
import cv2
import numpy as np
import pyautogui
pyautogui.FAILSAFE = False
import mediapipe as mp
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import (
    FaceLandmarker, FaceLandmarkerOptions, RunningMode)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
# Smoothing: 0.1 (Very smooth/slow) to 0.9 (Very responsive/twitchy)
EMA_ALPHA = 0.25
SENSITIVITY = 3.0
DEADZONE = 0.02  # Ignore tiny movements in the center

# Mouth settings
MOUTH_OPEN_THRESH = 0.35
MIN_OPEN_TIME = 0.25  # Minimum to count as a click
DOUBLE_CLICK_TIME = 3.0  # Time required for double click
CLICK_COOLDOWN = 0.5
# ──────────────────────────────────────────────────────────────────────────────

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "face_landmarker/face_landmarker/float16/1/face_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "face_landmarker.task")

# Landmarks
L_IRIS = 468;
R_IRIS = 473
MOUTH_TOP = 13;
MOUTH_BOT = 14;
MOUTH_LEFT = 78;
MOUTH_RIGHT = 308


def download_model():
    if os.path.exists(MODEL_PATH): return
    print("[EYE CURSOR] Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def dist(a, b): return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def xy(lm): return lm.x, lm.y


class EyeMouse:
    def __init__(self):
        download_model()
        opts = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO, num_faces=1
        )
        self.lm = FaceLandmarker.create_from_options(opts)
        self.sw, self.sh = pyautogui.size()
        self.cam = cv2.VideoCapture(0)

        # Movement state
        self.cursor_x, self.cursor_y = self.sw / 2, self.sh / 2
        self.last_click_t = 0.0
        self.mouth_open_start = None

        print("[EYE CURSOR] Ready. Mouth open > 3s = Double Click.")

    def _get_mar(self, lms):
        v = dist(xy(lms[MOUTH_TOP]), xy(lms[MOUTH_BOT]))
        h = dist(xy(lms[MOUTH_LEFT]), xy(lms[MOUTH_RIGHT]))
        return v / (h + 1e-6)

    def _process_mouth(self, lms, now):
        mar = self._get_mar(lms)
        if mar > MOUTH_OPEN_THRESH:
            if self.mouth_open_start is None:
                self.mouth_open_start = now
        else:
            if self.mouth_open_start is not None:
                duration = now - self.mouth_open_start
                self.mouth_open_start = None

                if now - self.last_click_t > CLICK_COOLDOWN:
                    if duration >= DOUBLE_CLICK_TIME:
                        print(f"[EYE CURSOR] Double Click!")
                        pyautogui.doubleClick()
                    elif duration > MIN_OPEN_TIME:
                        print(f"[EYE CURSOR] Single Click!")
                        pyautogui.click()
                    self.last_click_t = now

    def _move_cursor(self, lms):
        # Average iris position
        tx = (lms[L_IRIS].x + lms[R_IRIS].x) / 2
        ty = (lms[L_IRIS].y + lms[R_IRIS].y) / 2

        # Map to screen space with sensitivity
        target_x = (tx - 0.5) * SENSITIVITY * self.sw + (self.sw / 2)
        target_y = (ty - 0.5) * SENSITIVITY * self.sh + (self.sh / 2)

        # Apply Deadzone
        if abs(target_x - self.cursor_x) < 5 and abs(target_y - self.cursor_y) < 5:
            return

        # Exponential Moving Average (Smoothing)
        self.cursor_x = self.cursor_x * (1 - EMA_ALPHA) + target_x * EMA_ALPHA
        self.cursor_y = self.cursor_y * (1 - EMA_ALPHA) + target_y * EMA_ALPHA

        pyautogui.moveTo(int(self.cursor_x), int(self.cursor_y))

    def run(self):
        while self.cam.isOpened():
            ok, frame = self.cam.read()
            if not ok: continue
            frame = cv2.flip(frame, 1)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = self.lm.detect_for_video(mp_img, int(time.time() * 1000))

            if result.face_landmarks:
                lms = result.face_landmarks[0]
                self._move_cursor(lms)
                self._process_mouth(lms, time.monotonic())

            if not os.environ.get("HIDE_EYE_WINDOW"):
                cv2.imshow("Eye Mouse", frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27): break

        self.cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    EyeMouse().run()
