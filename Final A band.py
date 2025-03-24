import os
import pygame
import pyautogui
import sys
import pytesseract
import threading
import time
import tkinter as tk
from PIL import Image
import sqlite3
from datetime import datetime

# Set up pygame and tesseract
pygame.init()
pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), r"Tesseract-OCR/tesseract.exe")

# Connect to or create database
test = sqlite3.connect('NHS Database.sqlite')
cursor = test.cursor()
cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support for sqlite

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS patient (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    age REAL,
    vaccine_type TEXT,
    patient_name TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS vaccination (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    vaccine_type TEXT,
    date_administered TEXT,
    FOREIGN KEY (patient_id) REFERENCES patient(ID)
)
''')
test.commit()

# Helper function to letterbox images in the preview area
def letterbox_image(image, target_width, target_height, background_color=(50, 50, 50)):
    # Scales a pygame Surface to fit the target area, preserving aspect ratio
    orig_width, orig_height = image.get_size()
    scale = min(target_width / orig_width, target_height / orig_height)
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)
    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
    letterboxed_surface = pygame.Surface((target_width, target_height))
    letterboxed_surface.fill(background_color)
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    letterboxed_surface.blit(scaled_image, (x_offset, y_offset))
    return letterboxed_surface

class ScreenshotSelector:
    # Lets the user select a region on the screen
    def __init__(self):
        self.selected_rect = None

    def select_area(self):
        screen_width, screen_height = pyautogui.size()
        full_screen_pil = pyautogui.screenshot()
        mode = full_screen_pil.mode
        size = full_screen_pil.size
        data = full_screen_pil.tobytes()
        background = pygame.image.fromstring(data, size, mode)

        full_screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Select Area")
        full_screen.blit(background, (0, 0))
        pygame.display.flip()

        selecting = True
        start_pos = None
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    start_pos = event.pos
                if event.type == pygame.MOUSEMOTION and start_pos:
                    current_pos = event.pos
                    full_screen.blit(background, (0, 0))
                    x = min(start_pos[0], current_pos[0])
                    y = min(start_pos[1], current_pos[1])
                    width = abs(current_pos[0] - start_pos[0])
                    height = abs(current_pos[1] - start_pos[1])
                    rect = pygame.Rect(x, y, width, height)
                    pygame.draw.rect(full_screen, (255, 0, 0), rect, 2)
                    pygame.display.flip()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and start_pos:
                    end_pos = event.pos
                    x1 = min(start_pos[0], end_pos[0])
                    y1 = min(start_pos[1], end_pos[1])
                    x2 = max(start_pos[0], end_pos[0])
                    y2 = max(start_pos[1], end_pos[1])
                    self.selected_rect = (x1, y1, x2 - x1, y2 - y1)
                    selecting = False
                    break

        selected_image = pyautogui.screenshot(region=self.selected_rect)
        return self.selected_rect, selected_image

class App:
    # Main application class
    def __init__(self):
        self.width = 1150
        self.height = 400
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Screenshot Selector")
        self.clock = pygame.time.Clock()
        self.running = True

        self.age_rect = None
        self.age_image = None
        self.name_rect = None
        self.name_image = None

        self.ocr_active = False
        self.latest_ocr_number = None
        self.latest_patient_name = None

        self.database_comment = None

        self.output_window = None
        self.output_label = None

        self.manual_override = False
        self.manual_bg_color = None
        self.manual_text = None

        self.font = pygame.font.SysFont('Arial', 16)

        self.select_age_button_rect = pygame.Rect(50, 20, 200, 40)
        self.select_name_button_rect = pygame.Rect(300, 20, 200, 40)
        self.ocr_button_rect = pygame.Rect(550, 20, 200, 40)
        self.spawn_output_button_rect = pygame.Rect(800, 20, 200, 40)

        self.age_preview_area = pygame.Rect(50, 80, 500, 250)
        self.name_preview_area = pygame.Rect(600, 80, 500, 250)

        self.debug_toggle_rect = pygame.Rect(5, self.height - 35, 60, 30)
        self.debug_mode = False
        self.debug_less_rect = pygame.Rect(70, self.height - 35, 60, 30)
        self.debug_more_rect = pygame.Rect(135, self.height - 35, 60, 30)
        self.debug_drop_table = pygame.Rect(200, self.height - 35, 60, 30)
        self.debug_print_db_rect = pygame.Rect(265, self.height - 35, 60, 30)

        # Dictionary to track last processed data for each patient name
        self.last_processed = {}

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            if self.output_window:
                try:
                    self.update_output_window()
                    self.output_window.update_idletasks()
                    self.output_window.update()
                except tk.TclError:
                    self.output_window = None
                    self.ocr_active = False
            self.clock.tick(30)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.debug_toggle_rect.collidepoint(mouse_pos):
                    self.debug_mode = not self.debug_mode
                if self.debug_mode:
                    if self.debug_less_rect.collidepoint(mouse_pos):
                        self.latest_ocr_number = 50
                        print("Debug: Set OCR result to 50 (<65)")
                    if self.debug_more_rect.collidepoint(mouse_pos):
                        self.latest_ocr_number = 70
                        print("Debug: Set OCR result to 70 (>65)")
                    if self.debug_drop_table.collidepoint(mouse_pos):
                        cursor.execute('DROP TABLE IF EXISTS vaccination')
                        cursor.execute('DROP TABLE IF EXISTS patient')
                        print("Debug: Dropped patient and vaccination tables.")
                        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS patient (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            age REAL,
                            vaccine_type TEXT,
                            patient_name TEXT
                        )
                        ''')
                        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS vaccination (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            patient_id INTEGER,
                            vaccine_type TEXT,
                            date_administered TEXT,
                            FOREIGN KEY (patient_id) REFERENCES patient(ID)
                        )
                        ''')
                        test.commit()
                        print("Debug: Recreated tables.")
                    if self.debug_print_db_rect.collidepoint(mouse_pos):
                        self.print_database()
                if self.select_age_button_rect.collidepoint(mouse_pos):
                    self.start_age_selection()
                if self.select_name_button_rect.collidepoint(mouse_pos):
                    self.start_name_selection()
                if self.ocr_button_rect.collidepoint(mouse_pos) and self.age_image and self.name_image:
                    self.toggle_ocr()
                if self.spawn_output_button_rect.collidepoint(mouse_pos):
                    if self.output_window:
                        self.on_output_window_close()
                        print("Output window closed.")
                    else:
                        self.spawn_output_window()
                        print("Output window spawned.")

    def start_age_selection(self):
        # Temporarily switch to a small display for full screen capture
        pygame.display.set_mode((1, 1))
        pygame.time.delay(100)
        selector = ScreenshotSelector()
        result = selector.select_area()
        if result is not None:
            self.age_rect, selected_pil_image = result
            selected_pil_image = selected_pil_image.convert("RGB")
            mode = selected_pil_image.mode
            size = selected_pil_image.size
            data = selected_pil_image.tobytes()
            self.age_image = pygame.image.fromstring(data, size, mode)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Screenshot Selector")
        self.draw()
        pygame.display.flip()

    def start_name_selection(self):
        # Temporarily switch to a small display for full screen capture
        pygame.display.set_mode((1, 1))
        pygame.time.delay(100)
        selector = ScreenshotSelector()
        result = selector.select_area()
        if result is not None:
            self.name_rect, selected_pil_image = result
            selected_pil_image = selected_pil_image.convert("RGB")
            mode = selected_pil_image.mode
            size = selected_pil_image.size
            data = selected_pil_image.tobytes()
            self.name_image = pygame.image.fromstring(data, size, mode)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Screenshot Selector")
        self.draw()
        pygame.display.flip()

    def toggle_ocr(self):
        if not self.output_window:
            self.spawn_output_window()
        if self.ocr_active:
            self.ocr_active = False
            print("OCR deactivated.")
        else:
            self.ocr_active = True
            print("OCR activated.")
            threading.Thread(target=self.ocr_loop, daemon=True).start()

    def ocr_loop(self):
        while self.ocr_active:
            if self.age_rect:
                screenshot_age = pyautogui.screenshot(region=self.age_rect)
                processed_age = screenshot_age.convert("L")
                width, height = processed_age.size
                upscale_factor = 3
                processed_age = processed_age.resize((width * upscale_factor, height * upscale_factor),
                                                     resample=Image.Resampling.LANCZOS)
                threshold = 128
                processed_age = processed_age.point(lambda x: 0 if x < threshold else 255, '1')
                processed_age = processed_age.convert("L")
                processed_age_rgb = processed_age.convert("RGB")
                mode = processed_age_rgb.mode
                size = processed_age_rgb.size
                data = processed_age_rgb.tobytes()
                self.age_image = pygame.image.fromstring(data, size, mode)
                custom_config = "--psm 7 -c tessedit_char_whitelist=0123456789"
                ocr_result_age = pytesseract.image_to_string(processed_age, config=custom_config).strip()
                try:
                    self.latest_ocr_number = int(ocr_result_age)
                    print("OCR age result (number):", self.latest_ocr_number)
                except ValueError:
                    self.latest_ocr_number = None
                    print("OCR age result invalid or not a number:", ocr_result_age)
            if self.name_rect:
                screenshot_name = pyautogui.screenshot(region=self.name_rect)
                processed_name = screenshot_name.convert("L")
                width, height = processed_name.size
                upscale_factor = 3
                processed_name = processed_name.resize((width * upscale_factor, height * upscale_factor),
                                                       resample=Image.Resampling.LANCZOS)
                threshold = 128
                processed_name = processed_name.point(lambda x: 0 if x < threshold else 255, '1')
                processed_name = processed_name.convert("L")
                processed_name_rgb = processed_name.convert("RGB")
                mode = processed_name_rgb.mode
                size = processed_name_rgb.size
                data = processed_name_rgb.tobytes()
                self.name_image = pygame.image.fromstring(data, size, mode)
                ocr_result_name = pytesseract.image_to_string(processed_name).strip()
                self.latest_patient_name = ocr_result_name
                print("OCR name result:", self.latest_patient_name)
            time.sleep(10)

    def spawn_output_window(self):
        if self.output_window:
            return
        self.output_window = tk.Tk()
        self.output_window.title("OCR Output")
        self.output_window.geometry("300x300")
        self.output_window.protocol("WM_DELETE_WINDOW", self.on_output_window_close)
        self.output_label = tk.Label(self.output_window, text="Awaiting next input...", font=("Arial", 18))
        self.output_label.pack(expand=True, fill='both')
        self.manual_frame = tk.Frame(self.output_window, bg=self.output_window["bg"])
        self.manual_frame.place(relx=1.0, rely=1.0, anchor='se')
        btn_blue = tk.Button(self.manual_frame, text="Blue", command=self.manual_blue, font=("Arial", 8))
        btn_green = tk.Button(self.manual_frame, text="Green", command=self.manual_green, font=("Arial", 8))
        btn_clear = tk.Button(self.manual_frame, text="Clear", command=self.manual_clear, font=("Arial", 8))
        btn_blue.pack(side="right", padx=2)
        btn_green.pack(side="right", padx=2)
        btn_clear.pack(side="right", padx=2)

    def on_output_window_close(self):
        if self.output_window:
            self.output_window.destroy()
        self.output_window = None
        self.ocr_active = False
        print("Output window closed. OCR deactivated.")

    def update_output_window(self):
        if not self.output_window or not self.output_label:
            return
        if self.manual_override:
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(bg=self.manual_bg_color, text=self.manual_text)
            return
        if self.latest_ocr_number is not None and self.latest_patient_name is not None:
            if self.latest_ocr_number >= 65:
                bg_color = "#0000FF"
                computed_vaccine = "Blue"
            else:
                bg_color = "#00FF00"
                computed_vaccine = "Green"
            display_text = f"Age: {self.latest_ocr_number}  Name: {self.latest_patient_name}"
        else:
            bg_color = "#AAAAAA"
            display_text = "Awaiting next input..."
            computed_vaccine = None
        self.output_window.configure(bg=bg_color)
        self.output_label.configure(text=display_text, bg=bg_color)
        # Only update database if OCR result has changed for the current patient
        if self.latest_patient_name and self.latest_ocr_number is not None and computed_vaccine:
            current_data = (self.latest_ocr_number, computed_vaccine)
            # Check if this patient already has this data recorded
            if self.last_processed.get(self.latest_patient_name) != current_data:
                cursor.execute("SELECT age FROM patient WHERE patient_name = ?", (self.latest_patient_name,))
                row = cursor.fetchone()
                if row:
                    if row[0] != self.latest_ocr_number:
                        cursor.execute("UPDATE patient SET age = ?, vaccine_type = ? WHERE patient_name = ?",
                                       (self.latest_ocr_number, computed_vaccine, self.latest_patient_name))
                        test.commit()
                else:
                    insert_query = '''
                    INSERT INTO patient (age, vaccine_type, patient_name)
                    VALUES (?, ?, ?)
                    '''
                    cursor.execute(insert_query, (self.latest_ocr_number, computed_vaccine, self.latest_patient_name))
                    test.commit()
                self.record_vaccination(self.latest_patient_name, computed_vaccine)
                self.last_processed[self.latest_patient_name] = current_data

    def record_vaccination(self, patient_name, vaccine_type):
        # Records a vaccination if not already recorded for the day
        cursor.execute("SELECT ID FROM patient WHERE patient_name = ?", (patient_name,))
        row = cursor.fetchone()
        if row:
            patient_id = row[0]
            date_administered = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                SELECT COUNT(*) FROM vaccination
                WHERE patient_id = ?
                  AND vaccine_type = ?
                  AND date_administered = ?
            ''', (patient_id, vaccine_type, date_administered))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute('''
                    INSERT INTO vaccination (patient_id, vaccine_type, date_administered)
                    VALUES (?, ?, ?)
                ''', (patient_id, vaccine_type, date_administered))
                test.commit()

    def manual_clear(self):
        if self.output_window and self.output_label:
            self.manual_override = False
            self.manual_bg_color = None
            self.manual_text = None
            self.output_window.configure(bg="#AAAAAA")
            self.output_label.configure(text="Awaiting next input...", bg="#AAAAAA")

    def manual_green(self):
        if self.output_window and self.output_label:
            self.manual_override = True
            self.manual_bg_color = "#00FF00"
            self.manual_text = "Manual: Green"
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(text=self.manual_text, bg=self.manual_bg_color)

    def manual_blue(self):
        if self.output_window and self.output_label:
            self.manual_override = True
            self.manual_bg_color = "#0000FF"
            self.manual_text = "Manual: Blue"
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(text=self.manual_text, bg=self.manual_bg_color)

    def print_database(self):
        # Prints joined patient/vaccination data
        cursor.execute('''
            SELECT p.ID, p.age, p.vaccine_type, p.patient_name,
                   v.vaccine_type, v.date_administered
            FROM patient p
            LEFT JOIN vaccination v ON p.ID = v.patient_id
        ''')
        rows = cursor.fetchall()
        print("Joined Patient/Vaccination Data:")
        print("PatientID | Age | PatientTable_VaccineType | PatientName | VaccinationTable_VaccineType | DateAdministered")
        for row in rows:
            print(row)

    def draw_button(self, rect, text, base_color, hover_color, disabled=False):
        mouse_pos = pygame.mouse.get_pos()
        color = (120, 120, 120) if disabled else (hover_color if rect.collidepoint(mouse_pos) else base_color)
        pygame.draw.rect(self.screen, color, rect)
        txt_surface = self.font.render(text, True, (255, 255, 255))
        txt_rect = txt_surface.get_rect(center=rect.center)
        self.screen.blit(txt_surface, txt_rect)

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.draw_button(self.select_age_button_rect, "Select Age Area", (70, 70, 200), (100, 100, 230))
        self.draw_button(self.select_name_button_rect, "Select Name Area", (70, 70, 200), (100, 100, 230))
        if self.ocr_active:
            self.draw_button(self.ocr_button_rect, "Stop Image OCR", (200, 70, 70), (230, 100, 100))
        else:
            disabled = (self.age_image is None or self.name_image is None)
            self.draw_button(self.ocr_button_rect, "Begin Screen Reading",
                             (70, 200, 70), (100, 230, 100), disabled=disabled)
        spawn_text = "Kill Output Window" if self.output_window else "Spawn Output Window"
        self.draw_button(self.spawn_output_button_rect, spawn_text, (70, 130, 200), (100, 150, 230))
        pygame.draw.rect(self.screen, (50, 50, 50), self.age_preview_area)
        if self.age_image:
            preview_age = letterbox_image(self.age_image, self.age_preview_area.width, self.age_preview_area.height)
            self.screen.blit(preview_age, self.age_preview_area.topleft)
        else:
            placeholder = self.font.render("Age area not selected.", True, (255, 255, 255))
            ph_rect = placeholder.get_rect(center=self.age_preview_area.center)
            self.screen.blit(placeholder, ph_rect)
        pygame.draw.rect(self.screen, (50, 50, 50), self.name_preview_area)
        if self.name_image:
            preview_name = letterbox_image(self.name_image, self.name_preview_area.width, self.name_preview_area.height)
            self.screen.blit(preview_name, self.name_preview_area.topleft)
        else:
            placeholder = self.font.render("Name area not selected.", True, (255, 255, 255))
            ph_rect = placeholder.get_rect(center=self.name_preview_area.center)
            self.screen.blit(placeholder, ph_rect)
        self.draw_button(self.debug_toggle_rect, "Debug", (80, 80, 80), (110, 110, 110))
        if self.debug_mode:
            self.draw_button(self.debug_less_rect, "<65", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_more_rect, ">65", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_drop_table, "Drop", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_print_db_rect, "PrintDB", (80, 80, 80), (110, 110, 110))
        pygame.display.flip()

if __name__ == '__main__':
    app = App()
    app.run()
