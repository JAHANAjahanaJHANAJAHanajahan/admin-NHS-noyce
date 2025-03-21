import pygame
import sys

# Initialize pygame
pygame.init()

# Set window dimensions and create a window
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Button & Image Prototype")

# Load an image (update the path to an actual image file on your system)
try:
    image = pygame.image.load("sample_image.png")
except pygame.error:
    # If image loading fails, create a placeholder surface
    image = pygame.Surface((200, 150))
    image.fill((150, 150, 150))
    pygame.draw.line(image, (0, 0, 0), (0, 0), (200, 150), 3)
    pygame.draw.line(image, (0, 0, 0), (0, 150), (200, 0), 3)

# Define button properties
button_rect = pygame.Rect(350, 500, 100, 50)
button_color = (70, 130, 180)
button_hover_color = (100, 160, 210)
button_text_color = (255, 255, 255)
font = pygame.font.SysFont("Arial", 24)


def draw_button(surface, rect, text, color):
    """Draws a button with text."""
    pygame.draw.rect(surface, color, rect)
    text_surface = font.render(text, True, button_text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)


# Variable to track button click state
button_clicked = False

clock = pygame.time.Clock()
running = True

while running:
    screen.fill((30, 30, 30))

    # Display the image at a fixed position
    screen.blit(image, (100, 100))

    # Determine button color based on hover state
    mouse_pos = pygame.mouse.get_pos()
    if button_rect.collidepoint(mouse_pos):
        current_color = button_hover_color
    else:
        current_color = button_color

    # Draw the button
    draw_button(screen, button_rect, "Click Me", current_color)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Check for mouse click on the button
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if button_rect.collidepoint(event.pos):
                button_clicked = not button_clicked
                print("Button clicked!")

    # Display a message on the screen if the button was clicked
    if button_clicked:
        message = font.render("Button was clicked!", True, (255, 255, 255))
        screen.blit(message, (300, 400))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

