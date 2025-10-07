import pygame
import os

def convert_audio_for_pygame():
    """Convertit l'audio existant vers un format compatible pygame"""
    
    # Initialiser pygame mixer avec des paramètres compatibles
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    
    music_dir = "assets/music"
    
    print("🎵 Test des fichiers audio...")
    
    # Tester différents fichiers
    test_files = ["level1_music.wav", "test.wav"]
    
    for filename in test_files:
        filepath = os.path.join(music_dir, filename)
        if os.path.exists(filepath):
            print(f"\n📁 Test de {filename}...")
            try:
                pygame.mixer.music.load(filepath)
                print(f"✅ {filename} - Format compatible!")
                
                # Renommer le fichier compatible
                if filename != "level1_music.wav":
                    new_path = os.path.join(music_dir, "level1_music_working.wav")
                    import shutil
                    shutil.copy2(filepath, new_path)
                    print(f"📋 Copié vers level1_music_working.wav")
                    
                return filename
            except Exception as e:
                print(f"❌ {filename} - Erreur: {e}")
    
    print("\n💡 Aucun fichier compatible trouvé.")
    print("Conseil: Utilise un convertisseur audio en ligne vers WAV PCM 16-bit")
    return None

if __name__ == "__main__":
    os.chdir(r"C:\Users\lalle\OneDrive\Desktop\Code python\AI in Prod\geometry_dash_custom")
    compatible_file = convert_audio_for_pygame()
    
    if compatible_file:
        print(f"\n🎉 Fichier compatible trouvé: {compatible_file}")
        print("Tu peux maintenant utiliser ce fichier dans ton jeu!")