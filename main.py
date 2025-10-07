"""Entry point with simple level selection menu."""
import os
import json
import pygame
from game.engine import Game


def list_levels(folder="data/levels"):
    files = []
    for entry in os.listdir(folder):
        if entry.endswith('.json'):
            path = os.path.join(folder, entry)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                title = data.get('title', entry)
            except Exception:
                title = entry
            files.append((title, path))
    files.sort()
    return files


def menu():
    pygame.init()
    screen = pygame.display.set_mode((800, 450))
    font = pygame.font.Font(None, 36)
    levels = list_levels()
    if not levels:
        screen.fill((30, 30, 40))
        t = font.render('No levels found in data/levels', True, (240, 240, 240))
        screen.blit(t, (20, 20))
        pygame.display.flip()
        pygame.time.wait(2000)
        return

    idx = 0
    running = True
    clock = pygame.time.Clock()
    while running:
        dt = clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    idx = min(idx + 1, len(levels) - 1)
                elif event.key == pygame.K_UP:
                    idx = max(idx - 1, 0)
                elif event.key == pygame.K_RETURN:
                    # launch level
                    title, path = levels[idx]
                    g = Game(width=800, height=450, title=f"Geometry Dash - {title}")
                    g.run(level_path=path)
                    # re-create menu display surface in case the level altered/quit the display
                    try:
                        pygame.display.quit()
                        pygame.display.init()
                    except Exception:
                        pass
                    screen = pygame.display.set_mode((800, 450))
                    # return to menu after level ends
        # draw menu
        screen.fill((20, 20, 30))
        header = font.render('Select level', True, (220, 220, 220))
        screen.blit(header, (20, 20))
        for i, (title, path) in enumerate(levels):
            color = (255, 255, 120) if i == idx else (200, 200, 200)
            txt = font.render(title, True, color)
            screen.blit(txt, (40, 80 + i * 44))
        pygame.display.flip()


if __name__ == '__main__':
    menu()
