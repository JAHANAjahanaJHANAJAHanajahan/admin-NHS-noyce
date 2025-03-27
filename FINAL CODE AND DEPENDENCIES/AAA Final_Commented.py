import os                                   # Provides functions for interacting with the operating system
import pygame                               # Library for creating graphical applications and handling input/output
import pyautogui                            # Library for taking screenshots
import sys                                  # Provides system-specific functions and parameters
import pytesseract                          # Python wrapper for the Google Tesseract OCR engine
import threading                            # Allows running separate threads for concurrent execution
import time                                 # Provides time-related functions like sleep
import tkinter as tk                        # GUI library for creating additional windows
from PIL import Image                       # Library for image processing and manipulation
import sqlite3                              # SQLite database library for data storage and retrieval
from datetime import datetime               # Used to work with dates and times
import hashlib                              # Provides hashing functions (I used sha256)

# Initializing pygame and configuring the Tesseract executable path
pygame.init()
pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), r"Tesseract-OCR/tesseract.exe")

# Connecting to or creating if non-existent an SQLite database named 'NHS Database.sqlite'
test = sqlite3.connect('../NHS Database.sqlite')
cursor = test.cursor()
cursor.execute("PRAGMA foreign_keys = ON")  # Enabling support for foreign key constraints in SQLite

# Creating the 'patient' table if it does not exist. Includes a data_hash column for data integrity checks
cursor.execute('''
CREATE TABLE IF NOT EXISTS patient (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    age REAL,
    vaccine_type TEXT,
    patient_name TEXT,
    data_hash TEXT
)
''')
# Creating the 'vaccination' table if it does not exist. Establishing a foreign key relationship with the patient table
cursor.execute('''
CREATE TABLE IF NOT EXISTS vaccination (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    vaccine_type TEXT,
    date_administered TEXT,
    FOREIGN KEY (patient_id) REFERENCES patient(ID)
)
''')
test.commit()  # Commiting changes to the database

# Function to compute an sha256 hash for a record for data integrity purposes
def compute_record_hash(age, patient_name, vaccine_type):
    # Concatenates the key patient data into a single string
    record_str = f"{age}-{patient_name}-{vaccine_type}"
    # Returns the sha256 hash of the concatenated string
    return hashlib.sha256(record_str.encode('utf-8')).hexdigest()

# Function to letterbox images. Scales and centers an image within a target area while preserving its aspect ratio
# and adding paddingwhen nescessary
def letterbox_image(image, target_width, target_height, background_color=(50, 50, 50)):
    orig_width, orig_height = image.get_size()  # Get original dimensions of the image
    scale = min(target_width / orig_width, target_height / orig_height)  # Compute scale factor
    new_width = int(orig_width * scale)         # Calculate new width after scaling
    new_height = int(orig_height * scale)       # Calculate new height after scaling
    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))  # Smoothly scale the image
    letterboxed_surface = pygame.Surface((target_width, target_height))  # Create a new surface with target dimensions
    letterboxed_surface.fill(background_color)  # Fill the surface with a background color for padding and "black bars" effect
    x_offset = (target_width - new_width) // 2  # Calculate horizontal offset to center the image
    y_offset = (target_height - new_height) // 2  # Calculate vertical offset to center the image
    letterboxed_surface.blit(scaled_image, (x_offset, y_offset))  # Blit the scaled image onto the letterboxed surface
    return letterboxed_surface

# Base class for OCR processors. Contains common image processing methods for OCR.
class BaseOCRProcessor:
    def process_image(self, screenshot):
        # Converts screenshot to grayscale
        image = screenshot.convert("L")
        width, height = image.size
        upscale_factor = 3
        # Factor to enlarge the image for improved OCR accuracy. I chose three because it felt like a good middle ground.
        # Resize the image using high-quality Lanczos resampling
        image = image.resize((width * upscale_factor, height * upscale_factor), resample=Image.Resampling.LANCZOS)
        threshold = 128  # Defining the threshold for converting to binary image
        # Applying the thresholding which sets pixels below threshold to black and others to white
        image = image.point(lambda x: 0 if x < threshold else 255, '1')
        return image

