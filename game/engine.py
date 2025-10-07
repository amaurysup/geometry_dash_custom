import pygame
import sys
from .player import Player
from .level import Level, Obstacle
import os
import json
import random
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available - GIF animation disabled")


class Game:
    def __init__(self, width=800, height=450, title="Geometry Dash"):
        pygame.init()
        # Initialize mixer with specific parameters for better MP3 compatibility
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.bg_color = (30, 30, 40)

        # physics
        self.gravity = 2400.0  # px/s^2 (increased for snappier feel)
        self.jump_strength = 700.0  # compensated jump velocity for new gravity

        # player
        self.player = Player(100, height - 80)

        # level
        self.level = None
        self.scroll_x = 0.0

        # Combo vidéo system
        self.combo_triggered = False
        self.combo_active = False
        self.combo_start_time = 0
        self.combo_duration = 4.0  # 4 secondes (plus de temps pour réagir)
        self.combo_letters = []
        self.combo_input = []
        self.combo_success = False

        self.font = pygame.font.Font(None, 28)
        self.combo_font = pygame.font.Font(None, 72)  # Plus gros pour le combo
        self.game_over_font = pygame.font.Font(None, 96)  # Pour "GAME OVER"
        self.assets_path = os.path.join(os.path.dirname(__file__), '..', 'assets')
        self.loaded_bg_images = []
        self.loaded_obstacle_images = []
        self.loaded_fixed_bg_images = []
        self.player_image = None
        
        # Game Over assets
        self.game_over_image = None
        self.game_over_sound = None
        self.game_over_sound_played = False
        
        # QTE sound assets
        self.qte_sound = None
        self.qte_sound_played = False
        self.music_paused_for_qte = False

    def load_level(self, path: str):
        self.level = Level.load_from_file(path)
        # clamp obstacle heights so they are potentially reachable by player
        max_jump_px = (self.jump_strength ** 2) / (2 * self.gravity)  # h = v^2 / (2g)
        ground_y = self.height - 40
        for o in self.level.obstacles:
            # ensure obstacle top is not higher than max_jump_px above ground
            obstacle_top = o.y
            # if the obstacle is a high ceiling (y < ground_y - max_jump_px - player height)
            min_allowed_y = ground_y - max_jump_px - self.player.rect.height
            if o.y < min_allowed_y:
                o.y = int(min_allowed_y)
        # try to load bg images if present
        self.loaded_bg_images = []
        for idx, layer in enumerate(self.level.bg_layers):
            img_name = layer.get('image')
            loaded = None
            if img_name:
                candidate = os.path.join(self.assets_path, img_name)
                if os.path.exists(candidate):
                    try:
                        loaded = pygame.image.load(candidate).convert_alpha()
                    except Exception:
                        loaded = None
            # If no specific image, try to load sequential background images
            elif not img_name:
                # Try bg1.png, bg2.png, etc.
                for i in range(1, 10):  # Try up to 9 background images
                    bg_file = f"bg{i}.png"
                    candidate = os.path.join(self.assets_path, bg_file)
                    if os.path.exists(candidate):
                        try:
                            loaded = pygame.image.load(candidate).convert_alpha()
                            break  # Use first found image for this layer
                        except Exception:
                            continue
            self.loaded_bg_images.append(loaded)

        # try to load obstacle images
        self.loaded_obstacle_images = []
        for i in range(1, 10):  # Try obstacle1.png, obstacle2.png, etc.
            obs_file = f"obstacle{i}.png"
            candidate = os.path.join(self.assets_path, obs_file)
            if os.path.exists(candidate):
                try:
                    img = pygame.image.load(candidate).convert_alpha()
                    self.loaded_obstacle_images.append(img)
                except Exception:
                    continue

        # try to load sequential background images for fixed backgrounds
        self.loaded_fixed_bg_images = []
        self.scaled_bg_images = []  # Images redimensionnées pour même hauteur
        
        for i in range(1, 20):  # Try background1.png, background2.png, etc.
            bg_file = f"background{i}.png"
            candidate = os.path.join(self.assets_path, bg_file)
            if os.path.exists(candidate):
                try:
                    img = pygame.image.load(candidate).convert_alpha()
                    self.loaded_fixed_bg_images.append(img)
                    print(f"Background chargé: {bg_file} - Taille: {img.get_size()}")
                except Exception as e:
                    print(f"Erreur chargement {bg_file}: {e}")
                    continue
        
        # Redimensionner tous les backgrounds à la même hauteur (hauteur de l'écran)
        if self.loaded_fixed_bg_images:
            for img in self.loaded_fixed_bg_images:
                # Calculer la largeur proportionnelle pour garder le ratio
                original_w, original_h = img.get_size()
                target_h = self.height
                target_w = int((original_w / original_h) * target_h)
                scaled_img = pygame.transform.scale(img, (target_w, target_h))
                self.scaled_bg_images.append(scaled_img)
            print(f"Backgrounds chargés et redimensionnés: {len(self.scaled_bg_images)} images")

        # try to load player image
        self.player_image = None
        player_file = "player.png"
        candidate = os.path.join(self.assets_path, player_file)
        if os.path.exists(candidate):
            try:
                self.player_image = pygame.image.load(candidate).convert_alpha()
            except Exception:
                self.player_image = None

        # try to load combo GIF/image with animation support
        self.combo_frames = []
        self.combo_frame_duration = 100  # ms entre frames
        self.combo_current_frame = 0
        self.combo_last_frame_time = 0
        
        combo_files = ["combo.gif", "combo.png", "combo.jpg"]
        for combo_file in combo_files:
            candidate = os.path.join(self.assets_path, combo_file)
            if os.path.exists(candidate):
                try:
                    if combo_file.endswith('.gif') and PIL_AVAILABLE:
                        # Charger GIF animé avec PIL
                        pil_image = Image.open(candidate)
                        frames = []
                        try:
                            while True:
                                # Convertir chaque frame PIL en surface Pygame
                                frame = pil_image.convert('RGBA')
                                mode = frame.mode
                                size = frame.size
                                data = frame.tobytes()
                                
                                pygame_surface = pygame.image.fromstring(data, size, mode)
                                frames.append(pygame_surface.convert_alpha())
                                
                                pil_image.seek(pil_image.tell() + 1)
                        except EOFError:
                            pass  # Fin du GIF
                        
                        if frames:
                            self.combo_frames = frames
                            print(f"GIF animé chargé: {combo_file} ({len(frames)} frames)")
                        else:
                            # Fallback: charger comme image statique
                            static_img = pygame.image.load(candidate).convert_alpha()
                            self.combo_frames = [static_img]
                            print(f"GIF chargé comme image statique: {combo_file}")
                    else:
                        # Image statique
                        static_img = pygame.image.load(candidate).convert_alpha()
                        self.combo_frames = [static_img]
                        print(f"Image combo chargée: {combo_file}")
                    break
                except Exception as e:
                    print(f"Erreur chargement {combo_file}: {e}")
                    continue

        # music - démarrage immédiat
        if getattr(self.level, 'music_file', None):
            music_path = os.path.join(self.assets_path, self.level.music_file)
            if os.path.exists(music_path):
                try:
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(0.5)  # Volume réduit
                    pygame.mixer.music.play(-1)  # -1 = loop infinitely
                    print(f"🎵 Musique lancée avec succès!")
                except pygame.error as e:
                    print(f"⚠️ Format non supporté: {e}")
                    print("💡 Conseil: Convertis en WAV 16-bit PCM ou MP3 standard")
                except Exception as e:
                    print(f"❌ Erreur musique: {e}")
            else:
                print(f"❌ Fichier introuvable: {music_path}")

    def generate_combo(self):
        """Génère un combo aléatoire de 2 lettres"""
        import random
        letters = ['Q', 'W', 'E', 'R', 'A', 'S', 'D', 'F']
        self.combo_letters = random.sample(letters, 2)
        self.combo_input = []
        
    def handle_combo_input(self, key):
        """Gère l'input du combo - les 2 touches doivent être pressées simultanément"""
        if not self.combo_active:
            return
            
        # Conversion des touches pygame vers lettres
        key_to_letter = {
            pygame.K_q: 'Q', pygame.K_w: 'W', pygame.K_e: 'E', pygame.K_r: 'R',
            pygame.K_a: 'A', pygame.K_s: 'S', pygame.K_d: 'D', pygame.K_f: 'F'
        }
        
        if key in key_to_letter:
            letter = key_to_letter[key]
            if letter not in self.combo_input:
                self.combo_input.append(letter)
                print(f"Touche pressée: {letter}, Total: {self.combo_input}")
    
    def check_combo_simultaneous(self):
        """Vérifie si les touches sont pressées simultanément"""
        if not self.combo_active:
            return
            
        # Vérifier si toutes les touches du combo sont actuellement pressées
        keys = pygame.key.get_pressed()
        key_map = {
            'Q': pygame.K_q, 'W': pygame.K_w, 'E': pygame.K_e, 'R': pygame.K_r,
            'A': pygame.K_a, 'S': pygame.K_s, 'D': pygame.K_d, 'F': pygame.K_f
        }
        
        combo_keys_pressed = True
        for letter in self.combo_letters:
            if not keys[key_map[letter]]:
                combo_keys_pressed = False
                break
        
        if combo_keys_pressed:
            # Toutes les bonnes touches sont pressées simultanément
            self.combo_success = True
            self.combo_active = False
            
            # Relancer la musique si elle était en pause pour le QTE
            if self.music_paused_for_qte:
                try:
                    pygame.mixer.music.unpause()  # Relancer la musique
                    self.music_paused_for_qte = False
                    print("🎵 Musique relancée après QTE réussi")
                except Exception as e:
                    print(f"Erreur lors de la reprise musique: {e}")
            
            print("COMBO RÉUSSI - Touches simultanées détectées!")

    def draw_combo_screen(self, elapsed_time):
        """Dessine l'écran de combo en haut à gauche sans couvrir tout l'écran"""
        # Zone du combo en haut à gauche (400x250 pixels)
        combo_width = 400
        combo_height = 250
        
        # Fond semi-transparent pour la zone combo
        combo_surface = pygame.Surface((combo_width, combo_height))
        combo_surface.set_alpha(220)
        combo_surface.fill((20, 20, 40))
        
        # Bordure
        pygame.draw.rect(combo_surface, (255, 255, 255), (0, 0, combo_width, combo_height), 3)
        
        # Afficher le GIF/image combo animé si disponible
        y_offset = 10
        if self.combo_frames:
            # Gestion de l'animation
            current_time = pygame.time.get_ticks()
            if current_time - self.combo_last_frame_time > self.combo_frame_duration:
                self.combo_current_frame = (self.combo_current_frame + 1) % len(self.combo_frames)
                self.combo_last_frame_time = current_time
            
            # Afficher la frame actuelle
            current_frame = self.combo_frames[self.combo_current_frame]
            gif_width = min(150, combo_width - 20)
            gif_height = min(80, combo_height // 3)
            scaled_gif = pygame.transform.scale(current_frame, (gif_width, gif_height))
            gif_x = (combo_width - gif_width) // 2
            combo_surface.blit(scaled_gif, (gif_x, y_offset))
            y_offset += gif_height + 10
        
        # Titre compact
        title_font = pygame.font.Font(None, 36)
        title_text = title_font.render("COMBO!", True, (255, 255, 255))
        title_x = (combo_width - title_text.get_width()) // 2
        combo_surface.blit(title_text, (title_x, y_offset))
        y_offset += 40
        
        # Lettres à presser (simultanément)
        combo_str = " + ".join(self.combo_letters)
        combo_font = pygame.font.Font(None, 32)
        combo_text = combo_font.render(combo_str, True, (255, 255, 0))
        combo_x = (combo_width - combo_text.get_width()) // 2
        combo_surface.blit(combo_text, (combo_x, y_offset))
        y_offset += 35
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instruction_text = instruction_font.render("Pressez EN MÊME TEMPS!", True, (255, 100, 100))
        instruction_x = (combo_width - instruction_text.get_width()) // 2
        combo_surface.blit(instruction_text, (instruction_x, y_offset))
        y_offset += 25
        
        # Input actuel
        if self.combo_input:
            input_str = " + ".join(self.combo_input)
            input_text = instruction_font.render(f"Pressé: {input_str}", True, (150, 150, 150))
            input_x = (combo_width - input_text.get_width()) // 2
            combo_surface.blit(input_text, (input_x, y_offset))
            y_offset += 25
        
        # Timer
        remaining = self.combo_duration - elapsed_time
        timer_text = instruction_font.render(f"Temps: {remaining:.1f}s", True, (255, 100, 100))
        timer_x = (combo_width - timer_text.get_width()) // 2
        combo_surface.blit(timer_text, (timer_x, y_offset))
        
        # Dessiner la zone combo en haut à gauche
        self.screen.blit(combo_surface, (10, 10))

    def draw_grid(self):
        """Dessine un quadrillage pour aider à la construction du niveau"""
        # Taille des cellules de la grille (40x40 pixels)
        grid_size = 40
        
        # Couleur de la grille (gris très léger, presque transparent)
        grid_color = (80, 80, 80, 50)
        
        # Dessiner les lignes verticales
        for x in range(0, self.width + grid_size, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height), 1)
        
        # Dessiner les lignes horizontales  
        for y in range(0, self.height + grid_size, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y), 1)
        
        # Marquer les coordonnées importantes
        ground_y = self.height - 40
        
        # Ligne du sol plus visible
        pygame.draw.line(self.screen, (120, 120, 120), (0, ground_y), (self.width, ground_y), 2)
        
        # Afficher quelques coordonnées importantes
        coord_font = pygame.font.Font(None, 20)
        
        # Niveau 0 (sol)
        level0_text = coord_font.render("Niveau 0 (Sol)", True, (150, 150, 150))
        self.screen.blit(level0_text, (5, ground_y - 15))
        
        # Niveau 1 (étage supérieur)
        level1_y = ground_y - 160  # Environ 4 cellules plus haut
        pygame.draw.line(self.screen, (100, 150, 100), (0, level1_y), (self.width, level1_y), 1)
        level1_text = coord_font.render("Niveau 1", True, (100, 150, 100))
        self.screen.blit(level1_text, (5, level1_y - 15))

    def load_game_over_assets(self):
        """Charge l'image et le son de game over"""
        try:
            # Charger l'image de game over
            game_over_path = os.path.join(self.assets_path, 'ui', 'game_over.png')
            if os.path.exists(game_over_path):
                self.game_over_image = pygame.image.load(game_over_path).convert_alpha()
                print("Image de game over chargée!")
        except Exception as e:
            print(f"Erreur lors du chargement de l'image game over: {e}")
            
        try:
            # Charger le son de game over
            game_over_sound_path = os.path.join(self.assets_path, 'sounds', 'game_over.wav')
            if os.path.exists(game_over_sound_path):
                self.game_over_sound = pygame.mixer.Sound(game_over_sound_path)
                print("Son de game over chargé!")
        except Exception as e:
            print(f"Erreur lors du chargement du son game over: {e}")
            
        try:
            # Charger le son de QTE
            qte_sound_path = os.path.join(self.assets_path, 'sounds', 'qte_alert.wav')
            if os.path.exists(qte_sound_path):
                self.qte_sound = pygame.mixer.Sound(qte_sound_path)
                print("Son de QTE chargé!")
        except Exception as e:
            print(f"Erreur lors du chargement du son QTE: {e}")

    def run(self, level_path: str):
        self.load_level(level_path)
        self.load_game_over_assets()  # Charger les assets de game over
        
        running = True
        game_over = False
        win = False
        elapsed = 0.0
        victory_timer = 0.0
        all_obstacles_passed = False
        total_obstacles = len(self.level.obstacles)  # Keep track of original obstacle count
        obstacles_passed = 0  # Count how many obstacles have been passed
        while running:
            dt = self.clock.tick(60) / 1000.0
            elapsed += dt
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # Gestion du combo en priorité
                    if self.combo_active:
                        self.handle_combo_input(event.key)
                    elif event.key in (pygame.K_SPACE, pygame.K_UP):
                        if not game_over:
                            self.player.jump(self.jump_strength)
                    elif event.key == pygame.K_r and game_over:
                        # restart - properly reinitialize everything
                        # Arrêter le son de game over s'il est en cours
                        if self.game_over_sound:
                            self.game_over_sound.stop()
                        
                        # Redémarrer la musique
                        try:
                            pygame.mixer.music.play(-1)  # -1 = loop infinitely
                        except Exception as e:
                            print(f"Erreur lors du redémarrage de la musique: {e}")
                        
                        self.load_level(level_path)
                        self.player = Player(100, self.height - 80)
                        self.scroll_x = 0.0
                        game_over = False
                        win = False
                        self.game_over_sound_played = False  # Reset pour pouvoir rejouer le son
                        self.qte_sound_played = False  # Reset pour le QTE
                        self.music_paused_for_qte = False  # Reset pour la musique
                        all_obstacles_passed = False
                        victory_timer = 0.0
                        obstacles_passed = 0
                        elapsed = 0.0
                        total_obstacles = len(self.level.obstacles)
                        # Reset combo state
                        self.combo_triggered = False
                        self.combo_active = False

            # Check for continuous space/up key press for more responsive jumping
            if not game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                    self.player.jump(self.jump_strength)

            # Vérifier les touches simultanées pour le combo
            if self.combo_active:
                self.check_combo_simultaneous()

            # update player
            if not game_over:
                self.player.update(dt, self.gravity)

            # ===== SYSTÈME DE COMBO VIDÉO À 10s =====
            if not self.combo_triggered and elapsed >= 8.0:
                self.combo_triggered = True
                self.combo_active = True
                self.combo_start_time = elapsed
                self.combo_success = False  # Reset du succès pour ce nouveau combo
                self.generate_combo()
                
                # Jouer le son de QTE et mettre la musique en pause
                if self.qte_sound and not self.qte_sound_played:
                    try:
                        pygame.mixer.music.pause()  # Mettre la musique en pause
                        self.music_paused_for_qte = True
                        self.qte_sound.play()  # Jouer le son de QTE
                        self.qte_sound_played = True
                        print("🎵 Musique mise en pause pour QTE")
                    except Exception as e:
                        print(f"Erreur lors de la pause musique: {e}")
                
                print(f"COMBO DÉCLENCHÉ ! Pressez: {' + '.join(self.combo_letters)}")

            # Gestion du combo actif
            if self.combo_active:
                combo_elapsed = elapsed - self.combo_start_time
                if combo_elapsed >= self.combo_duration:
                    # Temps écoulé
                    self.combo_active = False
                    
                    # Relancer la musique si elle était en pause pour le QTE
                    if self.music_paused_for_qte:
                        try:
                            pygame.mixer.music.unpause()  # Relancer la musique
                            self.music_paused_for_qte = False
                            print("🎵 Musique relancée après QTE")
                        except Exception as e:
                            print(f"Erreur lors de la reprise musique: {e}")
                    
                    if not self.combo_success:
                        # Combo raté = Game Over
                        game_over = True
                        pygame.mixer.music.stop()  # Arrêter la musique
                        self.game_over_sound_played = False  # Reset pour jouer le son
                        print("COMBO RATÉ - GAME OVER!")
                        # On continue la boucle pour afficher l'écran de game over
                    else:
                        print("COMBO RÉUSSI !")

            # Le jeu continue même pendant le combo

            # simple ground collision
            ground_y = self.height - 40
            if self.player.rect.bottom >= ground_y:
                self.player.rect.bottom = ground_y
                self.player.vel_y = 0
                was_on_ground = self.player.on_ground
                self.player.on_ground = True
                # Check jump buffer when landing
                if not was_on_ground and self.player.jump_buffer > 0:
                    self.player.jump(self.jump_strength)

            # scroll level
            self.scroll_x += self.level.scroll_speed * dt

            # spawn-timeline handling: spawn obstacles based on time
            if getattr(self.level, 'spawn_timeline', None):
                # move items from timeline to active obstacles when their time has come
                to_spawn = [s for s in self.level.spawn_timeline if s.get('time', 0) <= elapsed]
                for s in to_spawn:
                    sx = self.width + 100
                    sy = s.get('y', self.height - 80)
                    sw = s.get('w', 40)
                    sh = s.get('h', 80)
                    self.level.obstacles.append(Obstacle(sx, sy, sw, sh))
                    self.level.spawn_timeline.remove(s)

            # move obstacles left as the world scrolls
            for o in list(self.level.obstacles):
                o.x -= int(self.level.scroll_speed * dt)
                # Count obstacles that have been passed by the player
                if o.x + o.w < self.player.rect.x and not hasattr(o, 'counted'):
                    obstacles_passed += 1
                    o.counted = True  # Mark as counted to avoid double counting
                # remove obstacles that have scrolled past the left
                if o.x + o.w < -200:
                    try:
                        self.level.obstacles.remove(o)
                    except ValueError:
                        pass

            # Check if all obstacles have been passed based on count, not remaining obstacles
            if not all_obstacles_passed and not game_over:
                if obstacles_passed >= total_obstacles:
                    all_obstacles_passed = True
                    victory_timer = 1.0  # Start 1-second countdown

            # collision
            player_rect = self.player.rect
            collision = False
            for i, o in enumerate(self.level.obstacles):
                o_rect = o.rect()
                if player_rect.colliderect(o_rect):
                    # Les pics tuent instantanément
                    if o.is_deadly():
                        collision = True
                        break
                    
                    # Pour les plateformes et obstacles normaux, logique d'atterrissage
                    if o.is_platform():
                        # Simple and reliable collision logic - check if landing from above
                        if (player_rect.bottom <= o_rect.top + 20 and  # Player bottom is close to obstacle top (plus de marge)
                            self.player.vel_y >= 0 and  # Player is falling or stationary
                            player_rect.centerx >= o_rect.left - 25 and  # Player is roughly above obstacle (plus de marge)
                            player_rect.centerx <= o_rect.right + 25):  # Plus de marge pour éviter les glissements
                            # Valid landing on top of obstacle
                            self.player.rect.bottom = o_rect.top
                            self.player.vel_y = 0
                            was_on_ground = self.player.on_ground
                            self.player.on_ground = True
                            # Check jump buffer when landing on obstacle
                            if not was_on_ground and self.player.jump_buffer > 0:
                                self.player.jump(self.jump_strength)
                            collision = False
                            continue
                        else:
                            # All other collisions are fatal
                            collision = True
                            break

            if collision and not game_over:
                # Déclencher le game over au lieu de retourner au menu
                game_over = True
                pygame.mixer.music.stop()  # Arrêter la musique
                self.game_over_sound_played = False  # Reset pour jouer le son
                print("COLLISION - GAME OVER!")

            # draw
            # draw background layers (parallax)
            # default sky
            sky_color = (30, 30, 40)
            if self.level and getattr(self.level, 'bg_layers', None):
                # if first layer has a color, use it as sky base
                first = self.level.bg_layers[0]
                if first.get('color'):
                    sky_color = tuple(first['color'])
            self.screen.fill(sky_color)

            if self.level and getattr(self.level, 'bg_layers', None):
                for idx, layer in enumerate(self.level.bg_layers):
                    speed_factor = layer.get('speed_factor', 0.3 + idx * 0.2)
                    color = tuple(layer.get('color', [80, 80, 120]))
                    # vertical variation and scaling
                    y_base = int(self.height * layer.get('y_factor', 0.2 + idx * 0.1))
                    scale = layer.get('scale', 1.0 + idx * 0.1)
                    img = self.loaded_bg_images[idx] if idx < len(self.loaded_bg_images) else None
                    if img:
                        # scale image to layer scale and tile it seamlessly
                        iw = int(img.get_width() * scale)
                        ih = int(img.get_height() * scale)
                        if iw <= 0 or ih <= 0:
                            continue
                        scaled = pygame.transform.smoothscale(img, (iw, ih))
                        pattern_width = iw
                        offset = int((self.scroll_x * speed_factor) % pattern_width)
                        # Draw multiple copies to ensure seamless scrolling
                        for i in range(-2, 6):  # More copies for smoother scrolling
                            x = i * pattern_width - offset
                            y = y_base
                            self.screen.blit(scaled, (x, y))
                    else:
                        # fallback: colored rectangles with vertical variation
                        pattern_width = max(120 // (1 + idx), 40)
                        offset = int((self.scroll_x * speed_factor) % (pattern_width * 2))
                        for i in range(-1, 4):
                            x = i * pattern_width * 2 - offset
                            y = int(y_base + (idx % 2) * 10)
                            w = int(pattern_width * scale)
                            h = int(self.height * 0.15 * scale)
                            s = pygame.Surface((w, h), pygame.SRCALPHA)
                            s.fill((*color, 220 - idx * 40))
                            self.screen.blit(s, (x, y))

            # Draw fixed background images that cycle infinitely
            if self.scaled_bg_images:
                # Vitesse de défilement des backgrounds (plus lent que les obstacles)
                bg_scroll = self.scroll_x * 0.8
                
                # Largeur totale d'un cycle complet de backgrounds
                total_width = sum(img.get_width() for img in self.scaled_bg_images)
                
                if total_width > 0:
                    # Position dans le cycle (0 à total_width)
                    cycle_pos = bg_scroll % total_width
                    
                    # Dessiner en partant de la position cyclique
                    x_offset = -cycle_pos
                    
                    # Dessiner suffisamment de cycles pour couvrir l'écran
                    while x_offset < self.width + 100:
                        for img in self.scaled_bg_images:
                            # Dessiner cette image
                            if x_offset + img.get_width() > -100:  # Si visible
                                self.screen.blit(img, (x_offset, 0))
                            
                            # Passer à l'image suivante
                            x_offset += img.get_width()
                            
                            # Arrêter si on a couvert l'écran
                            if x_offset >= self.width + 100:
                                break
                        
                        # Si la boucle for s'est terminée sans break, on continue
                        if x_offset < self.width + 100:
                            continue
                        else:
                            break

            # draw ground
            pygame.draw.rect(self.screen, (80, 80, 100), (0, ground_y, self.width, 40))

            # decorative foreground elements removed

            # draw obstacles
            for idx, o in enumerate(self.level.obstacles):
                # Rendu différent selon le type d'obstacle
                if o.type == "spike":
                    # Pics arc-en-ciel - forme triangulaire
                    points = [
                        (o.x + o.w // 2, o.y),  # Sommet du pic
                        (o.x, o.y + o.h),       # Base gauche
                        (o.x + o.w, o.y + o.h)  # Base droite
                    ]
                    # Couleur arc-en-ciel basée sur la position X
                    import math
                    hue = (o.x / 100) % 6  # Cycle through rainbow every 600 pixels
                    if hue < 1:  # Rouge -> Orange
                        color = (255, int(255 * hue), 0)
                    elif hue < 2:  # Orange -> Jaune
                        color = (int(255 * (2 - hue)), 255, 0)
                    elif hue < 3:  # Jaune -> Vert
                        color = (0, 255, int(255 * (hue - 2)))
                    elif hue < 4:  # Vert -> Cyan
                        color = (0, int(255 * (4 - hue)), 255)
                    elif hue < 5:  # Cyan -> Bleu
                        color = (int(255 * (hue - 4)), 0, 255)
                    else:  # Bleu -> Magenta
                        color = (255, 0, int(255 * (6 - hue)))
                    
                    pygame.draw.polygon(self.screen, color, points)
                    # Contour blanc brillant pour les rendre plus visibles
                    pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)
                    
                elif o.type == "platform":
                    # Plateformes - plus claires, différentes des obstacles normaux
                    pygame.draw.rect(self.screen, (120, 120, 140), (o.x, o.y, o.w, o.h))
                    # Bordure pour les distinguer
                    pygame.draw.rect(self.screen, (200, 200, 220), (o.x, o.y, o.w, o.h), 3)
                    
                else:  # obstacle normal
                    # Use image if available, otherwise fallback to colored rectangle
                    if self.loaded_obstacle_images:
                        # Use obstacle position to determine which image to use (fixed per obstacle)
                        # This ensures each obstacle always has the same image
                        img_idx = (o.x // 100) % len(self.loaded_obstacle_images)  # Based on X position
                        img = self.loaded_obstacle_images[img_idx]
                        # Scale image to obstacle size
                        scaled_img = pygame.transform.scale(img, (o.w, o.h))
                        self.screen.blit(scaled_img, (o.x, o.y))
                    # Fallback rectangle removed - obstacles need proper images

            # draw player
            self.player.draw(self.screen, self.player_image)

            # HUD
            # Victory condition: 1 second after passing all obstacles
            if all_obstacles_passed and not game_over:
                victory_timer -= dt
                if victory_timer <= 0:
                    win = True
                    game_over = True
                    pygame.mixer.music.stop()  # Arrêter la musique

            # Affichage normal (victoire, countdown)
            if win:
                text = self.font.render("Vous avez gagné ! Appuyez sur R pour rejouer", True, (200, 255, 200))
                self.screen.blit(text, (20, 20))
            elif all_obstacles_passed and not game_over:
                # Show countdown during victory timer
                countdown_text = f"Victory in {victory_timer:.1f}s!"
                text = self.font.render(countdown_text, True, (255, 255, 100))
                self.screen.blit(text, (20, 20))

            # Dessiner le quadrillage pour l'aide à la construction (désactivé pendant le jeu)
            # self.draw_grid()

            # Dessiner le combo en haut à gauche s'il est actif
            if self.combo_active:
                combo_elapsed = elapsed - self.combo_start_time
                self.draw_combo_screen(combo_elapsed)

            # AFFICHAGE DU GAME OVER EN DERNIER (par-dessus tout)
            if game_over and not win:
                # Jouer le son de game over une seule fois
                if not self.game_over_sound_played and self.game_over_sound:
                    self.game_over_sound.play()
                    self.game_over_sound_played = True
                
                # Assombrir l'écran
                dark_overlay = pygame.Surface((self.width, self.height))
                dark_overlay.set_alpha(150)
                dark_overlay.fill((0, 0, 0))
                self.screen.blit(dark_overlay, (0, 0))
                
                # Afficher l'image de game over si disponible
                if self.game_over_image:
                    # Centrer l'image
                    img_rect = self.game_over_image.get_rect()
                    img_rect.center = (self.width // 2, self.height // 2)
                    self.screen.blit(self.game_over_image, img_rect)
                
                # Afficher "WASTED" centré dans le cadre rouge
                game_over_text = self.game_over_font.render("WASTED", True, (255, 50, 50))
                game_over_rect = game_over_text.get_rect()
                # Centrage au milieu de l'image (même position que l'image)
                game_over_rect.centerx = self.width // 2
                game_over_rect.centery = self.height // 2  # Même Y que l'image
                self.screen.blit(game_over_text, game_over_rect)
                
                # Afficher les instructions
                restart_text = self.font.render("Press R to start another run", True, (255, 200, 200))
                restart_rect = restart_text.get_rect()
                restart_rect.center = (self.width // 2, self.height - 100)
                self.screen.blit(restart_text, restart_rect)

            pygame.display.flip()

            keys = pygame.key.get_pressed()
            if collision and keys[pygame.K_r]:
                # reload level
                self.load_level(level_path)
                self.player = Player(100, self.height - 80)
                self.scroll_x = 0.0

        # stop music playback for this level (if any) and return to caller (menu)
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        return
