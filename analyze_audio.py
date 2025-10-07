import pygame
import os
import shutil

def try_pygame_conversion():
    """Essaie de charger et reconvertir avec pygame"""
    
    input_file = r"C:\Users\lalle\OneDrive\Desktop\Code python\AI in Prod\geometry_dash_custom\assets\music\level1_music.wav"
    
    print("🔍 Analyse du fichier...")
    
    # Vérifier la taille du fichier
    file_size = os.path.getsize(input_file)
    print(f"📊 Taille du fichier: {file_size} bytes")
    
    # Lire les premiers bytes pour voir le format
    with open(input_file, 'rb') as f:
        header = f.read(12)
        print(f"📋 En-tête: {header}")
        
        # Vérifier si c'est vraiment un WAV
        if header[:4] != b'RIFF':
            print("❌ Ce n'est pas un fichier WAV valide (pas d'en-tête RIFF)")
            
            # Peut-être que c'est un MP3 renommé ?
            if header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
                print("💡 Ce semble être un fichier MP3 renommé en .wav")
                
                # Copier vers .mp3 et essayer
                mp3_file = input_file.replace('.wav', '_real.mp3')
                shutil.copy2(input_file, mp3_file)
                print(f"📋 Copié vers: {mp3_file}")
                
                # Tester le MP3
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                
                try:
                    pygame.mixer.music.load(mp3_file)
                    print("✅ Le fichier fonctionne comme MP3!")
                    
                    # Créer un nouveau nom pour le jeu
                    final_file = r"C:\Users\lalle\OneDrive\Desktop\Code python\AI in Prod\geometry_dash_custom\assets\music\level1_music_final.mp3"
                    shutil.copy2(mp3_file, final_file)
                    print(f"✅ Fichier prêt: level1_music_final.mp3")
                    return "music/level1_music_final.mp3"
                    
                except Exception as e:
                    print(f"❌ Même en MP3, ça ne marche pas: {e}")
            else:
                print("❓ Format de fichier inconnu")
        else:
            print("✅ En-tête RIFF trouvé, mais il y a un autre problème")
    
    return None

if __name__ == "__main__":
    result = try_pygame_conversion()
    if result:
        print(f"\n🎉 Fichier prêt à utiliser: {result}")
        print("Maintenant je vais mettre à jour la configuration du jeu...")
    else:
        print("\n😔 Impossible de convertir le fichier.")
        print("💡 Conseil: Télécharge un nouveau fichier audio ou utilise un convertisseur en ligne.")