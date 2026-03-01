# ShapeKey Axis Control - Release Notes

## Version 4.0.41 (Blender 4.2+ Support & Installer Fixes)
- **Blender 4.2+ Compatibility**: Restored compatibility for Blender 4.2 and above by fully migrating away from the deprecated `bgl` module in favor of pure `gpu` module calls.
- **HUD Rendering Fixes**: Fixed an issue where the Axis UI (joystick, dots, and text) would fail to draw or crash the draw loop when groups were active due to strict shader binding rules in Blender 4.0+.
- **Robust Dependency Installer**: The "Install Face Tracker Requirements" button now auto-upgrades `pip`, falls back to `--user` installation if permission is denied, and reports detailed `STDOUT` error logs directly to the Blender Info Log and System Console instead of a generic exit status 1.
- **Improved HUD Error Tracking**: Added granular `try...except` blocks within the draw loop to help catch and isolate rendering failures natively within the UI.

## Version 4.0.4 (Face Tracker Integration)
- **Built-In Face Tracker**: The ShapeKeyFaceTracker algorithm is now fully integrated natively within Blender as a module inside the addon.
- **Removed Dear PyGui dependency**: You no longer need to open the external `.exe`. Everything happens in the 3D Viewport.
- **One-Click Installer**: Added automatic UI button to install Python tracking dependencies (`opencv` and `mediapipe`).
- **Live Preview Window**: Added a native UI pixel preview window straight to Blender UI, displaying tracking dots.
- **Embedded Target Management**: Target Groups, X/Y Landmark configurations, Tracking Limits and Filters are now directly tied and saved onto objects as part of Blender's native Addon `shape_xy_groups` settings.
- **Removed UDP Background Setup**: The pipeline uses Blender timers and memory to transfer capture frames securely & reliably.
- **Extension Support**: Updated `blender_manifest.toml` to support the modern add-on architecture.
