import pygame
import sys

button_size = 300, 50

pygame.init()
i = 0



clock = pygame.time.Clock()

window_size = (500,500)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Jahan's Button Test")

font = pygame.font.Font(None, 24)

button_surface = pygame.Surface(button_size)

text = font.render("Click me please please PLEASE JusT CLICK ME SEMOBODY CLICK ME", True, (0,0,0))
text_rect = text.get_rect(center=(button_surface.get_width() / 2, button_surface.get_height() / 2))

# Create a pygame.Rect object that represents the button's boundaries
button_rect = pygame.Rect(10, 10, *button_size)  # Adjust the position as needed

# Start the main loop
while True:
    # Set the frame rate
    clock.tick(60)

    # Fill the display with color
    screen.fill((255, 255, 255))

    # Get events from the event queue
    for event in pygame.event.get():
        # Check for the quit event
        if event.type == pygame.QUIT:
            # Quit the game
            pygame.quit()
            sys.exit()

        # Check for the mouse button down event
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Call the on_mouse_button_down() function
            if button_rect.collidepoint(event.pos):
                print (i)
                i += 1

    # Check if the mouse is over the button. This will create the button hover effect
    if button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(button_surface, (22, 184, 124), (1, 1, 148, 48))
    else:
        pygame.draw.rect(button_surface, (0, 0, 0), (0, 0, *button_size))
        pygame.draw.rect(button_surface, (255, 255, 255), (1, 1, 148, 48))
        pygame.draw.rect(button_surface, (0, 0, 0), (1, 1, 148, 1), 2)
        pygame.draw.rect(button_surface, (0, 100, 0), (1, 48, 148, 10), 2)

    # Shwo the button text
    button_surface.blit(text, text_rect)

    # Draw the button on the screen
    screen.blit(button_surface, (button_rect.x, button_rect.y))

    # Update the game state
    pygame.display.update()