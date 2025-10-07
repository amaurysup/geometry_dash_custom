# 🎵 Guide Musique - Geometry Dash Custom

## Formats supportés
- MP3 (recommandé)
- OGG
- WAV

## Comment ajouter de la musique à un niveau

1. **Placer le fichier audio** dans ce dossier (`assets/music/`)

2. **Modifier le fichier JSON du niveau** en ajoutant :
```json
{
  "music": "music/nom_de_votre_fichier.mp3"
}
```

## Exemple pour level1.json
```json
{
  "width": 800,
  "height": 450,
  "scroll_speed": 350,
  "music": "music/level1_music.mp3",
  "bg_layers": [...]
}
```

## Notes importantes
- La musique se lance automatiquement au début du niveau
- Elle boucle automatiquement
- Formats recommandés : MP3 (meilleure compatibilité)
- Taille recommandée : < 10MB pour de bonnes performances

## Musiques suggérées
- Niveau 1 : Musique énergique et motivante
- Niveau 2+ : Augmenter progressivement l'intensité
- Boss levels : Musique épique et dramatique