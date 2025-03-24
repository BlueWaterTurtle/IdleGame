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
click_value = 1
upgrade_cost = 10
font = pygame.font.Font(None, 36)

# Last update time
last_update = time.time()

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            resources += click_value

    # Increment resources over time
    current_time = time.time()
    if current_time - last_update >= 1:  # Increment every second
        resources += 1
        last_update = current_time

    # Check for upgrades
    if resources >= upgrade_cost:
        resources -= upgrade_cost
        click_value += 1
        upgrade_cost *= 2  # Increase the cost for the next upgrade

    # Fill the screen with a color (e.g., white)
    screen.fill((255, 255, 255))

    # Render the resource counter
    resource_text = font.render(f"Resources: {resources}", True, (0, 0, 0))
    screen.blit(resource_text, (50, 50))

    # Render the upgrade cost
    upgrade_text = font.render(f"Upgrade cost: {upgrade_cost}", True, (0, 0, 0))
    screen.blit(upgrade_text, (50, 100))

    # Render the click value
    click_value_text = font.render(f"Click value: {click_value}", True, (0, 0, 0))
    screen.blit(click_value_text, (50, 150))

    # Update the display
    pygame.display.flip()