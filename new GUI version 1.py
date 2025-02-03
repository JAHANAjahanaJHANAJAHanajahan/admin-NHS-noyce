import pygame
import sys
import pyautogui
from pygame.locals import *
import os
import pytesseract
from PIL import Image
import time
import threading

# Initializing the constructor
pygame.init()

BASE_DIR = os.getcwd()
file_name = os.path.join(BASE_DIR, 'image_success.png')
noimage_file_name = os.path.join(BASE_DIR, 'noimage.png')
pytesseract.pytesseract.tesseract_cmd = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
max_age = 65
smallfont = pygame.font.SysFont('comic sans', 35)
button_font = pygame.font.SysFont('comic sans', 25)
color = (255, 255, 255)
button_text = button_font.render('Select Area', True, color)
start_button_text = button_font.render('Start', True, color)
no_screenshot_text = smallfont.render('No screenshot has been taken yet', True, color)

if os.path.isfile(file_name):
    os.remove(file_name)

# Global variables for screenshot coordinates and running state
screenshot_coords = None
running_ocr = False

def letterbox_image(image, target_width, target_height, background_color=(0, 0, 0)):
    # Get the original dimensions of the image
    original_width, original_height = image.get_size()

    # Calculate the scaling factor to fit the image within the target dimensions
    width_ratio = target_width / original_width
    height_ratio = target_height / original_height
    scale_factor = min(width_ratio, height_ratio)  # Maintain aspect ratio

    # Calculate the new dimensions of the scaled image
    scaled_width = int(original_width * scale_factor)
    scaled_height = int(original_height * scale_factor)

    # Scale the image
    scaled_image = pygame.transform.scale(image, (scaled_width, scaled_height))

    # Create a new surface for the letterboxed image
    letterboxed_surface = pygame.Surface((target_width, target_height))
    letterboxed_surface.fill(background_color)  # Fill with the background color

    # Calculate the position to center the scaled image
    x_offset = (target_width - scaled_width) // 2
    y_offset = (target_height - scaled_height) // 2

    # Blit the scaled image onto the letterboxed surface
    letterboxed_surface.blit(scaled_image, (x_offset, y_offset))

    return letterboxed_surface

def screenshot():
    global screenshot_coords
    if os.path.isfile(file_name):
        os.remove(file_name)
    width, height = pyautogui.size()

    print(width, height)

    running = True
    # Take a new screenshot of the entire screen
    whole_screen_capture = pyautogui.screenshot()
    whole_screen_capture.save(os.path.join(BASE_DIR, 'image_test.png'))

    # Setting the background of the screen as the screenshot
    bg = pygame.image.load(os.path.join(BASE_DIR, 'image_test.png'))

    screen = pygame.display.set_mode((width, height))

    mouseDown, mouseUp = False, False
    screen.blit(bg, (0, 0))

    # Code for actually drawing the box and selecting the area
    while running:
        for event in pygame.event.get():
            # Checking for when the mouse is clicked down and saving the coordinates
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    x_down, y_down = pygame.mouse.get_pos()
                    mouseDown = True

            # Detecting the mouse moving so that the red rectangle only updates when needed
            # Also drawing the actual red rectangle outline
            if event.type == MOUSEMOTION and mouseDown:
                x_current, y_current = pygame.mouse.get_pos()
                screenshot_width = abs(x_current - x_down)
                screenshot_height = abs(y_current - y_down)
                screen.blit(bg, (0, 0))
                # Draw the rectangle from the top-left to bottom-right, regardless of direction
                pygame.draw.rect(
                    screen,
                    (255, 0, 0),
                    (
                        min(x_down, x_current),
                        min(y_down, y_current),
                        screenshot_width,
                        screenshot_height
                    ),
                    2
                )

            # When the mouse button is released, the final screenshot corner coordinates are determined and run through
            # pyautogui to take the screenshot
            if event.type == MOUSEBUTTONUP:
                x_up, y_up = pygame.mouse.get_pos()
                mouseUp = True
                if mouseDown and mouseUp:
                    # Calculate the top-left and bottom-right coordinates
                    x1 = min(x_down, x_up)
                    y1 = min(y_down, y_up)
                    x2 = max(x_down, x_up)
                    y2 = max(y_down, y_up)
                    screenshot_width = x2 - x1
                    screenshot_height = y2 - y1
                    screenshot_coords = (x1, y1, screenshot_width, screenshot_height)
                    newScreenshot = pyautogui.screenshot(region=screenshot_coords)
                    newScreenshot.save(file_name)

        # If the screenshot file now exists then exit out of the while loop
        if os.path.isfile(file_name):
            pygame.quit()
            running = False
        else:
            pygame.display.update()
    menu()

