# Rabbit Adventure

A six-level woodland puzzle game built with Pygame. Collect every carrot and
reach the burrow while avoiding foxes, water, lightning, and tidal waves.

## Run

Requires Python 3, Pygame, OpenCV, and MediaPipe:

```bash
pip install pygame opencv-python mediapipe
python3 main.py
```

A webcam enables hand controls. Its live preview and hand overlay appear beside
the board inside the game window. Keyboard controls remain available if the
camera cannot open. Keep `hand_landmarker.task`, `levels.txt`, and `textures/` with the
Python source files.

Fullscreen renders at the display's native resolution. Text, game tiles, and the
webcam panel resize directly from their sources when the window size changes.

## Controls

- **Enter / Space:** start or continue; **H:** title-screen instructions.
- **WASD / arrows:** move.
- **P:** pause; **R:** retry the current level.
- **M:** toggle sound during play; return to title from a result screen.
- **F11:** fullscreen; **Q:** exit.
- **Hand controls:** extend only your index finger and point in the desired
  direction. Open your palm or close your fist to stop.

## Levels

1. **Carrot Trail:** collect carrots through a forest maze.
2. **River Ride:** cross the water on moving logs.
3. **Fox Forest:** stay ahead of the pursuing fox.
4. **Storm Switchyard:** toggle sun/moon gates and cross electrical paths.
5. **Portal Hunt:** use matching portals while a fox follows you.
6. **Sinking Causeway:** cross fragile planks between safe islands.

Foxes turn to face their horizontal movement. Storms and waves activate without
advance warnings. Waves repeat every **8 seconds** and remain active for 2.52
seconds. Planks collapse after departure or become lethal after 2.52 seconds
underfoot. Islands remain safe during waves.
