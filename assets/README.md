Assets folder

Place your background, obstacle, player and music PNG/MP3 files here.

## Player Image (PNG):
- `player.png` - Image for the player character
- Will be automatically scaled to 40x40 pixels
- If missing, falls back to colored rectangle

## Background Images (PNG):
- `bg1.png`, `bg2.png`, `bg3.png`, etc. - Parallax background layers (tiled and scrolling)
- Images will be tiled horizontally and scroll at different speeds for parallax effect

## Fixed Background Images (PNG):
- `background1.png`, `background2.png`, `background3.png`, etc. - Fixed backgrounds that follow each other
- These images are placed one after another and scroll as a sequence (not tiled)
- Perfect for creating a continuous landscape or story sequence

## Obstacle Images (PNG):
- `obstacle1.png`, `obstacle2.png`, `obstacle3.png`, etc. - Images for obstacles
- Each obstacle will have a FIXED image based on its position (no cycling)
- Images will be automatically scaled to fit obstacle dimensions
- Recommended: square or rectangular images work best

## Other Assets:
- `music.mp3` (optional) - background music

## Tips:
- **Player image**: Recommended size 40x40px or square format
- **Parallax backgrounds (bg1.png, etc.)**: Use seamless/tileable images (width: 800-1600px)
- **Fixed backgrounds (background1.png, etc.)**: Can be any width, will be placed sequentially
- **Obstacle images**: Can be any size, will be scaled automatically to 50px width
- **Format**: PNG with transparency is recommended, JPG also works
- Place your files directly in this folder with the exact names above

If files are missing, the engine will fall back to colored shapes.