def start_ocr():
    global running_ocr, screenshot_coords
    running_ocr = True
    while running_ocr:
        if screenshot_coords:
            # Take a screenshot of the selected area
            screenshot = pyautogui.screenshot(region=screenshot_coords)
            # Save the screenshot temporarily
            screenshot.save(file_name)
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(Image.open(file_name))
            print("Extracted Text:", text.strip())
        time.sleep(5)  # Wait for 5 seconds before taking the next screenshot

def menu():
    global running_ocr
    # Reinitialize pygame to avoid the "Library not initialized" error
    pygame.init()

    # Screen resolution
    res = (800, 600)

    # Opens up a window
    screen = pygame.display.set_mode(res)
    if os.path.isfile(file_name):
        imp = pygame.image.load(file_name).convert()
    else:
        imp = None

    # Light shade of the button
    color_light = (170, 170, 170)

    # Dark shade of the button
    color_dark = (100, 100, 100)

    # Stores the width and height of the screen
    width = screen.get_width()
    height = screen.get_height()

    # Button dimensions and position
    button_width = 200
    button_height = 50
    button_x = (width - button_width) // 2
    button_y = 20

    # Start button position
    start_button_x = button_x
    start_button_y = button_y + 70

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running_ocr = False
                pygame.quit()
                sys.exit()

            # Checks if a mouse is clicked
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                # If the mouse is clicked on the "Take Screenshot" button
                if button_x <= mouse[0] <= button_x + button_width and button_y <= mouse[1] <= button_y + button_height:
                    pygame.quit()
                    time.sleep(1)
                    screenshot()
                # If the mouse is clicked on the "Start" button
                if start_button_x <= mouse[0] <= start_button_x + button_width and start_button_y <= mouse[1] <= start_button_y + button_height:
                    if screenshot_coords:
                        # Start the OCR thread
                        threading.Thread(target=start_ocr, daemon=True).start()

        # Fills the screen with a color
        screen.fill((60, 25, 60))

        # Draw the "Take Screenshot" button
        mouse = pygame.mouse.get_pos()
        if button_x <= mouse[0] <= button_x + button_width and button_y <= mouse[1] <= button_y + button_height:
            pygame.draw.rect(screen, color_light, [button_x, button_y, button_width, button_height])
        else:
            pygame.draw.rect(screen, color_dark, [button_x, button_y, button_width, button_height])

        # Add text to the "Take Screenshot" button
        screen.blit(button_text, (button_x + 20, button_y + 10))

        # Draw the "Start" button
        if start_button_x <= mouse[0] <= start_button_x + button_width and start_button_y <= mouse[1] <= start_button_y + button_height:
            pygame.draw.rect(screen, color_light, [start_button_x, start_button_y, button_width, button_height])
        else:
            pygame.draw.rect(screen, color_dark, [start_button_x, start_button_y, button_width, button_height])

        # Add text to the "Start" button
        screen.blit(start_button_text, (start_button_x + 70, start_button_y + 10))

        # Draw the screenshot preview area
        preview_x = 50
        preview_y = 200
        preview_width = width - 100
        preview_height = height - 250
        pygame.draw.rect(screen, (255, 255, 255), [preview_x, preview_y, preview_width, preview_height], 2)

        # Add label for the screenshot preview
        preview_label = smallfont.render('Screenshot Preview:', True, color)
        screen.blit(preview_label, (preview_x, preview_y - 40))

        # Display the screenshot or the "no screenshot" text
        if imp:
            imp = letterbox_image(imp, preview_width, preview_height)
            screen.blit(imp, (preview_x, preview_y))
        else:
            no_screenshot_label = smallfont.render('No screenshot has been taken yet', True, color)
            screen.blit(no_screenshot_label, (preview_x + 50, preview_y + (preview_height // 2) - 20))

        # Updates the frames of the game
        pygame.display.update()

menu()