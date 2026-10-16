# Woodland art

Created for this project with the built-in `image_gen` tool. No API/CLI fallback
was used. Assets are loaded locally; the game does not call an image service.
The original `textures/*.png` assets remain as the fallback art set.

- `title.png`: cinematic title-screen illustration, 1536 × 1024.
- `tiles.png`: RGBA atlas, 1254 × 1254, nine equal 418 × 418 cells.
  Row 1: original grass, tree, rabbit. Row 2: carrot, burrow, water.
  Row 3: log, fox, rocks. The loader slices cells and smooth-scales to game tiles.
- `ground.png`: quiet walkable floor; overrides the atlas grass for legibility.

## Title prompt

Use case: stylized-concept. Asset type: title-screen background for a polished Rabbit Adventure forest puzzle game shown at a technical booth. Create a cinematic wide landscape illustration, 1536x1024. A lush enchanted woodland at dusk with deep midnight teal shadows, softly glowing mint vegetation, warm amber fireflies, winding stepping-stone path and a small inviting burrow under old tree roots on the RIGHT half. One charming small ivory rabbit with long ears seen from behind on the path in the lower RIGHT third, a few orange carrots beside the path. Sophisticated hand-painted 3D game art, tactile moss and stone textures, atmospheric depth, premium indie adventure aesthetic. LEFT half mostly quiet very dark forest for readable UI text to be overlaid by code. No text, letters, logos, interface, watermarks or borders.

## Tile atlas prompt

Use case: stylized-concept. Asset type: production 2D game tile atlas, exactly 3 columns by 3 rows of equal square cells, square 1536x1536 image, each tile centered in its cell. Professional top-down woodland puzzle game, rich painterly storybook game art, crisp readable silhouettes, consistent overhead camera, midnight teal and emerald vegetation, warm ivory rabbit and orange carrots. Every cell has a flat solid dark teal background #183c36, no grid borders or gaps. Row 1 left: seamless dark mossy grass ground texture fills cell edge to edge, subtle tiny leaves, unobstructed walkable grass. Row 1 middle: dense rounded evergreen bush/tree canopy filling cell, top down forest obstacle. Row 1 right: cute small ivory rabbit facing right with long pink inner ears, full body centered with generous 12 percent margin, overhead three-quarter view. Row 2 left: single large bright orange carrot with green leafy top centered with generous margin. Row 2 middle: small welcoming hollow burrow entrance in mossy roots with golden light centered, overhead three-quarter view. Row 2 right: dark turquoise water texture edge to edge, gentle stylized ripples. Row 3 left: horizontal thick wooden floating log centered, cut ends, moss, overhead view. Row 3 middle: cute dangerous russet fox facing left, full body fluffy tail centered with generous margin, overhead three-quarter view. Row 3 right: cluster of rounded slate rocks with moss centered. EXACT nine cells, EXACT order, no text, no letters, no labels, no UI, no watermark, no scenery crossing cell boundaries. Consistent lighting and shadows.

## Transparency edit prompt

Edit this 3 by 3 sprite atlas for game integration. Remove only the solid dark teal background behind the tree, rabbit, carrot, burrow, log, fox and rocks and replace it with true alpha transparency. Preserve the grass texture in top left and water texture in middle right as opaque full squares. Preserve all nine objects and their grid cell positions and exact 3x3 layout, silhouettes, original painterly style, colors and sizing. No added objects, no text. Transparent background.

## Walkable ground prompt

Use case: stylized-concept. Asset type: single square seamless walkable floor texture for a top-down forest maze game, will repeat at 56x56 pixels. Create a very quiet low-detail woodland dirt ground tile: smooth matte dark desaturated warm sage-gray packed soil, a very subtle touch of dusty moss, almost uniform center with tiny soft grain. Clearly walkable empty ground. Premium painterly game texture, overhead orthographic lighting, no cast shadows, no perspective. Color around muted gray-green #647363 with gentle variations, not bright green. No plants, no large leaves, no rocks, no flowers, no objects, no text, no border. Seamless edge-to-edge. Priority: extremely restrained texture so characters and green tree obstacles remain readable at small size.


## Bright daytime revision

The active title and walkable floor are now `title-day.png` and `ground-day.png`.
The original dusk and muted-ground assets are retained as earlier variants.
Both revisions use the built-in `image_gen` tool.

### Daytime title edit prompt

Edit this game title illustration from dark dusk into a bright cheerful spring morning. Preserve the rabbit, burrow, winding path and forest composition, same charming polished storybook game-art style. All areas including the LEFT forest should now be airy, sunlit and welcoming with fresh light green leaves, soft golden sunshine and a pale blue sky. Replace midnight teal shadows with gentle warm green shade. No ominous atmosphere. Keep the left half relatively low-detail for dark green text to be added by code on a cream translucent panel. No text, logos, watermarks or UI.

### Daytime ground prompt

Use case: stylized-concept. Asset type: seamless square walkable ground texture for a bright friendly top-down woodland rabbit puzzle game. Very restrained smooth soft fresh spring green meadow ground, pale yellow-green moss and subtle tiny blades, warm gentle daylight, matte painterly storybook style. Quiet low-detail texture that repeats cleanly at 64x64 pixels, evenly lit edge to edge, no borders or shadows, no large leaves or flowers or objects. Predominant color fresh light grass green around #a4c978 with subtle variations. Inviting sunny cheerful mood. No dark teal, gray mud, black, text or watermark.


## Happy ending illustration

`ending.png` is the full-screen celebration scene, generated with the built-in
`image_gen` tool. `puzzle_art.py` draws switches, gates, animated portals, and
storm-path materials directly at 3× resolution before downsampling. Hazard effects
and victory petals are animated by code. The ground receives a gentle ambient
color grade at render time to balance the surrounding moss-green frame.

### Ending prompt

Use case: stylized-concept. Asset type: wide victory background for Rabbit Adventure woodland puzzle game, 1536x1024. Happy ending: a charming ivory rabbit with soft pink inner ears celebrating beside a full woven basket of bright orange carrots outside its welcoming mossy tree-root burrow. Rabbit and basket prominent on RIGHT half, rabbit looks delighted, upright ears, friendly face. Gentle floating golden leaves and flower petals, warm late-afternoon sunlight, rich balanced fresh green woodland, cozy amber burrow light. Premium painterly 3D storybook game art with tactile moss, wood and fur. LEFT half quieter softly shaded green woodland suitable for a dark translucent text panel added by code. Balanced warm colors, neither washed-out white nor dark nighttime. No text, logos, UI or watermarks.
