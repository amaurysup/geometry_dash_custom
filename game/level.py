import json
from typing import List, Dict, Any


class Obstacle:
    def __init__(self, x: int, y: int, w: int, h: int, obstacle_type: str = "normal"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = obstacle_type  # "normal", "platform", "spike"

    def rect(self):
        import pygame
        return pygame.Rect(self.x, self.y, self.w, self.h)
    
    def is_deadly(self) -> bool:
        """Retourne True si l'obstacle tue instantanément"""
        return self.type == "spike"
    
    def is_platform(self) -> bool:
        """Retourne True si c'est une plateforme sur laquelle on peut atterrir"""
        return self.type in ["normal", "platform"]


class Level:
    """Represents a side-scrolling level loaded from JSON."""

    def __init__(self, width: int, height: int, obstacles: List[Obstacle], scroll_speed: float):
        self.width = width
        self.height = height
        self.obstacles = obstacles
        self.scroll_speed = scroll_speed
        self.bg_layers: List[Dict[str, Any]] = []
        self.duration = None  # seconds, if None level runs until obstacles exhausted
        self.spawn_timeline: List[Dict[str, Any]] = []  # list of timed spawn events
        self.music_file: str | None = None

    @staticmethod
    def load_from_file(path: str) -> 'Level':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        w = data.get('width', 800)
        h = data.get('height', 450)
        speed = data.get('scroll_speed', 200)
        obs = []
        for o in data.get('obstacles', []):
            # Support pour le nouveau format avec types d'obstacles
            obstacle_type = o.get('type', 'normal')  # Par défaut : obstacle normal
            obs.append(Obstacle(o['x'], o['y'], o['w'], o['h'], obstacle_type))

        lvl = Level(w, h, obs, speed)
        # backgrounds: list of layers {image: optional, color: [r,g,b], speed_factor: float}
        lvl.bg_layers = data.get('bg_layers', [])
        lvl.duration = data.get('duration')
        # spawn_timeline: list of {time: seconds, w: , h:, y: }
        lvl.spawn_timeline = data.get('spawn_timeline', [])
        lvl.music_file = data.get('music')
        return lvl
