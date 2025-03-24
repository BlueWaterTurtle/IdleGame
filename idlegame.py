import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Set up the game window
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Idle Game")

# Initialize resources
resources = 0
font = pygame.font.Font(None, 36)

# Last update time
last_update = time.time()

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Increment resources over time
    current_time = time.time()
    if current_time - last_update >= 1:  # Increment every second
        resources += 1
        last_update = current_time

    # Fill the screen with a color (e.g., white)
    screen.fill((255, 255, 255))

    # Render the resource counter
    resource_text = font.render(f"Resources: {resources}", True, (0, 0, 0))
    screen.blit(resource_text, (50, 50))

    # Update the display
    pygame.display.flip()
