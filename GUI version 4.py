import pygame
import sys
import pyautogui
from pygame.locals import *
import os
import pytesseract
from PIL import Image, ImageFilter
import time
import threading

# Initializing the constructor
pygame.init()

BASE_DIR = os.getcwd()
file_name = os.path.join(BASE_DIR, 'image_success.png')
noimage_file_name = os.path.join(BASE_DIR, 'noimage.png')
pytesseract.pytesseract.tesseract_cmd = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
max_age = 65
smallfont = pygame.font.SysFont('impact', 25)
color = (255, 255, 255)
text = smallfont.render('Screenshot', True, color)

if os.path.isfile(file_name):
    os.remove(file_name)

# Global variables
screenshot_coords = None
ocr_running = False

def letterbox_image(image, target_width, target_height, background_color=(0, 0, 0)):
    original_width, original_height = image.get_size()
    width_ratio = target_width / original_width
    height_ratio = target_height / original_height
    scale_factor = min(width_ratio, height_ratio)
    scaled_width = int(original_width * scale_factor)
    scaled_height = int(original_height * scale_factor)
    scaled_image = pygame.transform.scale(image, (scaled_width, scaled_height))
    letterboxed_surface = pygame.Surface((target_width, target_height))
    letterboxed_surface.fill(background_color)
    x_offset = (target_width - scaled_width) // 2
    y_offset = (target_height - scaled_height) // 2
    letterboxed_surface.blit(scaled_image, (x_offset, y_offset))
    return letterboxed_surface

def perform_ocr():
    global ocr_running
    while ocr_running:
        if screenshot_coords:
            newScreenshot = pyautogui.screenshot(region=screenshot_coords)
            text = pytesseract.image_to_string(newScreenshot)
            print("Extracted Text:", text)
        time.sleep(5)

def start_ocr():
    global ocr_running
    if not ocr_running:
        ocr_running = True
        threading.Thread(target=perform_ocr).start()

def stop_ocr():
    global ocr_running
    ocr_running = False

def menu():

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if width / 2 - 70 <= mouse[0] <= width / 2 + 70 and 20 <= mouse[1] <= 60:
                    #screenpygame.display.set_mode(flags=pygame.HIDDEN)
                    time.sleep(1)

                    if os.path.isfile(file_name):
                        os.remove(file_name)
                    width, height = pyautogui.size()
                    running = True
                    time.sleep(1)
                    whole_screen_capture = pyautogui.screenshot()
                    whole_screen_capture.save(os.path.join(BASE_DIR, 'image_test.png'))
                    screenshot_screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
                    bg = pygame.image.load(os.path.join(BASE_DIR, 'image_test.png')).convert()
                    mouseDown, mouseUp = False, False
                    screenshot_screen.blit(bg, (0, 0))

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
                                    screenshot_screen,
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
                            pygame.display.quit()
                            running = False
                        else:
                            pygame.display.update()

                elif width / 2 - 70 <= mouse[0] <= width / 2 + 70 and 80 <= mouse[1] <= 120:
                    start_ocr()
                elif width / 2 - 70 <= mouse[0] <= width / 2 + 70 and 140 <= mouse[1] <= 180:
                    stop_ocr()

        res = (800, 600)
        screen = pygame.display.set_mode(res)
        if os.path.isfile(file_name):
            imp = pygame.image.load(file_name).convert()
        else:
            imp = None

        color_light = (170, 170, 170)
        color_dark = (100, 100, 100)
        width = screen.get_width()
        height = screen.get_height()

        screen.fill((60, 25, 60))

        if imp:
            imp = letterbox_image(imp, res[0], res[1])
            imp = pygame.transform.scale(imp, res)
            screen.blit(imp, (0, 100))
        else:
            no_screenshot_text = smallfont.render('No screenshot taken yet', True, color)
            screen.blit(no_screenshot_text, (width / 2 - 100, height / 2))

        mouse = pygame.mouse.get_pos()
        buttons = [("Take Screenshot", width / 2 - 70, 20, 200, 40),("Start Image OCR", width / 2 - 70, 80, 200, 40),("Stop Image OCR", width / 2 - 70, 140, 200, 40)]

        for text, x, y, w, h in buttons:
            if x <= mouse[0] <= x + w and y <= mouse[1] <= y + h:
                pygame.draw.rect(screen, color_light, [x, y, w, h])
            else:
                pygame.draw.rect(screen, color_dark, [x, y, w, h])
            screen.blit(smallfont.render(text, True, color), (x + 10, y + 10))

        pygame.display.update()

menu()