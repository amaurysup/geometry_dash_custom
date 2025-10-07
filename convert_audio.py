import pygame
import numpy as np
import wave
import os

def convert_wav_to_pygame_compatible():
    """Convertit level1_music.wav vers un format compatible pygame"""
    
    input_file = r"C:\Users\lalle\OneDrive\Desktop\Code python\AI in Prod\geometry_dash_custom\assets\music\level1_music.wav"
    output_file = r"C:\Users\lalle\OneDrive\Desktop\Code python\AI in Prod\geometry_dash_custom\assets\music\level1_music_converted.wav"
    
    try:
        print("🔄 Conversion en cours...")
        
        # Lire le fichier WAV original
        with wave.open(input_file, 'rb') as wav_in:
            # Obtenir les paramètres
            frames = wav_in.readframes(-1)
            sample_rate = wav_in.getframerate()
            channels = wav_in.getnchannels()
            sample_width = wav_in.getsampwidth()
            
            print(f"📊 Fichier original:")
            print(f"   - Sample rate: {sample_rate} Hz")
            print(f"   - Channels: {channels}")
            print(f"   - Sample width: {sample_width} bytes")
            
            # Convertir en numpy array
            if sample_width == 1:
                dtype = np.uint8
            elif sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                dtype = np.int16
                
            audio_data = np.frombuffer(frames, dtype=dtype)
            
            # Si mono, convertir en stéréo
            if channels == 1:
                audio_data = np.repeat(audio_data, 2)
                channels = 2
                print("🔄 Conversion mono → stéréo")
            
            # Reshape pour avoir la bonne forme (samples, channels)
            if channels == 2:
                audio_data = audio_data.reshape(-1, 2)
            
            # Normaliser et convertir en 16-bit si nécessaire
            if dtype != np.int16:
                # Normaliser vers -1 à 1, puis vers int16
                audio_data = audio_data.astype(np.float32)
                audio_data = audio_data / np.max(np.abs(audio_data))
                audio_data = (audio_data * 32767).astype(np.int16)
                print("🔄 Conversion vers 16-bit PCM")
        
        # Écrire le nouveau fichier WAV
        with wave.open(output_file, 'wb') as wav_out:
            wav_out.setnchannels(2)  # Stéréo
            wav_out.setsampwidth(2)  # 16-bit
            wav_out.setframerate(44100 if sample_rate > 22050 else 22050)  # Freq compatible
            
            # Si on change la fréquence, on doit rééchantillonner
            if sample_rate != wav_out.getframerate():
                print(f"🔄 Rééchantillonnage: {sample_rate} Hz → {wav_out.getframerate()} Hz")
                # Rééchantillonnage simple (peut perdre un peu de qualité)
                ratio = wav_out.getframerate() / sample_rate
                new_length = int(len(audio_data) * ratio)
                indices = np.linspace(0, len(audio_data) - 1, new_length).astype(int)
                audio_data = audio_data[indices]
            
            wav_out.writeframes(audio_data.tobytes())
        
        print(f"✅ Conversion réussie!")
        print(f"📁 Fichier converti: level1_music_converted.wav")
        
        # Tester le fichier converti
        print("\n🧪 Test du fichier converti...")
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        try:
            pygame.mixer.music.load(output_file)
            print("✅ Fichier converti compatible avec pygame!")
            return True
        except Exception as e:
            print(f"❌ Fichier converti toujours incompatible: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {e}")
        return False

if __name__ == "__main__":
    success = convert_wav_to_pygame_compatible()
    if success:
        print("\n🎉 Tu peux maintenant utiliser level1_music_converted.wav dans ton jeu!")
    else:
        print("\n😔 La conversion a échoué. Essaie un convertisseur en ligne.")