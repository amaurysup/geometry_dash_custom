import pygame


class Player:
    """Simple player rectangle with gravity and jump."""

    def __init__(self, x: int, y: int, w: int = 40, h: int = 40):
        self.rect = pygame.Rect(x, y, w, h)
        self.vel_y = 0.0
        self.on_ground = False
        self.alive = True
        self.coyote_time = 0.0  # time in air before losing ability to jump
        self.jump_buffer = 0.0  # buffer time for jump input
        self.last_jump_time = 0.0  # prevent multiple jumps per keypress

    def update(self, dt: float, gravity: float):
        # apply gravity
        self.vel_y += gravity * dt
        self.rect.y += int(self.vel_y * dt)
        
        # Update coyote time (grace period after leaving ground)
        if self.on_ground:
            self.coyote_time = 0.1  # 100ms grace period
        else:
            self.coyote_time = max(0, self.coyote_time - dt)
            
        # Update jump buffer
        self.jump_buffer = max(0, self.jump_buffer - dt)
        self.last_jump_time = max(0, self.last_jump_time - dt)

    def jump(self, strength: float):
        # More responsive jump with coyote time and jump buffer
        if self.alive and self.last_jump_time <= 0:
            # Can jump if on ground OR within coyote time
            if self.on_ground or self.coyote_time > 0:
                self.vel_y = -strength
                self.on_ground = False
                self.coyote_time = 0  # consume coyote time
                self.last_jump_time = 0.1  # prevent multiple jumps for 100ms
            else:
                # Store jump input for a short time (jump buffer)
                self.jump_buffer = 0.1

    def draw(self, surface: pygame.Surface, player_image=None):
        if player_image:
            # Scale image to player size
            scaled_img = pygame.transform.scale(player_image, (self.rect.width, self.rect.height))
            surface.blit(scaled_img, (self.rect.x, self.rect.y))
        else:
            # Fallback: colored rectangle
            pygame.draw.rect(surface, (255, 100, 100), self.rect)
