import pygame

class Button:
    def __init__(self, text, pos, font, bg="black"):
        self.x, self.y = pos
        self.font = pygame.font.Font(None, font)
        self.bg = bg
        self.text = text
        self.change_text(text, bg)

    def change_text(self, text, bg="black"):
        """Change the text"""
        self.text_surf = self.font.render(text, True, pygame.Color("white"))
        self.size = self.text_surf.get_size()
        self.surface = pygame.Surface(self.size)
        self.surface.fill(bg)
        self.surface.blit(self.text_surf, (0, 0))
        self.rect = pygame.Rect(self.x, self.y, self.size[0], self.size[1])

    def show(self, screen):
        screen.blit(self.surface, (self.x, self.y))

    def click(self, event):
        x, y = pygame.mouse.get_pos()
        if self.rect.collidepoint(x, y):
            return True
        return False