# Derived OCR processor for reading the integer age data
class AgeOCRProcessor(BaseOCRProcessor):
    def process_ocr(self, screenshot):
        processed_image = self.process_image(screenshot)  # Preprocess the image using the base class method above
        custom_config = "--psm 7 -c tessedit_char_whitelist=0123456789"  # Tesseract config which ensures it only detects digits
        ocr_result = pytesseract.image_to_string(processed_image, config=custom_config).strip()  # Perform the image OCR
        try:
            return int(ocr_result)  # Trys to convert the OCR result to an integer
        except ValueError:
            return None  # Return None if the conversion fails

# Derived OCR processor for reading general text for the patient names
class NameOCRProcessor(BaseOCRProcessor):
    def process_ocr(self, screenshot):
        processed_image = self.process_image(screenshot)  # Preprocess image using common method again
        ocr_result = pytesseract.image_to_string(processed_image).strip()
        # Perform OCR with default configuration so characters can be recognized too
        return ocr_result  # Return the extracted text

# Class to enable user to select a screen region interactively with a screenshot like interface
class ScreenshotSelector:
    # Allows user to define a region on the screen via mouse dragging
    def __init__(self):
        self.selected_rect = None  # Initializes the variable to store the selected rectangle

    def select_area(self):
        screen_width, screen_height = pyautogui.size()  # Get full screen dimensions
        full_screen_pil = pyautogui.screenshot()          # Capture a full-screen screenshot which is a PIL image
        mode = full_screen_pil.mode                       # Get image mode
        size = full_screen_pil.size                       # Get image size
        data = full_screen_pil.tobytes()                  # Get raw image data
        background = pygame.image.fromstring(data, size, mode)  # Create a pygame surface from the screenshot
        # Creates a fullscreen pygame window to allow the user to select with mouse
        full_screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        full_screen.blit(background, (0, 0))  # Displays the screenshot as background
        pygame.display.flip()
        selecting = True
        start_pos = None  # Variable that stores the starting mouse position
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None  # Exits if the window is closed
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    start_pos = event.pos  # Records the starting position on mouse down which is left mouse button
                if event.type == pygame.MOUSEMOTION and start_pos:
                    current_pos = event.pos  # This is the current mouse position during drag
                    full_screen.blit(background, (0, 0))  # Redraws the background
                    x = min(start_pos[0], current_pos[0])  # Determines rectangle x coordinate
                    y = min(start_pos[1], current_pos[1])  # Determines rectangle y coordinate
                    width = abs(current_pos[0] - start_pos[0])  # Determines rectangle width
                    height = abs(current_pos[1] - start_pos[1])  # Determines rectangle height
                    rect = pygame.Rect(x, y, width, height)
                    pygame.draw.rect(full_screen, (255, 0, 0), rect, 2)  # Draws a red rectangle for selection
                    pygame.display.flip()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and start_pos:
                    end_pos = event.pos  # Gets the ending mouse position on release of the left mouse button
                    x1 = min(start_pos[0], end_pos[0])
                    y1 = min(start_pos[1], end_pos[1])
                    x2 = max(start_pos[0], end_pos[0])
                    y2 = max(start_pos[1], end_pos[1])
                    self.selected_rect = (x1, y1, x2 - x1, y2 - y1)  # Stores the selected region dimensions
                    selecting = False  # Ends the selection loop
                    break
        selected_image = pyautogui.screenshot(region=self.selected_rect)  # Captures the selected screen region
        return self.selected_rect, selected_image  # Returns the region and its image

