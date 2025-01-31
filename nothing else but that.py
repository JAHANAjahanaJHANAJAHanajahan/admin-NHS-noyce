import pyautogui
import os

BASE_DIR = os.getcwd()
whole_screen_capture = pyautogui.screenshot()
whole_screen_capture.save(os.path.join(BASE_DIR, 'image test.png'))

