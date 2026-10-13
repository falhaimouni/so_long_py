# Rabbit Adventure

A Python/Pygame tile game inspired by the 42 `so_long` project. Play as a rabbit, collect all carrots, avoid hazards, and reach the burrow exit.

The project also includes an OpenCV + MediaPipe hand-tracking control mode using the MediaPipe Tasks `HandLandmarker`.

## Features

- Pygame tile-based gameplay
- Multiple levels loaded from `levels.txt`
- Map validation for required player, exit, collectibles, walls, and valid characters
- Texture-based rendering for grass, trees, rabbit, carrots, water, logs, foxes, rocks, and exits
- Keyboard controls
- Webcam preview with MediaPipe hand detection
- Index-finger zone controls
- Closed-fist quit gesture

## Requirements

- Python 3
- Webcam
- `pygame`
- `opencv-python`
- `mediapipe`
- `hand_landmarker.task` in the project root

Install dependencies:

```bash
pip install pygame opencv-python mediapipe
```

## Run

From the project root:

```bash
python3 main.py
```

The game opens a Pygame window and an OpenCV camera preview window.

## Controls

Keyboard:

- `W` or arrow up: move up
- `S` or arrow down: move down
- `A` or arrow left: move left
- `D` or arrow right: move right
- `Esc`: quit
- `R`: restart after game over

Hand tracking:

- Point with your index finger.
- Move your fingertip into a camera zone:
  - top zone: move up
  - bottom zone: move down
  - left zone: move left
  - right zone: move right
  - center zone: no movement
- Hold a closed fist for about `0.7` seconds to quit.

The webcam frame is mirrored with `cv2.flip(frame, 1)`, so the controls feel natural like looking into a mirror.

## Map Symbols

Levels are stored in `levels.txt` and separated with `---`.

| Symbol | Meaning |
| --- | --- |
| `1` | Wall/tree |
| `0` | Floor/grass |
| `P` | Player start |
| `C` | Collectible/carrot |
| `E` | Exit/burrow |
| `W` | Water |
| `L` | Log |
| `F` | Fox |
| `R` | Rock |

Valid maps must be rectangular, surrounded by walls, include exactly one player start, exactly one exit, and at least one collectible.

## Project Structure

```text
main.py              Program entry point and camera/detector setup
game.py              Main game loop, movement, drawing, hazards, hand controls
level_loader.py      Loads and validates levels from levels.txt
map_validator.py     Map validation helpers
texture_loader.py    Loads and scales texture assets
config.py            Shared constants
levels.txt           Level definitions
textures/            Game image assets
hand_landmarker.task MediaPipe hand landmark model
```

## Troubleshooting

If the camera does not open, make sure no other app is using it and that `cv2.VideoCapture(0)` works on your machine.

If MediaPipe fails to start, check that `hand_landmarker.task` exists in the project root.

If hand movement feels too fast or too slow, adjust `GESTURE_COOLDOWN` in `game.py`.

If the direction feels reversed, make sure the frame is flipped before MediaPipe processing:

```python
frame = cv2.flip(frame, 1)
```
