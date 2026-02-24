# ShapeKey Axis Control — Release Notes

## What is ShapeKey Axis Control?

ShapeKey Axis Control is a Blender addon that lets you **control multiple shape keys at once** using an interactive 2D joystick controller. Instead of adjusting each shape key slider one by one, you place shape keys on a 2D coordinate map and drive them all by dragging a single joystick handle — just like a game controller.

### How It Works (Quick Example)

Imagine you want to animate a character's mouth with 4 shape keys: **Smile**, **Frown**, **Open**, **Close**.

1. Create a **Group** called "Mouth"
2. Map each shape key to a position on the 2D axis:
   - **Smile** → X: 1.0, Y: 0.0 (right)
   - **Frown** → X: -1.0, Y: 0.0 (left)
   - **Open** → X: 0.0, Y: 1.0 (up)
   - **Close** → X: 0.0, Y: -1.0 (down)
3. Press **Start** — a joystick HUD appears in the viewport
4. Drag the handle right → Smile activates smoothly
5. Drag to upper-right → both Smile + Open blend together

The addon calculates shape key weights based on **distance** from the handle to each mapped point, with adjustable radius and blend modes.

---

## Version 4.0.3

### Bug Fix
- Fixed Blender Extensions submission — added `support` URL field for issue tracking

---

## Version 4.0.2

### Core System
- **2D Axis Joystick HUD** — Interactive overlay in the 3D Viewport. Drag the handle to control shape keys in real-time
- **Multi-Object Support** — Shape key groups are per-object, so you can control different meshes independently
- **Group System** — Organize shape key mappings into named groups (e.g. "Mouth", "Eyes", "Brow"). Each group has its own joystick
- **Multiple Blend Modes** per mapping:
  - `Auto` — Automatically detects axis-aligned vs diagonal mappings
  - `Box Falloff` — Square distance falloff
  - `Radial Falloff` — Circular distance falloff
  - `X-Axis` / `Y-Axis` — Single-axis only control

### Animation
- **Keyframe Handle** — Insert a keyframe for the joystick X/Y values at the current frame
- **Auto-Key** — Works with Blender's auto-keying when the HUD is active
- **Frame Change Handler** — Joystick values update correctly when scrubbing the timeline
- **Bake Animation** — Convert animated joystick motion into raw shape key keyframes for export (FBX, GLTF, etc.). Configurable start/end frame and step

### Presets
- **Global Presets** — Save the current joystick positions of ALL groups across ALL objects as a named preset
- **Call Preset** — Instantly recall a saved preset to restore all joystick positions
- **Keyframe Preset** — Call a preset AND insert keyframes for all affected shape keys in one click
- **Reorder Presets** — Move presets up/down in the list

### Tools
- **Auto-Mirror** — Automatically generate symmetrical `.L` ↔ `.R` mappings. If "Smile.L" exists at X: 1.0, creates "Smile.R" at X: -1.0
- **Edit Values** — Manually input exact X/Y coordinates via a dialog
- **Reset Handle** — Reset a single group's joystick to center (0, 0)
- **Reset All** — Reset ALL joystick handles across every group and object
- **Reset HUD Position** — Fix the HUD if it goes off-screen
- **Enable Drag** — Toggle whether the joystick can be dragged or is locked

### Export / Import
- **Export Group** — Save a group's shape key mappings to a `.json` file
- **Import Group** — Load mappings from a `.json` file into the current group

### HUD Display
- Rendered with Blender's GPU module (`gpu`, `blf`)
- Shows joystick circle, handle position, X/Y axis labels, and group name
- Draggable HUD position in the viewport
- Visual feedback for active point position

### Tracker Interface (UDP)
- **UDP Server** — Listen on a configurable port (default: 5000) for external input
- **Start / Stop** buttons in the panel
- Supports both legacy single-group format (`{"x": 0.5, "y": 0.2}`) and multi-group format (`{"Object_Group": {"x": 0.5, "y": 0.2}}`)
- **GET_GROUPS** command — External apps can query available group names
- Processes messages at 20Hz with queue-based deduplication (always uses latest value)

### UI Panel
- Located at **View3D → Sidebar → Shape Axis**
- Group list with add/remove/reorder
- Shape key mapping list with inline editing
- Expose joystick X/Y values directly for manual driver setup
- Preset section for global animation states
- Tracker section with port configuration and start/stop controls
