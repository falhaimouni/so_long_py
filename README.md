# Rabbit Adventure

A Python/Pygame tile game inspired by the 42 `so_long` project. Play as a rabbit, collect all carrots, avoid hazards, and reach the burrow exit.

The project also includes an OpenCV + MediaPipe hand-tracking control mode using the MediaPipe Tasks `HandLandmarker`.

## Booth presentation

The game uses balanced moss-green framing, warm neutral panels, a sunlit title screen and a short
help screen. The larger, centered board has a slim level/carrot header and one
short objective below it. Time and step counts appear only on result screens. Switches, gates, portals and
storm paths use detailed code-drawn art; portal rings and active hazards animate.
The final victory screen celebrates with custom rabbit artwork and drifting petals. Pause, retry, level-complete and
final victory screens support both keyboard navigation and mouse buttons.
Collection particles and soft synthesized sound cues provide feedback; no extra
audio dependency is needed. The original six levels and gesture rules are retained.

Press **Enter** to begin or **H** to read the instructions on the title screen.
Use **F11** for fullscreen on the booth display. The logical canvas is 1280 × 900;
the resizable window scales the game and preserves mouse coordinates.

Generated art lives in `textures/woodland/`; see its `ASSETS.md` for the prompts.
Preview screenshots are in `previews/`.

## Features

- Pygame tile-based gameplay
- Six levels loaded from `levels.txt`, including lethal storms, portal-hunting foxes, and sinking bridges
- Map validation for required player, exit, collectibles, walls, and valid characters
- Texture-based rendering for grass, trees, rabbit, carrots, water, logs, foxes, rocks, and exits
- Smooth, time-based animation with a 60 FPS rendering target
- Independent camera capture and asynchronous hand tracking
- Keyboard controls (tap or hold to move)
- Webcam preview with MediaPipe hand detection
- Rotation-aware pointing gestures with smoothing and stable turns
- Open palm or closed fist stops movement; hand gestures never quit the game

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

The game opens a Pygame window and an OpenCV camera preview window. The final victory screen offers replay, return to title, or Q to exit.

## Controls

Keyboard:

- `W` or arrow up: move up
- `S` or arrow down: move down
- `A` or arrow left: move left
- `D` or arrow right: move right
- `R`: restart the current level at any time
- `P`: pause / resume (or use Enter to resume)
- `M`: toggle sound during gameplay
- `F11`: toggle fullscreen
- `F3`: toggle performance display
- `Q`: quit from the game window or camera preview (also works on intro, game-over, and victory screens)

Hand tracking:

- Extend your index finger and curl the other fingers, like pointing.
- Point **up, down, left, or right in the camera view** to move that way. Your hand can stay wherever it is comfortable; there are no screen zones to reach.
- Open your hand or close your fist to stop immediately.
- Keep your hand visible, with your index finger pointing across the image rather than directly toward the lens.

The mirrored camera preview draws your hand skeleton and a smoothed direction
arrow. Green indicates active movement; yellow indicates rest or a gesture settling.
It shows the recognized gesture and current direction, with instructions below.
Finger recognition uses joint geometry, so turning your hand does not reverse the
fist check. A time-based filter reduces jitter, a 30 ms stability check confirms
new directions, and hysteresis prevents rapid turns near diagonals. Lost tracking
stops movement and requires a fresh stable gesture when your hand returns.

## Levels

| Level | Name | Challenge |
| --- | --- | --- |
| 1 | Carrot Trail | Find the carrots and the burrow through a forest maze. |
| 2 | River Ride | Cross the river on moving logs. |
| 3 | Fox Forest | Escape a fox that follows the shortest route around walls (one step every 1120 ms). |
| 4 | Storm Switchyard | Swap sun/moon gates while dodging two alternating lightning lanes. Electrical storms strike the stone lanes. |
| 5 | Portal Hunt | One fox hunts through all three gardens, using the same numbered portals as you. |
| 6 | Sinking Causeway | Water and fallen planks kill. Each plank sinks after 2.52 seconds underfoot; periodic tidal waves sweep every bridge. |

Each level shows its name and carrot count in a compact header, with a short hint below the board.
All six share the same keyboard and hand movement controls. Step onto a switch
to activate it; stepping off and back on toggles it again. Matching portal numbers
teleport on entry, with no extra gesture or interaction button. The fox in level 5
can use both portal pairs too. It starts hunting after a short head start and
moves every 1512 ms. Foxes face their horizontal movement direction and retain
that facing while moving vertically or teleporting. Contact with a fox is fatal, including stepping onto one.

Storm lanes use stone paths with animated lightning during a strike.
Storms and tides switch directly from quiet to active, with no advance warning
phase or countdown. Storm cadence is preserved; tidal surges repeat every 8 seconds. Lightning strikes kill on entry and while standing in the lane.
In level 6, stepping into water or onto a collapsed plank kills immediately.
Standing on the same intact plank for 2.52 seconds also kills; moving to another
plank resets that timer. Leaving a plank collapses it permanently. A 2.52-second
tidal surge kills anyone on a bridge. Islands remain safe from the tide.
Press **R** to restart anytime.

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
| `X` | Sinking plank: collapses after departure; lethal after 2.52 seconds underfoot or during a live tidal wave |
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
hazards.py           Active lightning, tidal waves, and sinking-plank timers
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
| `GAMEPLAY_TIME_SCALE` | 2.8 | Multiplies all gameplay durations; increase for a slower game |
| `MOVE_INTERVAL_MS` | 360 | Minimum interval between keyboard/hand moves |
| `ANIMATION_MS` | 360 | Time to animate a tile movement |
| `LOG_INTERVAL_MS` | 1400 | Log movement interval |
| `FOX_INTERVAL_MS` | 1120 | Level 3 fox movement interval |
| `PORTAL_FOX_INTERVAL_MS` | 1512 | Level 5 fox movement interval |
| `PORTAL_FOX_GRACE_MS` | 3360 | Extra delay before the first portal-fox movement interval |
| `PLANK_LIFETIME_MS` | 2520 | Maximum time standing on a plank |
| `LIGHTNING_*_MS` | 7560 / 1680 | Quiet / lethal lightning durations |
| `TIDE_*_MS` | 5480 / 2520 | Quiet / lethal tide durations; 8000 ms total cycle |
| `CAMERA_WIDTH`, `CAMERA_HEIGHT` | 640, 480 | Requested camera resolution |
| `CAMERA_FPS` | 30 | Requested capture rate and target inference submission rate |
| `TRACKING_STALE_MS` | 250 | Stop using older tracking results |
| `GESTURE_SMOOTHING_MS` | 45 | Time constant for pointing-vector smoothing |
| `GESTURE_SETTLE_MS` | 30 | Confirm a stable gesture before starting or turning |
| `GESTURE_AXIS_HYSTERESIS` | 1.25 | Keep the current axis near diagonal pointing |

Hazards run at about 36% of their original speed. Player steps run slightly
faster, with animation filling the whole movement interval so held movement
flows continuously. Rendering and camera capture keep their normal rates.

Keyboard input takes priority over hand input. The first move activates immediately,
then every move respects the movement interval, even when changing direction or
briefly releasing a gesture. Releasing the key, opening your hand, or losing tracking stops repeated movement. Collisions still use tile
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
hazard cycles, and plank timers, then replay them using simulated hand directions.
They also verify that hazards and foxes actually trigger game over. Run them without a display or webcam:

```bash
PYTHONDONTWRITEBYTECODE=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest discover -s tests -v
```

If the direction feels reversed, make sure the frame is flipped before MediaPipe processing:

```python
frame = cv2.flip(frame, 1)
```
