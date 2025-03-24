import pygame
import sys
import time
import json
from button import Button

# Initialize Pygame
pygame.init()

# Set up the game window
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Idle Game")

# Initialize resources
resources = 0
click_value = 1
upgrade_cost = 10
auto_upgrade = True
font = pygame.font.Font(None, 36)

# Last update time
last_update = time.time()

# Function to save game state
def save_game():
    with open('savegame.json', 'w') as f:
        json.dump({
            'resources': resources,
            'click_value': click_value,
            'upgrade_cost': upgrade_cost
        }, f)

# Function to load game state
def load_game():
    global resources, click_value, upgrade_cost
    try:
        with open('savegame.json', 'r') as f:
            data = json.load(f)
            resources = data['resources']
            click_value = data['click_value']
            upgrade_cost = data['upgrade_cost']
    except FileNotFoundError:
        pass

# Load game state
load_game()

# Create buttons
generate_button = Button("Generate", (50, 200), font=36, bg="green")
upgrade_button = Button("Upgrade", (50, 250), font=36, bg="blue")

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if generate_button.click(event):
                resources += click_value
            if upgrade_button.click(event) and resources >= upgrade_cost:
                resources -= upgrade_cost
                click_value += 1
                upgrade_cost *= 2  # Increase the cost for the next upgrade

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

    # Render the upgrade cost
    upgrade_text = font.render(f"Upgrade cost: {upgrade_cost}", True, (0, 0, 0))
    screen.blit(upgrade_text, (50, 100))

    # Render the click value
    click_value_text = font.render(f"Click value: {click_value}", True, (0, 0, 0))
    screen.blit(click_value_text, (50, 150))

    # Render the additional information next to the buttons
    generate_info_text = font.render(f"Generates: {click_value}", True, (0, 0, 0))
    screen.blit(generate_info_text, (200, 200))

    upgrade_info_text = font.render(f"Cost: {upgrade_cost}", True, (0, 0, 0))
    screen.blit(upgrade_info_text, (200, 250))

    # Show buttons
    generate_button.show(screen)
    upgrade_button.show(screen)

    # Update the display
    pygame.display.flip()