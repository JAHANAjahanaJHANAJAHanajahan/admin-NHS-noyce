import pygame
import sys
import pyautogui
from pygame.locals import *
import os
import pytesseract
from PIL import Image, ImageFilter
import time

# initializing the constructor
pygame.init()
from pygame.transform import threshold

BASE_DIR = os.getcwd()
file_name = os.path.join(BASE_DIR, 'image success.png')
noimage_file_name = os.path.join(BASE_DIR, 'noimage.png')
pytesseract.pytesseract.tesseract_cmd = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
max_age = 65
smallfont = pygame.font.SysFont('impact', 25)
color = (255, 255, 255)
text = smallfont.render('Screenshot', True, color)

if os.path.isfile(file_name):
    os.remove(file_name)

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
    time.sleep(1)
    whole_screen_capture = pyautogui.screenshot()
    whole_screen_capture.save(os.path.join(BASE_DIR, 'image_test.png'))

    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)

    bg = pygame.image.load(os.path.join(BASE_DIR, 'image_test.png')).convert()

    mouseDown, mouseUp = False, False
    screen.blit(bg, (0, 0))

    while running:
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    x_down, y_down = pygame.mouse.get_pos()
                    mouseDown = True

            if event.type == MOUSEMOTION and mouseDown:
                x_current, y_current = pygame.mouse.get_pos()
                screenshot_width = abs(x_current - x_down)
                screenshot_height = abs(y_current - y_down)
                screen.blit(bg, (0, 0))

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

            if event.type == MOUSEBUTTONUP:
                x_up, y_up = pygame.mouse.get_pos()
                mouseUp = True
                if mouseDown and mouseUp:

                    x1 = min(x_down, x_up)
                    y1 = min(y_down, y_up)
                    x2 = max(x_down, x_up)
                    y2 = max(y_down, y_up)
                    screenshot_width = x2 - x1
                    screenshot_height = y2 - y1
                    screenshot_coords = (x1, y1, screenshot_width, screenshot_height)
                    newScreenshot = pyautogui.screenshot(region=screenshot_coords)
                    newScreenshot.save(file_name)

        if os.path.isfile(file_name):
            pygame.quit()
            running = False
        else:
            pygame.display.update()
    menu()

def menu():
        # screen resolution
    res = (800, 600)

    # opens up a window
    screen = pygame.display.set_mode(res)
    if os.path.isfile(file_name):
        imp = pygame.image.load(file_name).convert()
    else:
        imp = pygame.image.load(noimage_file_name).convert()
    imp = letterbox_image(imp, res[0], res[1])
    imp = pygame.transform.scale(imp, res)



    # light shade of the button
    color_light = (170, 170, 170)

    # dark shade of the button
    color_dark = (100, 100, 100)

    # stores the width of the
    # screen into a variable
    width = screen.get_width()

    # stores the height of the
    # screen into a variable
    height = screen.get_height()


    while True:

        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()

                # checks if a mouse is clicked
            if ev.type == pygame.MOUSEBUTTONDOWN:

                # if the mouse is clicked on the
                # button the game is terminated
                if width / 2 <= mouse[0] <= width / 2 + 140 and height / 2 <= mouse[1] <= height / 2 + 40:
                    pygame.quit()
                    time.sleep(1)
                    screenshot()

                    # fills the screen with a color
        screen.fill((60, 25, 60))
        screen.blit(imp, (0, 0))
        # stores the (x,y) coordinates into
        # the variable as a tuple
        mouse = pygame.mouse.get_pos()

        # if mouse is hovered on a button it
        # changes to lighter shade
        if width / 2 <= mouse[0] <= width / 2 + 140 and height / 2 <= mouse[1] <= height / 2 + 40:
            pygame.draw.rect(screen, color_light, [width / 2, height / 2, 140, 40])

        else:
            pygame.draw.rect(screen, color_dark, [width / 2, height / 2, 140, 40])

            # superimposing the text onto our button
        screen.blit(text, (width / 2 + 50, height / 2))

        # updates the frames of the game
        pygame.display.update()

menu()