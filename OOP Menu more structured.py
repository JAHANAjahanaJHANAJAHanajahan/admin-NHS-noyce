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
        self.window_resolution = (800, 600)
        self.menu_screen_background_colour = (60, 25, 60)
        self.button_colour = (100, 100, 100)
        self.button_colour = (175, 175, 175)

    def create_menu_screen(self):
        menu_screen = pygame.display.set_mode(self.window_resolution)
        menu_screen.fill(self.menu_screen_background_colour)

        pygame.display.update()

menu = Menu()
menu.create_menu_screen()