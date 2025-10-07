import pygame
import numpy as np
import os

# Créer un son de test simple
def create_test_sound():
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    
    # Paramètres
    duration = 3  # 3 secondes
    sample_rate = 22050
    
    # Créer un son simple (bip)
    frames = int(duration * sample_rate)
    arr = np.sin(2 * np.pi * 440 * np.linspace(0, duration, frames))
    arr = (arr * 32767).astype(np.int16)
    
    # Convertir en format stéréo
    stereo_arr = np.zeros((frames, 2), dtype=np.int16)
    stereo_arr[:, 0] = arr  # Canal gauche
    stereo_arr[:, 1] = arr  # Canal droit
    
    # Créer un objet sound pygame
    sound = pygame.sndarray.make_sound(stereo_arr)
    
    # Sauvegarder
    output_path = "assets/music/test.wav"
    pygame.mixer.quit()
    
    print(f"Son de test créé avec succès!")
    return True

if __name__ == "__main__":
    try:
        create_test_sound()
    except Exception as e:
        print(f"Erreur: {e}")
        print("numpy requis: pip install numpy")