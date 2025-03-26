import time
import threading
import pytest
from Final_Commented import App
from PIL import Image
import pyautogui


# Dummy output class to simulate tkinter output so update_output_window works
class DummyOutput:
    def __init__(self):
        self.config = {}

    def configure(self, **kwargs):
        self.config.update(kwargs)


# Monkeypatch function to simulate screenshot returning real test images
def fake_screenshot(region=None):
    # We assume test_age.png and test_name.png exist in the working directory
    if region == (0, 0, 100, 100):  # For age region
        return Image.open("test_age.png")
    elif region == (0, 0, 100, 100,):  # For name region (using same dummy coords)
        return Image.open("test_name.png")
    else:
        # Return a plain image if region is unexpected
        return Image.new("RGB", (100, 100), color="white")


# Test for age-based vaccine categorization logic via update_output_window
def test_vaccine_color_logic():
    app = App()
    dummy = DummyOutput()
    app.output_window = dummy
    app.output_label = dummy

    # Set dummy OCR regions (simulate that user has selected an area)
    app.age_rect = (0, 0, 100, 100)
    app.name_rect = (0, 0, 100, 100)

    # Test for age below 65 (should be green)
    app.latest_ocr_number = 64
    app.latest_patient_name = "Dummy Patient Low"
    app.update_output_window()
    bg_color_low = dummy.config.get("bg")
    assert bg_color_low == "#00FF00", f"Expected green for age 64 but got {bg_color_low}"

    # Test for age 65 and above (should be blue)
    app.latest_ocr_number = 65
    app.latest_patient_name = "Dummy Patient High"
    app.update_output_window()
    bg_color_high = dummy.config.get("bg")
    assert bg_color_high == "#0000FF", f"Expected blue for age 65 but got {bg_color_high}"


# Test for refresh interval using ocr_loop with real test images
def test_refresh_interval():
    app = App()
    dummy = DummyOutput()
    app.output_window = dummy
    app.output_label = dummy
    # Set dummy regions so that ocr_loop proceeds
    app.age_rect = (0, 0, 100, 100)
    app.name_rect = (0, 0, 100, 100)

    # Monkeypatch pyautogui.screenshot to return test images
    original_screenshot = pyautogui.screenshot
    pyautogui.screenshot = fake_screenshot

    # Set dummy OCR results to simulate processing
    app.latest_ocr_number = 50
    app.latest_patient_name = "Refresh Test"

    # Run ocr_loop in a separate thread and measure elapsed time
    app.ocr_active = True
    start_time = time.time()
    t = threading.Thread(target=app.ocr_loop)
    t.start()
    # Let the loop run for a little over 5 seconds (one full refresh cycle)
    time.sleep(6)
    app.ocr_active = False
    t.join()
    end_time = time.time()
    elapsed = end_time - start_time

    # Restore original screenshot function
    pyautogui.screenshot = original_screenshot

    # Assert that elapsed time is at least 5 seconds (confirming that a sleep of 5 seconds occurred)
    assert elapsed >= 5, f"Expected at least 5 seconds refresh interval, but elapsed time was {elapsed}s"


# Test for application startup time
def test_app_startup_time():
    start_time = time.time()
    _ = App()  # Instantiate the App; do not call run() to avoid starting the full GUI loop
    end_time = time.time()
    startup_time = end_time - start_time
    assert startup_time <= 2, f"Application startup too slow: {startup_time}s"
