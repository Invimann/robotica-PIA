# FSM Demo Lab — Reactive Obstacle Avoidance with ROS 2 + Gazebo

In this lab you will complete a Python ROS 2 node that makes a TurtleBot3
Burger navigate autonomously using a simple **3-state Finite State Machine**:

```

    ┌─────────┐  obstacle     ┌──────┐   2 s    ┌──────┐
    │ FORWARD │ ────────────► │ BACK │ ────────► │ LEFT │
    └─────────┘  detected     └──────┘           └──────┘
          ▲                                         │
          └─────────────────────────────────────────┘
                             2 s
```

Your node subscribes to the robot's **lidar** (`/scan`) and publishes
**velocity commands** (`/cmd_vel`). The simulation and the robot driver are
already provided — your job is to set up those ROS interfaces and implement
the obstacle-avoidance logic in `fsm_demo_node.py`.

---

## Before you start — check your Docker environment

This lab runs inside the course Docker container. If you haven't set it up
yet, follow the main `README.md` in the project root first, then come back
here.

Confirm the container is running:
```bash
# On your host
docker compose ps
```
You should see `ros2_jazzy_gpu` with status `Up`.

---

## Step 0 — One-time setup (TurtleBot3 simulation packages)

The TurtleBot3 simulation model is **not** baked into the Docker image — you
need to install it once inside the running container.

> ⚠️ This installation lives inside the container, not on your host.
> If you ever run `docker compose down` (which removes the container) you
> will need to repeat this step. `docker compose stop` / `docker compose start`
> is safe and preserves the installation.

Open a shell inside the container:
```bash
# On your host
docker compose exec ros2 bash
```

Then, inside the container:
```bash
sudo apt-get update
sudo apt-get install -y \
    ros-jazzy-turtlebot3-gazebo \
    ros-jazzy-turtlebot3-description
```

Verify the install worked:
```bash
ros2 pkg list | grep turtlebot3
# You should see: turtlebot3_description  turtlebot3_gazebo  (among others)
```

You only need to do this **once per container lifetime**. Leave this shell
open — you'll use it in the next steps.

---

## Step 1 — Place the package in your workspace

The `fsm_demo` package folder should go inside the workspace source
directory. On your **host** machine:

```
ros2_ws/
└── src/
    └── fsm_demo/        ← put the provided folder here
        ├── fsm_demo/
        │   ├── __init__.py
        │   └── fsm_demo_node.py   ← this is the file you will edit
        ├── launch/
        │   └── sim.launch.py
        ├── worlds/
        │   ├── empty.sdf
        │   ├── obstacles.sdf
        │   └── corridor.sdf
        ├── resource/
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

> The `ros2_ws/` folder on your host is automatically shared with the
> container at `/home/ros/ros2_ws/`. You can edit files with any editor
> on your host and build/run them inside the container.

---

## Step 2 — Build the package

Inside the container:

```bash
cd ~/ros2_ws
colcon build --packages-select fsm_demo
source install/setup.bash
```

You should see:
```
Starting >>> fsm_demo
Finished <<< fsm_demo [...]
Summary: 1 package finished [...]
```

> **Every time you edit `fsm_demo_node.py`** you need to re-run these two
> commands. The `source` line must also be re-run in any new terminal you
> open inside the container.

---

## Step 3 — Run the simulation

You will need **two terminal windows** inside the container for the full
workflow. Open a second one with:
```bash
# On your host (second terminal)
docker compose exec ros2 bash
```

### Terminal 1 — allow GUI windows (run once per login on the host)
```bash
# On your host, before opening Gazebo
xhost +local:docker
```

### Terminal 1 — launch the simulation
```bash
# Inside the container
ros2 launch fsm_demo sim.launch.py
```

This opens the Gazebo window with the default world (`obstacles`). You should
see a TurtleBot3 Burger spawn and sit still — it won't move until your node
is running.

**To try a different world:**
```bash
ros2 launch fsm_demo sim.launch.py world:=empty
ros2 launch fsm_demo sim.launch.py world:=corridor
```

| World | What it tests |
|---|---|
| `empty` | Open field — confirms your node drives the robot forward |
| `obstacles` | Five scattered boxes — tests all three FSM states *(default)* |
| `corridor` | Enclosed arena — robot triggers FSM repeatedly; observe the long-term pattern |

### Terminal 2 — run your node
```bash
# Inside the container (source first if you haven't in this terminal)
source ~/ros2_ws/install/setup.bash

