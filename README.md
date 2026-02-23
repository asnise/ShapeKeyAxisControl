# ShapeKey Axis Control

A Blender addon for controlling shape keys using a 2D Axis HUD Joystick. Map shape keys to X/Y axes and drive them interactively with an on-screen controller.

## Features

- **2D Axis Joystick** — On-screen HUD controller for real-time shape key manipulation
- **Multi-Object Support** — Control shape keys across multiple objects simultaneously
- **Group System** — Organize shape key mappings into groups for complex rigs
- **Preset System** — Save and recall shape key states as presets
- **Auto-Key Support** — Automatically insert keyframes while adjusting
- **Auto-Mirror** — Automatically generate symmetrical `.L`/`.R` mappings
- **Animation Bake** — Bake joystick animation to individual shape key keyframes
- **Export / Import** — Share group configurations between projects
- **Face Tracker Integration** — Connect with external face tracking via UDP
- **HUD Shortcuts** — Quick toggle and reset controls from the viewport

## Installation

### Blender 4.2+
1. Download the latest release from [Releases](https://extensions.blender.org/approval-queue/shapekey-axis-control/)
2. In Blender: **Edit → Preferences → Add-ons → Install from Disk**
3. Select the downloaded `.zip` file
4. Enable **ShapeKey Axis Control** in the addon list

### From Blender Extensions
Search for **"ShapeKey Axis Control"** in **Edit → Preferences → Get Extensions**

## Usage

1. Select an object with shape keys
2. Open the **Sidebar (N)** → **Shape XY** tab
3. Create a new **Group** and add shape key mappings
4. Assign shape keys to X and/or Y axes with desired ranges
5. Click **Start** to enable the HUD joystick
6. Drag the joystick handle to control your shape keys in real-time

## Face Tracker

A companion Python app is included in the `ShapeKeyFaceTracker` folder for mapping real-time face tracking to shape key groups via UDP.

## Requirements

- Blender **4.2.0** or later

## License

GPL-3.0-or-later — See [LICENSE](LICENSE) for details.

## Support

Report bugs and request features on the [Issues page](https://github.com/asnise/ShapeKeyAxisControl/issues).

## Author

**Axnise** — [GitHub](https://github.com/asnise)
