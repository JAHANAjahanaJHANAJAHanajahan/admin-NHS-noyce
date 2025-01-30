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
smallfont = pygame.font.SysFont('comic sans', 35)
color = (255, 255, 255)
text = smallfont.render('please please please', True, color)

if os.path.isfile(file_name):
    os.remove(file_name)

def screenshot():
    if os.path.isfile(file_name):
        os.remove(file_name)
    width, height = pyautogui.size()
    screen = pygame.display.set_mode((width, height))
    running = True
    screenshot_width = 0
    screenshot_height = 0
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
                pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(x_down, y_down, screenshot_width, screenshot_height),2)

            # When the mouse button is released, the final screenshot corner coordinates are determined and run through
            # pyautogui to take the screenshot
            if event.type == MOUSEBUTTONUP:
                x_up, y_up = pygame.mouse.get_pos()
                mouseUp = True
                if mouseDown and mouseUp:
                    #print(x_down, y_down, x_up, y_up)
                    screenshot_width = x_up - x_down
                    screenshot_height = y_up - y_down
                    #print(screenshot_width, screenshot_height)
                    newScreenshot = pyautogui.screenshot(region=(x_down, y_down, screenshot_width, screenshot_height))
                    newScreenshot.save(file_name)

        # If the screenshot file now exists then exit out of the while loop
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
    temp_resolution = imp.get_size()
    print(temp_resolution)

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