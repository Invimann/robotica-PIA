# end2end_control: F1 end-to-end CNN control lab

Drive the JdeRobot F1 car around a Gazebo Harmonic circuit using only its
camera image and a CNN you train yourself. More information can be found at [This link](https://jderobot.github.io/RoboticsAcademy/exercises/AutonomousCars/end_to_end_visual_control/), where several practical tips are discussed. (Note: this link uses a different docker container and structure)

```
/f1/camera/image_raw  (sensor_msgs/Image)  --> your node (CNN) --> /f1/cmd_vel (geometry_msgs/Twist)
```

This package gives you the simulation side (worlds, car spawn, bridges) and a
skeleton node. You provide the trained model and the code inside the skeleton's
`image_callback`.

## 1. Folder layout

`RoboticsInfrastructure` must sit **next to** `docker-compose.yml` and
`ros2_ws/` (the `custom_robots` link below depends on that):

```
course/                      <- the folder with docker-compose.yml
├── docker-compose.yml
├── Dockerfile
├── ros2_ws/
│   └── src/
│       ├── custom_robots  -> ../../RoboticsInfrastructure/CustomRobots   (link)
│       └── end2end_control/
└── RoboticsInfrastructure/
```

On the **host**:

```bash
cd /path/to/course
git clone https://github.com/JdeRobot/RoboticsInfrastructure.git
cd ros2_ws/src
ln -sfn ../../RoboticsInfrastructure/CustomRobots custom_robots   # relative link!
```

The link must be **relative**, as above. An absolute link points at a host path
that does not exist inside the container.

`docker-compose.yml` must mount the clone into the container (next to the
`./ros2_ws` volume):

```yaml
      - ./RoboticsInfrastructure:/home/ros/RoboticsInfrastructure
```

Then start the container as in the course Docker README (`xhost +local:docker`,
`docker compose up -d`, `docker compose exec ros2 bash`). Everything below runs
**inside the container**.

## 2. Install dependencies and build

```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src/end2end_control --ignore-src -r -y
colcon build --packages-select custom_robots end2end_control
source install/setup.bash
```

- `rosdep install` installs numpy, pillow and `onnxruntime-gpu`. Limit it to
  `src/end2end_control`, because other packages in `src/` list dependencies
  that do not exist on Jazzy.
- If pip refuses with `externally-managed-environment`, repeat the rosdep
  command prefixed with `PIP_BREAK_SYSTEM_PACKAGES=1`.
- Building `custom_robots` takes a while the first time. It provides the car
  and the track models.
- Run `source install/setup.bash` again after every `colcon build`.

Check that ONNX Runtime sees the GPU:

```bash
python3 -c "import onnxruntime as o; print(o.__version__, o.get_available_providers())"
```

`CUDAExecutionProvider` should be in the list. When you run your node, its log
line shows which providers were really loaded. If it only says
`['CPUExecutionProvider']`, the GPU is not being used.

## 3. Launch a world

```bash
ros2 launch end2end_control f1_lab.launch.py world:=simple_circuit
ros2 launch end2end_control f1_lab.launch.py world:=montmelo_line
ros2 launch end2end_control f1_lab.launch.py world:=montreal_line
ros2 launch end2end_control f1_lab.launch.py world:=nurburgring_line
```

The car appears on the start line of the circuit, on the red guide line,
facing the direction of travel. Other options:

| Argument | Meaning |
|---|---|
| `gui:=false` | run Gazebo without a window |
| `spawn_delay:=12.0` | wait longer before spawning the car (slow machines or big worlds) |
| `x:= y:= z:= Y:=` | override the start pose (metres / radians) |

Check that it works: in a second terminal (`docker compose exec ros2 bash`):

```bash
ros2 topic hz /f1/camera/image_raw
ros2 topic pub -r 10 /f1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}, angular: {z: 0.3}}"
```

The car should drive and turn. Press Ctrl+C to stop publishing.

## 4. The interface

| Topic | Type | Direction | Notes |
|---|---|---|---|
| `/f1/camera/image_raw` | `sensor_msgs/msg/Image` | sim -> you | 640x480, `rgb8`, about 20 Hz |
| `/f1/cmd_vel` | `geometry_msgs/msg/Twist` | you -> sim | `linear.x` = v, `angular.z` = w |
| `/f1/odom` | `nav_msgs/msg/Odometry` | sim -> you | optional |
| `/clock` | `rosgraph_msgs/msg/Clock` | sim -> you | optional (`use_sim_time`) |

Do not move or reconfigure the camera: the dataset was recorded with this view.

## 5. Your node

Dataset: `JdeRobot/e2e-visual-control-combined-dataset` on Hugging Face
(about 50,000 images, 4.8 GB). `label.csv` has the columns `image, v, w`
(linear and angular velocity for each image). Train a CNN, export it to
ONNX, then complete the skeleton in
`end2end_control/e2e_node.py`:

```bash
ros2 run end2end_control e2e_node --ros-args -p model_path:=/path/to/model.onnx
```

Everything in `image_callback` is yours to write: convert the image,
preprocess it exactly like in training, run the model, publish `v` and `w` with
`publish_cmd`. Re-run `colcon build --packages-select end2end_control` after
editing the node, or build once with `--symlink-install` so edits apply
directly.

Test your node in **all four worlds**.

## Troubleshooting

- **No car appears**: Gazebo was still loading. Increase `spawn_delay`.
- **`package 'custom_robots' not found`**: build it and source the workspace
  (section 2).
- **`ls ~/ros2_ws/src/custom_robots/f1` fails in the container**: the link is
  absolute or the compose volume is missing (section 1).
- **No window**: run `xhost +local:docker` on the host before starting the
  container.
- **Car ignores `/f1/cmd_vel`**: check `ros2 topic info /f1/cmd_vel` shows a
  subscriber (the Gazebo bridge). The simulator may also limit very large v/w
  values.
