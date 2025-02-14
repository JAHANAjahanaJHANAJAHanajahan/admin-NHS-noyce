import pygame
import sys
import pyautogui
from pygame.locals import *
import os
import pytesseract
from PIL import Image, ImageFilter
import time
import threading

pygame.init()

BASE_DIR = os.getcwd()
file_name = os.path.join(BASE_DIR, 'image_success.png')
noimage_file_name = os.path.join(BASE_DIR, 'noimage.png')
smallfont = pygame.font.SysFont('impact', 25)

if os.path.isfile(file_name):
    os.remove(file_name)

class Menu:
    def __init__(self):
        self.menu_window_resolution = (800, 600)
        self.menu_screen_background_colour = (60, 25, 60)
        self.button_colour = (175, 175, 175)
        self.button_colour_hover = (100, 100, 100)
        self.menu_screen = None
        self.mouseDown = False
        self.mouseUp = False
        self.x_down, self.y_down = 0, 0
        self.x_up, self.y_up = 0, 0
        self.screenshot_screen = None
        self.bg = None

    def create_menu_screen(self):
        self.menu_screen = pygame.display.set_mode(self.menu_window_resolution)
        self.menu_screen.fill(self.menu_screen_background_colour)
        pygame.display.update()

    def dragging_rectangle(self, event):
        if event.type == MOUSEMOTION and self.mouseDown:
            x_current, y_current = pygame.mouse.get_pos()
            screenshot_width = abs(x_current - self.x_down)
            screenshot_height = abs(y_current - self.y_down)
            self.menu_screen.blit(self.bg, (0, 0))
            pygame.draw.rect(
                self.screenshot_screen,
                (255, 0, 0),(min(self.x_down, x_current), min(self.y_down, y_current), screenshot_width, screenshot_height),2)

    def handle_mouse_button_down(self, event):
        if event.button == 1:
            self.x_down, self.y_down = pygame.mouse.get_pos()
            self.mouseDown = True

    def handle_mouse_button_up(self, event):
        self.x_up, self.y_up = pygame.mouse.get_pos()
        self.mouseUp = True
        if self.mouseDown and self.mouseUp:
            x1 = min(self.x_down, self.x_up)
            y1 = min(self.y_down, self.y_up)
            x2 = max(self.x_down, self.x_up)
            y2 = max(self.y_down, self.y_up)
            screenshot_width = x2 - x1
            screenshot_height = y2 - y1
            screenshot_coords = (x1, y1, screenshot_width, screenshot_height)
            newScreenshot = pyautogui.screenshot(region=screenshot_coords)
            newScreenshot.save(file_name)

    def take_screenshot(self):
        if os.path.isfile(file_name):
            os.remove(file_name)
        width, height = pyautogui.size()
        time.sleep(1)
        whole_screen_capture = pyautogui.screenshot()
        whole_screen_capture.save(os.path.join(BASE_DIR, 'image_test.png'))
        self.screenshot_screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        self.bg = pygame.image.load(os.path.join(BASE_DIR, 'image_test.png')).convert()
        self.mouseDown, self.mouseUp = False, False
        self.screenshot_screen.blit(self.bg, (0, 0))


    def start_ocr(self):
        # Implement OCR functionality here
        pass

    def stop_ocr(self):
        # Implement stop OCR functionality here
        pass

    def screenshot_event_loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse = pygame.mouse.get_pos()
                    if self.menu_window_resolution[0] / 2 - 70 <= mouse[0] <= self.menu_window_resolution[0] / 2 + 70 and 20 <= mouse[1] <= 60:
                        self.take_screenshot()
                        running = True
                        while running:
                            for event in pygame.event.get():
                                if event.type == MOUSEBUTTONDOWN:
                                    self.handle_mouse_button_down(event)
                                self.dragging_rectangle(event)
                                if event.type == MOUSEBUTTONUP:
                                    self.handle_mouse_button_up(event)
                                    if os.path.isfile(file_name):
                                        pygame.display.quit()
                                        running = False
                                    else:
                                        pygame.display.update()
                    elif self.menu_window_resolution[0] / 2 - 70 <= mouse[0] <= self.menu_window_resolution[0] / 2 + 70 and 80 <= mouse[1] <= 120:
                        self.start_ocr()
                    elif self.menu_window_resolution[0] / 2 - 70 <= mouse[0] <= self.menu_window_resolution[0] / 2 + 70 and 140 <= mouse[1] <= 180:
                        self.stop_ocr()

    def menu_buttons(self):
        pass


menu = Menu()
menu.create_menu_screen()
menu.screenshot_event_loop()