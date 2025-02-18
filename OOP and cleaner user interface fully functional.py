import pygame
import pyautogui
import sys
import pytesseract
import threading
import time
import tkinter as tk
from PIL import Image, ImageFilter, ImageEnhance

# Initialize pygame
pygame.init()

def letterbox_image(image, target_width, target_height, background_color=(50, 50, 50)):
    """
    Scales the given pygame Surface to fill as much as possible of the target area
    without altering its aspect ratio, then letterboxes the result on a surface of the
    target size.
    """
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
    """
    Handles taking a full-screen screenshot and letting the user select an area.
    """
    def __init__(self):
        self.selected_rect = None

    def select_area(self):
        """
        Displays a full-screen screenshot and allows the user to click & drag to select
        an area. Returns a tuple: (selected_rect, selected_image) where selected_rect
        is (x, y, width, height) and selected_image is a PIL image.
        Returns None if the user quits during selection.
        """
        screen_width, screen_height = pyautogui.size()
        full_screen_pil = pyautogui.screenshot()  # Capture full screen as a PIL image

        # Convert PIL image to a pygame Surface
        mode = full_screen_pil.mode
        size = full_screen_pil.size
        data = full_screen_pil.tobytes()
        background = pygame.image.fromstring(data, size, mode)

        # Create a full-screen window for selection
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
                    # Draw selection rectangle
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

        # Capture the selected region
        selected_image = pyautogui.screenshot(region=self.selected_rect)
        return self.selected_rect, selected_image


