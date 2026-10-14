# Rabbit Adventure

A Python/Pygame tile game inspired by the 42 `so_long` project. Play as a rabbit, collect all carrots, avoid hazards, and reach the burrow exit.

The project also includes an OpenCV + MediaPipe hand-tracking control mode using the MediaPipe Tasks `HandLandmarker`.

## Features

- Pygame tile-based gameplay
- Six levels loaded from `levels.txt`, including lethal storms, portal-hunting foxes, and sinking bridges
- Map validation for required player, exit, collectibles, walls, and valid characters
- Texture-based rendering for grass, trees, rabbit, carrots, water, logs, foxes, rocks, and exits
- Smooth, time-based animation with a 60 FPS rendering target
- Independent camera capture and asynchronous hand tracking
- Keyboard controls (tap or hold to move)
- Webcam preview with MediaPipe hand detection
- Index-finger zone controls
- Closed fist pauses movement; hand gestures never quit the game

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

The game opens a Pygame window and an OpenCV camera preview window. The victory screen stays open until you press Q.

## Controls

Keyboard:

- `W` or arrow up: move up
- `S` or arrow down: move down
- `A` or arrow left: move left
- `D` or arrow right: move right
- `R`: restart the current level at any time
- `F3`: toggle performance display
- `Q`: quit from the game window or camera preview (also works on intro, game-over, and victory screens)

Hand tracking:

- Point with your index finger.
- Move your fingertip into a camera zone:
  - top zone: move up
  - bottom zone: move down
  - left zone: move left
  - right zone: move right
  - center zone: no movement
- Close your fist to pause movement. Hand gestures cannot quit the game.

The webcam frame is mirrored with `cv2.flip(frame, 1)`, so the controls feel natural like looking into a mirror.

## Levels

| Level | Name | Challenge |
| --- | --- | --- |
| 1 | Carrot Trail | Find the carrots and the burrow through a forest maze. |
| 2 | River Ride | Cross the river on moving logs. |
| 3 | Fox Forest | Escape a faster fox that follows the shortest route around walls (one step every 450 ms). |
| 4 | Storm Switchyard | Swap sun/moon gates while dodging two alternating lightning lanes. Amber warnings turn into lethal lightning. |
| 5 | Portal Hunt | One fox hunts through all three gardens, using the same numbered portals as you. |
| 6 | Sinking Causeway | Water and fallen planks kill. Each plank sinks after 0.9 seconds underfoot; periodic tidal waves sweep every bridge. |

Each level shows its name, objective, and remaining carrots along the bottom.
All six share the same keyboard and hand movement controls. Step onto a switch
to activate it; stepping off and back on toggles it again. Matching portal numbers
teleport on entry, with no extra gesture or interaction button. The fox in level 5
can use both portal pairs too. It starts hunting after a short head start and
moves every 600 ms. Contact with a fox is fatal, including stepping onto one.

Storm lanes have a permanent outline, an amber lightning warning, then bright
lethal lightning. Lightning strikes kill on entry and while standing in the lane.
In level 6, stepping into water or onto a collapsed plank kills immediately.
Standing on the same intact plank for 0.9 seconds also kills; moving to another
plank resets that timer. Leaving a plank collapses it permanently. Blue waves warn
before a 0.9-second tidal surge kills anyone on a bridge. Islands remain safe from
the tide. Watch the countdown along the bottom, and press **R** to restart anytime.

To try a new level directly with keyboard controls (indexes start at zero):

```bash
python3 -c 'from game import run_game; run_game(3)'
```

For hands, run `python3 main.py` and progress through the levels as usual.

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
| `S` | Gold switch plate: toggles all sun/moon gates |
| `G`, `H` | Sun and moon gates (sun starts closed, moon starts open) |
| `A`, `B` | Portal pair 1 |
| `U`, `V` | Portal pair 2 |
| `X` | Sinking plank: collapses after departure; lethal after 0.9 seconds underfoot or during a live tidal wave |
| `T` | Storm lane: lethal during a lightning strike |

Valid maps must be rectangular, surrounded by walls, include exactly one player start, exactly one exit, and at least one collectible. Portal endpoints must appear in matching pairs, and gate puzzles must include a switch.

## Project Structure

```text
main.py              Program entry point and camera lifecycle
game.py              Main game loop, movement, drawing, hazards
hand_tracking.py     Camera worker, asynchronous detection, preview, tracking metrics
motion.py            Timed input repetition and interpolated drawing positions
level_loader.py      Loads and validates levels from levels.txt
level_mechanics.py   Gates, portals, bridge rules, fox pathfinding, and level guides
hazards.py           Lightning warnings, tidal waves, and sinking-plank timers
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

### Movement and performance

Tune these constants in `config.py`:

| Setting | Default | Purpose |
| --- | --- | --- |
| `TARGET_FPS` | 60 | Rendering target |
| `MOVE_INTERVAL_MS` | 150 | Interval between repeated keyboard/hand moves |
| `ANIMATION_MS` | 120 | Time to animate a tile movement |
| `LOG_INTERVAL_MS` | 500 | Log movement interval |
| `FOX_INTERVAL_MS` | 450 | Level 3 fox movement interval |
| `PORTAL_FOX_INTERVAL_MS` | 600 | Level 5 fox movement interval |
| `PORTAL_FOX_GRACE_MS` | 1200 | Extra delay before the first portal-fox movement interval |
| `PLANK_LIFETIME_MS` | 900 | Maximum time standing on a plank |
| `LIGHTNING_*_MS` | 1800 / 900 / 600 | Quiet / warning / lethal lightning durations |
| `TIDE_*_MS` | 4200 / 1200 / 900 | Quiet / warning / lethal tide durations |
| `CAMERA_WIDTH`, `CAMERA_HEIGHT` | 640, 480 | Requested camera resolution |
| `CAMERA_FPS` | 30 | Requested capture rate and target inference submission rate |
| `TRACKING_STALE_MS` | 250 | Stop using older tracking results |

Keyboard input takes priority over hand input. A direction activates immediately,
then repeats at the movement interval. Releasing the key, returning your finger to
the center, or losing tracking stops repeated movement. Collisions still use tile
coordinates; animation changes the displayed position between tiles. Wrapped logs
appear at their destination rather than sliding across the entire river.

Capture runs in a worker thread, while MediaPipe uses `LIVE_STREAM` and
`detect_async()`. Busy inference drops frames; the game reads the latest result
without waiting for the camera. See the [MediaPipe guide](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python).
Camera/model failures leave keyboard controls available. Camera resolution, FPS,
and the one-frame buffer request depend on backend support.

Press **F3** to see game FPS, frame duration, game work time (excluding the FPS
limiter), camera capture FPS, latest frame age, tracking latency, and result age.
Frame age starts when OpenCV returns a captured frame; it does not measure hidden
camera-driver buffering. Tracking latency includes conversion, submission, and
callback delivery, rather than measuring only model execution. Compare the game
with and without tracking using `python3 -c 'from game import run_game; run_game()'`.
Actual performance depends on the camera and hardware.

The tests find surviving routes through levels 3–6, accounting for enemy positions,
warning cycles, and plank timers, then replay them using simulated hand directions.
They also verify that hazards and foxes actually trigger game over. Run them without a display or webcam:

```bash
PYTHONDONTWRITEBYTECODE=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest discover -s tests -v
```

If the direction feels reversed, make sure the frame is flipped before MediaPipe processing:

```python
frame = cv2.flip(frame, 1)
```