ros2 run fsm_demo fsm_demo_node --ros-args -p use_sim_time:=true
```

The `use_sim_time:=true` flag makes your node use Gazebo's clock instead of
wall-clock time, which keeps the 2-second timers accurate.

---

## Step 4 — Complete the node

Open `fsm_demo/fsm_demo_node.py` in your editor. Complete **STEP 0** in
`__init__` to set up the ROS interfaces, then complete the **four TODO
blocks** inside `_timer_callback`.

### STEP 0 — Create the publisher and subscriber

Create a publisher for `Twist` messages on `/cmd_vel` and a subscriber for
`LaserScan` messages on `/scan`. Connect the subscriber to `_scan_callback`
so the node stores the latest lidar scan for the FSM timer to use.

### STEP 1 — Forward sector distance
Extract the minimum lidar range in a ±30° window around the robot's nose.

Hints:
- Index `0` is directly forward. The scan has 360 values (one per degree).
- ±30° means indices `0–30` **and** `330–359`. Notice the wrap-around —
  a single `range(0, 60)` slice will read the *wrong* rays.
- Filter out `inf` and `nan` before calling `min()`. What does `min([])` do?
  What should you return if there are no valid readings?

### STEP 2 — FORWARD state
Drive straight until an obstacle is closer than `OBSTACLE_THRESHOLD`.

### STEP 3 — BACK state
Reverse for `BACK_DURATION` seconds, then switch to `LEFT`.

Hint for measuring elapsed time:
```python
elapsed = (self.get_clock().now() - self._state_start_time).nanoseconds * 1e-9
```

### STEP 4 — LEFT state
Rotate counter-clockwise for `TURN_DURATION` seconds, then return to `FORWARD`.

Reminder: in ROS 2, **positive `angular.z` = turning left** (counter-clockwise
when viewed from above).

### Tune the robot's behavior

The node defines its behavior settings as constants near the top of
`fsm_demo_node.py`. Their units are metres, metres/second, radians/second,
and seconds:

| Constant | Purpose |
|---|---|
| `FORWARD_SPEED` | Forward linear speed |
| `BACK_SPEED` | Reverse linear speed magnitude (publish it as negative) |
| `TURN_SPEED` | Counter-clockwise angular speed |
| `BACK_DURATION` | Time spent reversing |
| `TURN_DURATION` | Time spent turning left |
| `OBSTACLE_THRESHOLD` | Distance at which the robot reacts to an obstacle |

Once the node works, experiment with these values. In particular, tune
`OBSTACLE_THRESHOLD` so the robot begins reversing early enough to avoid
collisions.

When you stop the node, it publishes a zero-velocity command before exiting,
leaving the robot stationary.

---

## Useful commands for debugging

All of these run inside the container while the simulation is running:

```bash
# Confirm the robot is receiving velocity commands
ros2 topic echo /cmd_vel

# Confirm the lidar is publishing
ros2 topic echo /scan --once

# Print just the range count (should be 360 for TB3 Burger)
ros2 topic echo /scan --once | grep -i ranges | head -1

# See the FSM state transitions in the node log
# (look for lines like "FSM transition: FORWARD → BACK")
ros2 topic echo /rosout

# Watch the robot's position
ros2 topic echo /odom --once
```

---

## Troubleshooting

### Gazebo opens but the robot never appears
The spawn is delayed 3 seconds after Gazebo starts. Wait a moment. If it
still doesn't appear, check the launch output for errors referencing
`turtlebot3_gazebo` or `model.sdf`.

### `/scan` is not in `ros2 topic list`
The bridge or the spawn may have failed. Check Terminal 1 for error messages.
Also confirm the TB3 packages are installed (Step 0).

### Robot moves in one direction and never stops (FORWARD only)
Your forward sector extraction (STEP 1) is likely returning `inf` for all
readings. Add a temporary debug print to check:
```python
self.get_logger().info(f'min_front_dist = {min_front_dist}')
```

### Node crashes with `ValueError: min() arg is an empty sequence`
You called `min()` on an empty list. This happens when every ray in the
forward sector returns `inf` or `nan`. Handle the empty-list case before
calling `min()` (see STEP 1 hints).

### `colcon build` fails with `package not found`
Run `sudo apt-get install -y ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3-description`
inside the container (Step 0), then rebuild.

### I ran `docker compose down` and lost my TB3 install
`docker compose down` removes the container. Repeat Step 0 after your next
`docker compose up`.
To avoid this in future, use `docker compose stop` / `docker compose start`
to pause and resume without destroying the container.

### Gazebo window doesn't open (no display)
On your **host** (not inside the container), run:
```bash
xhost +local:docker
```
Then relaunch. This is required once per login session.