# Main application class that integrates the GUI, OCR processing, and database interactions all together
class App:
    # Initializes the main application window and variables
    def __init__(self):
        self.width = 1150                     # Width of the pygame window
        self.height = 400                     # Height of the pygame window
        self.screen = pygame.display.set_mode((self.width, self.height)) # Setting the resolution of the screen
        pygame.display.set_caption("Screenshot Selector") # The name of the pygame window
        self.clock = pygame.time.Clock()      # Clock to manage frame rate
        self.running = True                   # Flag to keep the main loop running

        self.age_rect = None                  # Coordinates for the age area selection
        self.age_image = None                 # Pygame image for the age preview
        self.name_rect = None                 # Coordinates for the name area selection
        self.name_image = None                # Pygame image for the name preview

        self.ocr_active = False               # Flag to control OCR processing
        self.latest_ocr_number = None         # Stores the latest OCR result for age
        self.latest_patient_name = None       # Stores the latest OCR result for name

        self.database_comment = None          # Temporary placeholder for any database-related comment

        self.output_window = None             # Tkinter window for OCR output
        self.output_label = None              # Label widget in the OCR output window

        self.manual_override = False          # Flag to determine if manual override is active
        self.manual_bg_color = None           # Background color for manual override
        self.manual_text = None               # Text to display in manual override mode

        self.font = pygame.font.SysFont('Arial', 16)  # Font for rendering text in pygame which is never changed

        # Defining the buttons with their positions and dimensions
        self.select_age_button_rect = pygame.Rect(50, 20, 200, 40)
        self.select_name_button_rect = pygame.Rect(300, 20, 200, 40)
        self.ocr_button_rect = pygame.Rect(550, 20, 200, 40)
        self.spawn_output_button_rect = pygame.Rect(800, 20, 200, 40)

        # Defining the preview areas for displaying selected images
        self.age_preview_area = pygame.Rect(50, 80, 500, 250)
        self.name_preview_area = pygame.Rect(600, 80, 500, 250)

        # Defining the debug buttons and toggle
        self.debug_toggle_rect = pygame.Rect(5, self.height - 35, 60, 30)
        self.debug_mode = False               # A flag for debug mode activation
        self.debug_less_rect = pygame.Rect(70, self.height - 35, 60, 30)
        self.debug_more_rect = pygame.Rect(135, self.height - 35, 60, 30)
        self.debug_drop_table = pygame.Rect(200, self.height - 35, 60, 30)
        self.debug_print_db_rect = pygame.Rect(265, self.height - 35, 60, 30)

        # A dictionary to track processed data per patient to avoid duplicate database operations
        self.last_processed = {}

        # Instantiating the OCR processor objects for age and name
        self.age_processor = AgeOCRProcessor()
        self.name_processor = NameOCRProcessor()

    # Main loop which handles events, updates the display, and manages the Tkinter window if it is currently open
    def run(self):
        while self.running:
            self.handle_events()   # Processes user and system events
            self.draw()            # Redraws the pygame window
            if self.output_window:
                try:
                    self.update_output_window()  # Updates the OCR output if available
                    self.output_window.update_idletasks()  # Processes any pending Tkinter tasks
                    self.output_window.update()  # Refreshes the Tkinter window
                except tk.TclError:
                    self.output_window = None  # Handles any window closure errors
                    self.ocr_active = False
            self.clock.tick(30)  # Limits loop to 30 frames per second
        pygame.quit()            # Cleans up pygame resources
        sys.exit()               # Exits the program

    # Handles all pygame events like mouse clicks, window closing, etc...
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False  # Ends the main loop if window is closed
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()  # Gets the current mouse position
                # Toggles debug mode if debug toggle button is clicked in the bottom left of the menu window
                if self.debug_toggle_rect.collidepoint(mouse_pos):
                    self.debug_mode = not self.debug_mode
                if self.debug_mode:
                    # Manually sets OCR result to 50 for testing (<65)
                    if self.debug_less_rect.collidepoint(mouse_pos):
                        self.latest_ocr_number = 50
                        print("Debug: Set OCR result to 50 (<65)")
                    # Manually sets OCR result to 70 for testing (>65)
                    if self.debug_more_rect.collidepoint(mouse_pos):
                        self.latest_ocr_number = 70
                        print("Debug: Set OCR result to 70 (>65)")
                    # Drops and recreates tables in the database for testing or if you want to erase everything
                    if self.debug_drop_table.collidepoint(mouse_pos):
                        cursor.execute('DROP TABLE IF EXISTS vaccination')
                        cursor.execute('DROP TABLE IF EXISTS patient')
                        print("Debug: Dropped patient and vaccination tables.")
                        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS patient (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            age REAL,
                            vaccine_type TEXT,
                            patient_name TEXT,
                            data_hash TEXT
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
                    # Prints all database contents to the console for easy viewing
                    if self.debug_print_db_rect.collidepoint(mouse_pos):
                        self.print_database()
                # Starts the age selection process if the corresponding button is clicked
                if self.select_age_button_rect.collidepoint(mouse_pos):
                    self.start_age_selection()
                # Starts the name selection process if the corresponding button is clicked
                if self.select_name_button_rect.collidepoint(mouse_pos):
                    self.start_name_selection()
                # Toggles the OCR processing if both age and name images are available
                if self.ocr_button_rect.collidepoint(mouse_pos) and self.age_image and self.name_image:
                    self.toggle_ocr()
                # Spawns or closes the output window when its button is clicked
                if self.spawn_output_button_rect.collidepoint(mouse_pos):
                    if self.output_window:
                        self.on_output_window_close()  # Closes the window if it's already open
                        print("Output window closed.")
                    else:
                        self.spawn_output_window()      # Opens the window if it isn't already open
                        print("Output window spawned.")

    # Initiates selection of the age region using the ScreenshotSelector
    def start_age_selection(self):
        pygame.display.set_mode((1, 1))  # Switches to a minimal display for a full screen capture
        pygame.time.delay(100)           # A short delay to ensure the display update
        selector = ScreenshotSelector()  # Creates a new instance of ScreenshotSelector
        result = selector.select_area()  # Lets the user select a region
        if result is not None:
            self.age_rect, selected_pil_image = result  # Stores the selected region and image
            selected_pil_image = selected_pil_image.convert("RGB")
            # Converts the image to RGB to ensure that pygame accepts it without error
            mode = selected_pil_image.mode
            size = selected_pil_image.size
            data = selected_pil_image.tobytes()
            self.age_image = pygame.image.fromstring(data, size, mode)  # Creates a pygame image from PIL data
        self.screen = pygame.display.set_mode((self.width, self.height))  # Restores the main display
        pygame.display.set_caption("Screenshot Selector")
        self.draw()                   # Redraws the interface
        pygame.display.flip()         # Updates the display

    # Initiates selection of the patient name region using the ScreenshotSelector
    def start_name_selection(self):
        pygame.display.set_mode((1, 1))  # Switches to minimal display for a full screen capture
        pygame.time.delay(100)           # Short delay for stability
        selector = ScreenshotSelector()  # Creates a new ScreenshotSelector instance
        result = selector.select_area()  # Lets the user select the region
        if result is not None:
            self.name_rect, selected_pil_image = result  # Store selected region and image
            selected_pil_image = selected_pil_image.convert("RGB")
            # Convert image to RGB to ensure that pygame accepts it without error
            mode = selected_pil_image.mode
            size = selected_pil_image.size
            data = selected_pil_image.tobytes()
            self.name_image = pygame.image.fromstring(data, size, mode)  # Creates pygame image from data
        self.screen = pygame.display.set_mode((self.width, self.height))  # Restores main display
        pygame.display.set_caption("Screenshot Selector")
        self.draw()                   # Redraws the interface
        pygame.display.flip()         # Updates display

    # Toggles the OCR process on or off
    def toggle_ocr(self):
        if not self.output_window:
            self.spawn_output_window()  # Ensures the output window exists for OCR results
        if self.ocr_active:
            self.ocr_active = False     # Deactivates the image OCR if it's already active
            print("OCR deactivated.")
        else:
            self.ocr_active = True      # Activates OCR
            print("OCR activated.")
            threading.Thread(target=self.ocr_loop, daemon=True).start()  # Starts OCR processing in a new thread

    # Continuous loop for OCR processing which runs in a separate thread
    def ocr_loop(self):
        while self.ocr_active:
            if self.age_rect and self.name_rect:
                # Captures and processes the age region
                screenshot_age = pyautogui.screenshot(region=self.age_rect)
                processed_age = self.age_processor.process_image(screenshot_age)
                processed_age_rgb = processed_age.convert("RGB")  # Converts the processed image for display
                self.age_image = pygame.image.fromstring(processed_age_rgb.tobytes(), processed_age_rgb.size, processed_age_rgb.mode)
                age = self.age_processor.process_ocr(screenshot_age)  # Extracts any numeric age via OCR
                # Captures and processes the name region
                screenshot_name = pyautogui.screenshot(region=self.name_rect)
                processed_name = self.name_processor.process_image(screenshot_name)
                processed_name_rgb = processed_name.convert("RGB")  # Converts the processed image for display
                self.name_image = pygame.image.fromstring(processed_name_rgb.tobytes(), processed_name_rgb.size, processed_name_rgb.mode)
                name = self.name_processor.process_ocr(screenshot_name)  # Extracts patient name text via OCR
                # Updates OCR results only if both age and name are valid
                if age is not None and name:
                    self.latest_ocr_number = age
                    self.latest_patient_name = name
                    print("OCR age result (number):", self.latest_ocr_number)
                    print("OCR name result:", self.latest_patient_name)
            time.sleep(5)  # Pauses for 5 seconds before next OCR cycle to not put too much of a load onto the users system

    # Spawns a Tkinter window to actually display the OCR output
    def spawn_output_window(self):
        if self.output_window:
            return  # Doesn't create a new window if one already exists
        self.output_window = tk.Tk()
        self.output_window.title("OCR Output")
        self.output_window.geometry("300x300")
        self.output_window.protocol("WM_DELETE_WINDOW", self.on_output_window_close)  # Handles any window close events
        self.output_label = tk.Label(self.output_window, text="Awaiting next input...", font=("Arial", 18))
        self.output_label.pack(expand=True, fill='both')
        # Creates a manual override frame with buttons for color overrides
        self.manual_frame = tk.Frame(self.output_window, bg=self.output_window["bg"])
        self.manual_frame.place(relx=1.0, rely=1.0, anchor='se')
        btn_blue = tk.Button(self.manual_frame, text="Blue", command=self.manual_blue, font=("Arial", 8))
        btn_green = tk.Button(self.manual_frame, text="Green", command=self.manual_green, font=("Arial", 8))
        btn_clear = tk.Button(self.manual_frame, text="Clear", command=self.manual_clear, font=("Arial", 8))
        btn_blue.pack(side="right", padx=2)
        btn_green.pack(side="right", padx=2)
        btn_clear.pack(side="right", padx=2)

    # Handles the closing of the OCR output window while deactivating OCR processing as well
    def on_output_window_close(self):
        if self.output_window:
            self.output_window.destroy()  # Destroys the Tkinter window
        self.output_window = None
        self.ocr_active = False  # Deactivates OCR since the output window is closed
        print("Output window closed. OCR deactivated.")

    # Updates the OCR output window with the latest OCR results or manual override settings
    def update_output_window(self):
        if not self.output_window or not self.output_label:
            return
        # If the manual override is active, display manual settings
        if self.manual_override:
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(bg=self.manual_bg_color, text=self.manual_text)
            return
        # Sets display parameters based on OCR results if available
        if self.latest_ocr_number is not None and self.latest_patient_name is not None:
            if self.latest_ocr_number >= 65:
                bg_color = "#0000FF"  # Blue for ages 65 and above
                computed_vaccine = "Blue"
            else:
                bg_color = "#00FF00"  # Green for ages below 65
                computed_vaccine = "Green"
            display_text = f"Age: {self.latest_ocr_number}  Name: {self.latest_patient_name}"
        else:
            bg_color = "#AAAAAA"  # Default background if there is no OCR result
            display_text = "Awaiting next input..."
            computed_vaccine = None
        self.output_window.configure(bg=bg_color)
        self.output_label.configure(text=display_text, bg=bg_color)
        # If a valid OCR data is present, it updates the database accordingly
        if self.latest_patient_name and self.latest_ocr_number is not None and computed_vaccine:
            current_hash = compute_record_hash(self.latest_ocr_number, self.latest_patient_name, computed_vaccine)
            # Compute hash for integrity
            current_data = (self.latest_ocr_number, computed_vaccine)
            # Updates the database only if the current data is different from the last processed data to avoid duplicates
            if self.last_processed.get(self.latest_patient_name) != current_data:
                cursor.execute("SELECT age, data_hash FROM patient WHERE patient_name = ?", (self.latest_patient_name,))
                row = cursor.fetchone()
                if row:
                    stored_age, stored_hash = row
                    # Updates the record if the age or hash does not match the current data
                    if stored_age != self.latest_ocr_number or stored_hash != current_hash:
                        cursor.execute("UPDATE patient SET age = ?, vaccine_type = ?, data_hash = ? WHERE patient_name = ?",
                                       (self.latest_ocr_number, computed_vaccine, current_hash, self.latest_patient_name))
                        test.commit()
                else:
                    # Inserts a new record if the patient is not found in the database
                    insert_query = '''
                    INSERT INTO patient (age, vaccine_type, patient_name, data_hash)
                    VALUES (?, ?, ?, ?)
                    '''
                    cursor.execute(insert_query, (self.latest_ocr_number, computed_vaccine, self.latest_patient_name, current_hash))
                    test.commit()
                self.record_vaccination(self.latest_patient_name, computed_vaccine)  # Record the vaccination event
                self.last_processed[self.latest_patient_name] = current_data  # Update the last processed record

    # Records a vaccination event in the database for the specified patient and vaccine type, if it's not already recorded for today
    def record_vaccination(self, patient_name, vaccine_type):
        cursor.execute("SELECT ID FROM patient WHERE patient_name = ?", (patient_name,))
        row = cursor.fetchone()
        if row:
            patient_id = row[0]
            date_administered = datetime.now().strftime("%Y-%m-%d")  # Get current date in YYYY-MM-DD format
            # Checks if a vaccination record exists for this patient, vaccine, and date
            cursor.execute('''
                SELECT COUNT(*) FROM vaccination
                WHERE patient_id = ?
                  AND vaccine_type = ?
                  AND date_administered = ?
            ''', (patient_id, vaccine_type, date_administered))
            count = cursor.fetchone()[0]
            if count == 0:
                # Inserts a new vaccination record if none exists for today
                cursor.execute('''
                    INSERT INTO vaccination (patient_id, vaccine_type, date_administered)
                    VALUES (?, ?, ?)
                ''', (patient_id, vaccine_type, date_administered))
                test.commit()

    # Manual override function to clear any manual settings and reset the output window
    def manual_clear(self):
        if self.output_window and self.output_label:
            self.manual_override = False
            self.manual_bg_color = None
            self.manual_text = None
            self.output_window.configure(bg="#AAAAAA")
            self.output_label.configure(text="Awaiting next input...", bg="#AAAAAA")

    # Manual override function to set the output window to green with a manual message
    def manual_green(self):
        if self.output_window and self.output_label:
            self.manual_override = True
            self.manual_bg_color = "#00FF00"
            self.manual_text = "Manual: Green"
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(text=self.manual_text, bg=self.manual_bg_color)

    # Manual override function to set the output window to blue with a manual message
    def manual_blue(self):
        if self.output_window and self.output_label:
            self.manual_override = True
            self.manual_bg_color = "#0000FF"
            self.manual_text = "Manual: Blue"
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(text=self.manual_text, bg=self.manual_bg_color)

    # Prints the contents of the joined patient and vaccination tables to the console for debugging and/or viewing
    def print_database(self):
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

    # A function to draw a button on the pygame window which supports hover and disabled states
    def draw_button(self, rect, text, base_color, hover_color, disabled=False):
        mouse_pos = pygame.mouse.get_pos()
        color = (120, 120, 120) if disabled else (hover_color if rect.collidepoint(mouse_pos) else base_color)
        pygame.draw.rect(self.screen, color, rect)
        txt_surface = self.font.render(text, True, (255, 255, 255))
        txt_rect = txt_surface.get_rect(center=rect.center)
        self.screen.blit(txt_surface, txt_rect)

    # Redraws the entire pygame window, including buttons and preview areas
    def draw(self):
        self.screen.fill((30, 30, 30))  # Fills the background with a dark gray color for a clean look
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
        # Draws the preview area for the age image
        pygame.draw.rect(self.screen, (50, 50, 50), self.age_preview_area)
        if self.age_image:
            preview_age = letterbox_image(self.age_image, self.age_preview_area.width, self.age_preview_area.height)
            self.screen.blit(preview_age, self.age_preview_area.topleft)
        else:
            placeholder = self.font.render("Age area not selected.", True, (255, 255, 255))
            ph_rect = placeholder.get_rect(center=self.age_preview_area.center)
            self.screen.blit(placeholder, ph_rect)
        # Draws the preview area for the name image
        pygame.draw.rect(self.screen, (50, 50, 50), self.name_preview_area)
        if self.name_image:
            preview_name = letterbox_image(self.name_image, self.name_preview_area.width, self.name_preview_area.height)
            self.screen.blit(preview_name, self.name_preview_area.topleft)
        else:
            placeholder = self.font.render("Name area not selected.", True, (255, 255, 255))
            ph_rect = placeholder.get_rect(center=self.name_preview_area.center)
            self.screen.blit(placeholder, ph_rect)
        # Draws the debug buttons if debug mode is enabled
        self.draw_button(self.debug_toggle_rect, "Debug", (80, 80, 80), (110, 110, 110))
        if self.debug_mode:
            self.draw_button(self.debug_less_rect, "<65", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_more_rect, ">65", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_drop_table, "Drop", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_print_db_rect, "PrintDB", (80, 80, 80), (110, 110, 110))
        pygame.display.flip()  # Update the display

# This creates an instance of App and runs the main loop which essentially starts the whole program
if __name__ == '__main__':
    app = App()
    app.run()