class App:
    """
    Main application class that displays the UI, handles area selection,
    toggles OCR on the selected area (with pre-processing), and spawns an
    output window for OCR results. Also includes hidden debug controls.
    """
    def __init__(self):
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Screenshot Selector")
        self.clock = pygame.time.Clock()
        self.running = True

        # Selection data
        self.selected_rect = None
        self.selected_image = None  # pygame Surface for preview

        # OCR state and result
        self.ocr_active = False
        self.latest_ocr_number = None  # Will hold the OCR result if valid

        # Tkinter output window for OCR results
        self.output_window = None  # Tk instance
        self.output_label = None

        # Manual override flag (for the output window)
        self.manual_override = False
        self.manual_bg_color = None
        self.manual_text = None

        # Use a slightly smaller font for the UI
        self.font = pygame.font.SysFont('Arial', 16)

        # Button definitions:
        self.select_button_rect = pygame.Rect(self.width // 2 - 100, 20, 200, 40)
        self.ocr_button_rect = pygame.Rect(self.width // 2 - 100, 70, 200, 40)
        self.spawn_output_button_rect = pygame.Rect(self.width // 2 - 100, 120, 200, 40)
        # Preview area for the selected image
        self.preview_area = pygame.Rect(50, 180, self.width - 100, self.height - 230)
        # Debug toggle button (always visible in top-left)
        self.debug_toggle_rect = pygame.Rect(5, 5, 60, 30)
        self.debug_mode = False
        # Debug buttons (only visible when debug mode is active)
        self.debug_less_rect = pygame.Rect(70, 5, 60, 30)
        self.debug_more_rect = pygame.Rect(135, 5, 60, 30)

    def run(self):
        """
        Main loop.
        """
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(30)  # 30 FPS

            # Update the Tkinter output window if it exists
            if self.output_window:
                try:
                    self.update_output_window()
                    self.output_window.update_idletasks()
                    self.output_window.update()
                except tk.TclError:
                    self.output_window = None
                    self.ocr_active = False

        pygame.quit()
        sys.exit()

    def handle_events(self):
        """
        Processes Pygame events.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # Check Debug toggle button (top-left corner)
                if self.debug_toggle_rect.collidepoint(mouse_pos):
                    self.debug_mode = not self.debug_mode

                # If debug mode is active, check the debug buttons:
                if self.debug_mode:
                    if self.debug_less_rect.collidepoint(mouse_pos):
                        # Set OCR result to a number < 65 (e.g. 50)
                        self.latest_ocr_number = 50
                        print("Debug: Set OCR result to 50 (<65)")
                    if self.debug_more_rect.collidepoint(mouse_pos):
                        # Set OCR result to a number > 65 (e.g. 70)
                        self.latest_ocr_number = 70
                        print("Debug: Set OCR result to 70 (>65)")

                # "Select Area" button click
                if self.select_button_rect.collidepoint(mouse_pos):
                    self.start_selection()

                # "Begin Screen Reading" / "Deactivate" button click
                if self.ocr_button_rect.collidepoint(mouse_pos) and self.selected_image:
                    self.toggle_ocr()

                # "Spawn/Kill Output Window" button click (toggles window)
                if self.spawn_output_button_rect.collidepoint(mouse_pos):
                    if self.output_window:
                        self.on_output_window_close()
                        print("Output window closed.")
                    else:
                        self.spawn_output_window()
                        print("Output window spawned.")

    def start_selection(self):
        """
        Switches to selection mode (using a minimal window during selection)
        and restores the main UI immediately afterward.
        """
        # Switch to a minimal window to hide the main UI briefly
        pygame.display.set_mode((1, 1))
        pygame.time.delay(100)

        selector = ScreenshotSelector()
        result = selector.select_area()
        if result is not None:
            self.selected_rect, selected_pil_image = result
            # Convert the captured image to a pygame Surface (original color)
            selected_pil_image = selected_pil_image.convert("RGB")
            mode = selected_pil_image.mode
            size = selected_pil_image.size
            data = selected_pil_image.tobytes()
            self.selected_image = pygame.image.fromstring(data, size, mode)

        # Restore the main window
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Screenshot Selector")
        self.draw()
        pygame.display.flip()

    def toggle_ocr(self):
        """
        Toggles the OCR loop on or off. If no output window exists, spawn one automatically.
        """
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
        """
        Every 10 seconds, capture the selected area, pre-process it, perform OCR,
        update the preview image, and print the OCR result.
        The pre-processing steps include:
         - Converting to grayscale
         - Upscaling (to enlarge small numbers)
         - Binarizing via thresholding
         - Running OCR with a digit whitelist
        """
        while self.ocr_active:
            if self.selected_rect:
                # Capture the selected region as a PIL image
                screenshot = pyautogui.screenshot(region=self.selected_rect)
                # Preprocess the image:
                # 1. Convert to grayscale
                processed = screenshot.convert("L")
                # 2. Upscale the image by a factor (e.g., 3x)
                width, height = processed.size
                upscale_factor = 3
                processed = processed.resize((width * upscale_factor, height * upscale_factor), resample=Image.Resampling.LANCZOS)
                # 3. Binarize (thresholding): Convert to pure black & white
                threshold = 128
                processed = processed.point(lambda x: 0 if x < threshold else 255, '1')
                # Convert back to grayscale (L) for Tesseract
                processed = processed.convert("L")
                # For preview purposes, convert to RGB
                processed_rgb = processed.convert("RGB")
                mode = processed_rgb.mode
                size = processed_rgb.size
                data = processed_rgb.tobytes()
                self.selected_image = pygame.image.fromstring(data, size, mode)
                # Run OCR with digit-only settings:
                custom_config = "--psm 7 -c tessedit_char_whitelist=0123456789"
                ocr_result = pytesseract.image_to_string(processed, config=custom_config).strip()
                try:
                    number = int(ocr_result)
                    self.latest_ocr_number = number
                    print("OCR result (number):", number)
                except ValueError:
                    self.latest_ocr_number = None
                    print("OCR result invalid or not a number:", ocr_result)
            time.sleep(10)

    def spawn_output_window(self):
        """
        Spawns a new resizable Tkinter window for displaying OCR results.
        """
        if self.output_window:
            return  # Already exists

        self.output_window = tk.Tk()
        self.output_window.title("OCR Output")
        self.output_window.geometry("300x300")
        # Bind close event so OCR stops when the window is closed.
        self.output_window.protocol("WM_DELETE_WINDOW", self.on_output_window_close)

        # Create a label that fills the window
        self.output_label = tk.Label(self.output_window, text="Awaiting next input...", font=("Arial", 18))
        self.output_label.pack(expand=True, fill='both')

        # Create a manual override frame at bottom right for manual overwrite buttons
        self.manual_frame = tk.Frame(self.output_window, bg=self.output_window["bg"])
        self.manual_frame.place(relx=1.0, rely=1.0, anchor='se')
        btn_blue = tk.Button(self.manual_frame, text="Blue", command=self.manual_blue, font=("Arial", 8))
        btn_green = tk.Button(self.manual_frame, text="Green", command=self.manual_green, font=("Arial", 8))
        btn_clear = tk.Button(self.manual_frame, text="Clear", command=self.manual_clear, font=("Arial", 8))
        # Pack buttons so they appear from left to right (Clear, Green, Blue)
        btn_blue.pack(side="right", padx=2)
        btn_green.pack(side="right", padx=2)
        btn_clear.pack(side="right", padx=2)

    def on_output_window_close(self):
        """
        Called when the output window is closed.
        """
        if self.output_window:
            self.output_window.destroy()
        self.output_window = None
        self.ocr_active = False
        print("Output window closed. OCR deactivated.")

    def update_output_window(self):
        """
        Updates the Tkinter window’s background and label based on the latest OCR result
        or manual override.
        """
        if not self.output_window or not self.output_label:
            return

        # If manual override is active, keep its settings
        if self.manual_override:
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(bg=self.manual_bg_color, text=self.manual_text)
            return

        if self.latest_ocr_number is not None:
            # Set background color based on OCR number:
            if self.latest_ocr_number >= 65:
                bg_color = "#0000FF"  # Blue
            else:
                bg_color = "#00FF00"  # Green
            text = str(self.latest_ocr_number)
        else:
            bg_color = "#AAAAAA"  # Neutral gray
            text = "Awaiting next input..."

        self.output_window.configure(bg=bg_color)
        self.output_label.configure(text=text, bg=bg_color)

    def manual_clear(self):
        """
        Clears the manual override so that OCR results update the window again.
        """
        if self.output_window and self.output_label:
            self.manual_override = False
            self.manual_bg_color = None
            self.manual_text = None
            self.output_window.configure(bg="#AAAAAA")
            self.output_label.configure(text="Awaiting next input...", bg="#AAAAAA")

    def manual_green(self):
        """
        Manually sets the output window to green.
        """
        if self.output_window and self.output_label:
            self.manual_override = True
            self.manual_bg_color = "#00FF00"
            self.manual_text = "Manual: Green"
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(text=self.manual_text, bg=self.manual_bg_color)

    def manual_blue(self):
        """
        Manually sets the output window to blue.
        """
        if self.output_window and self.output_label:
            self.manual_override = True
            self.manual_bg_color = "#0000FF"
            self.manual_text = "Manual: Blue"
            self.output_window.configure(bg=self.manual_bg_color)
            self.output_label.configure(text=self.manual_text, bg=self.manual_bg_color)

    def draw_button(self, rect, text, base_color, hover_color, disabled=False):
        """
        Draws a button with a hover effect. If disabled, uses a gray color.
        """
        mouse_pos = pygame.mouse.get_pos()
        color = (120, 120, 120) if disabled else (hover_color if rect.collidepoint(mouse_pos) else base_color)
        pygame.draw.rect(self.screen, color, rect)
        txt_surface = self.font.render(text, True, (255, 255, 255))
        txt_rect = txt_surface.get_rect(center=rect.center)
        self.screen.blit(txt_surface, txt_rect)

    def draw(self):
        """
        Draws the main UI (buttons and preview area).
        """
        self.screen.fill((30, 30, 30))

        # Draw main buttons:
        self.draw_button(self.select_button_rect, "Select Area", (70, 70, 200), (100, 100, 230))
        # Use red shades when OCR is active (i.e. "Deactivate" state)
        if self.ocr_active:
            self.draw_button(self.ocr_button_rect, "Deactivate", (200, 70, 70), (230, 100, 100))
        else:
            self.draw_button(self.ocr_button_rect, "Begin Screen Reading", (70, 200, 70), (100, 230, 100), disabled=(self.selected_image is None))
        
        # Toggle button for spawning or killing the output window
        if self.output_window:
            spawn_text = "Kill Output Window"
        else:
            spawn_text = "Spawn Output Window"
        self.draw_button(self.spawn_output_button_rect, spawn_text, (70, 130, 200), (100, 150, 230))

        # Draw preview area:
        pygame.draw.rect(self.screen, (50, 50, 50), self.preview_area)
        if self.selected_image:
            preview = letterbox_image(self.selected_image, self.preview_area.width, self.preview_area.height)
            self.screen.blit(preview, self.preview_area.topleft)
        else:
            placeholder = self.font.render("Area not selected yet.", True, (255, 255, 255))
            ph_rect = placeholder.get_rect(center=self.preview_area.center)
            self.screen.blit(placeholder, ph_rect)

        # Draw debug toggle button (always visible)
        self.draw_button(self.debug_toggle_rect, "Debug", (80, 80, 80), (110, 110, 110))
        # If in debug mode, draw additional debug buttons
        if self.debug_mode:
            self.draw_button(self.debug_less_rect, "<65", (80, 80, 80), (110, 110, 110))
            self.draw_button(self.debug_more_rect, ">65", (80, 80, 80), (110, 110, 110))

        pygame.display.flip()


if __name__ == '__main__':
    app = App()
    app.run()
