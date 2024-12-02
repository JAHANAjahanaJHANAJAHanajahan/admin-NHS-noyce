import pyautogui
import pygame
from pygame.locals import *
import os
import pytesseract
from PIL import Image, ImageFilter
import time
import tkinter as tk

from pygame.transform import threshold

# TODO Improve your use of comments

# Global variables
BASE_DIR = os.getcwd()
file_name = os.path.join(BASE_DIR, 'image success.png')
pytesseract.pytesseract.tesseract_cmd = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
width, height = pyautogui.size()
screen = pygame.display.set_mode((width, height))
running = True
max_age = 65
screenshot_width = 0
screenshot_height = 0

# Removing the picture file if it is already there
if os.path.isfile(file_name):
    os.remove(file_name)

# Take a new screenshot of the entire screen
whole_screen_capture = pyautogui.screenshot()
whole_screen_capture.save(os.path.join(BASE_DIR, 'image test.png'))

# Setting the background of the screen as the screenshot
bg = pygame.image.load(os.path.join(BASE_DIR, 'image test.png'))

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
                selection_box = pygame.Rect(x_down, y_down, 15, 15)

        # Detecting the mouse moving so that the red rectangle only updates when needed
        # Also drawing the actual red rectangle outline
        if event.type == MOUSEMOTION and mouseDown:
            screenshot_width = pygame.mouse.get_pos()[0] - x_down
            screenshot_height = pygame.mouse.get_pos()[1] - y_down
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(x_down, y_down, screenshot_width, screenshot_height), 2)

        # When the mouse button is released, the final screenshot corner coordinates are determined and run through
        # pyautogui to take the screenshot
        if event.type == MOUSEBUTTONUP:
            x_up, y_up = pygame.mouse.get_pos()
            mouseUp = True
            if mouseDown and mouseUp:
                print (x_down, y_down, x_up, y_up)
                screenshot_width = x_up - x_down
                screenshot_height = y_up - y_down
                print (screenshot_width, screenshot_height)
                newScreenshot = pyautogui.screenshot(region=(x_down, y_down, screenshot_width, screenshot_height))
                newScreenshot.save(file_name)

    # If the screenshot file now exists then exit out of the while loop
    if os.path.isfile(file_name):
        pygame.quit()
        running = False
    else:
        pygame.display.update()

root = tk.Tk()
root.geometry("300x300")

while True:
    transcribed = pytesseract.image_to_string(Image.open(file_name))
    print(transcribed)  # misha put sigma here
    try:
        print (int(transcribed))
        if int(transcribed) > max_age:
            print("blue")
            #root.configure(bg="blue")
        else:
            print("green")
            #root.configure(bg="green")
    except:
        print("nuh uh")

    os.remove(file_name)
    newScreenshot = pyautogui.screenshot(region=(x_down, y_down, screenshot_width, screenshot_height))
    newScreenshot = newScreenshot.convert("L")
    threshold = 200
    #newScreenshot = newScreenshot.filter(ImageFilter.GaussianBlur(radius=1))
    newScreenshot = newScreenshot.point(lambda x: 0 if x < threshold else 255, '1')
    newScreenshot.save(file_name)
    time.sleep(5)

root.mainloop()