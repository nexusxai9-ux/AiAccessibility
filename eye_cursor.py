import os
import sys
import time
import urllib.request
import collections
import cv2
import numpy as np
import pyautogui
import mediapipe as mp
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import (
    FaceLandmarker, FaceLandmarkerOptions, RunningMode)

import shared_logger

# ── SETTINGS ──────────────────────────────────────────────────────────────────
SMOOTHING = 6
SENSITIVITY = 2.5
RECENTER_SPEED = 0.015

# Tracking box
EYE_RANGE_X = 0.14
EYE_RANGE_Y = 0.10

# Blink settings
BLINK_THRESH = 0.22
BLINK_COOLDOWN = 0.5
DOUBLE_CLICK_TIME = 0.8
# ──────────────────────────────────────────────────────────────────────────────

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "face_landmarker/face_landmarker/float16/1/face_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "face_landmarker.task")

# Landmarks
L_EYE_TOP = 159;
L_EYE_BOT = 145;
L_INNER = 133;
L_OUTER = 33
R_EYE_TOP = 386;
R_EYE_BOT = 374;
R_INNER = 362;
R_OUTER = 263
L_IRIS = 468;
R_IRIS = 473


def download_model():
    if os.path.exists(MODEL_PATH): return
    print("📥 Downloading model...")
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

        self.smooth_x = collections.deque(maxlen=SMOOTHING)
        self.smooth_y = collections.deque(maxlen=SMOOTHING)
        self.box_cx, self.box_cy = 0.5, 0.5

        self.last_click_t = 0.0
        self.eyes_closed_since = None

        pyautogui.FAILSAFE = False
        print("👁️  Eye Mouse Ready. Blink to click.")
        shared_logger.log("Visual Tracking Online")

    def _get_ear(self, lms, top, bot, inner, outer):
        v = dist(xy(lms[top]), xy(lms[bot]))
        h = dist(xy(lms[inner]), xy(lms[outer]))
        return v / (h + 1e-6)

    def _process_blinks(self, lms, now):
        ear_l = self._get_ear(lms, L_EYE_TOP, L_EYE_BOT, L_INNER, L_OUTER)
        ear_r = self._get_ear(lms, R_EYE_TOP, R_EYE_BOT, R_INNER, R_OUTER)
        avg_ear = (ear_l + ear_r) / 2

        if avg_ear < BLINK_THRESH:
            if self.eyes_closed_since is None:
                self.eyes_closed_since = now

            if now - self.eyes_closed_since > DOUBLE_CLICK_TIME and (now - self.last_click_t) > BLINK_COOLDOWN:
                pyautogui.doubleClick()
                shared_logger.log("Double Click Registered")
                self.last_click_t = now
                self.eyes_closed_since = None
        else:
            if self.eyes_closed_since is not None:
                duration = now - self.eyes_closed_since
                if 0.1 < duration < DOUBLE_CLICK_TIME and (now - self.last_click_t) > BLINK_COOLDOWN:
                    pyautogui.click()
                    shared_logger.log("Click Registered")
                    self.last_click_t = now
                self.eyes_closed_since = None

    def _move_cursor(self, lms):
        lx, ly = xy(lms[L_IRIS])
        rx, ry = xy(lms[R_IRIS])

        # Calculate centers correctly
        avg_x = (lx + rx) / 2
        avg_y = (lms[L_EYE_TOP].y + lms[R_EYE_TOP].y) / 2

        self.box_cx += (avg_x - self.box_cx) * RECENTER_SPEED
        self.box_cy += (avg_y - self.box_cy) * RECENTER_SPEED

        nx = (avg_x - self.box_cx) / (EYE_RANGE_X / 2)
        ny = (avg_y - self.box_cy) / (EYE_RANGE_Y / 2)

        tx = np.clip(0.5 + nx * SENSITIVITY * 0.5, 0.0, 1.0)
        ty = np.clip(0.5 + ny * SENSITIVITY * 0.5, 0.0, 1.0)

        self.smooth_x.append(tx * (self.sw - 1))
        self.smooth_y.append(ty * (self.sh - 1))
        pyautogui.moveTo(int(sum(self.smooth_x) / len(self.smooth_x)), int(sum(self.smooth_y) / len(self.smooth_y)))

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
                self._process_blinks(lms, time.monotonic())

            cv2.imshow("Eye Mouse", frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27): break
        self.cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    EyeMouse().run()