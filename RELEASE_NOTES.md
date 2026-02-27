# ShapeKey Axis Control - Release Notes

## Version 4.0.4 (Face Tracker Integration)
- **Built-In Face Tracker**: The ShapeKeyFaceTracker algorithm is now fully integrated natively within Blender as a module inside the addon.
- **Removed Dear PyGui dependency**: You no longer need to open the external `.exe`. Everything happens in the 3D Viewport.
- **One-Click Installer**: Added automatic UI button to install Python tracking dependencies (`opencv` and `mediapipe`).
- **Live Preview Window**: Added a native UI pixel preview window straight to Blender UI, displaying tracking dots.
- **Embedded Target Management**: Target Groups, X/Y Landmark configurations, Tracking Limits and Filters are now directly tied and saved onto objects as part of Blender's native Addon `shape_xy_groups` settings.
- **Removed UDP Background Setup**: The pipeline uses Blender timers and memory to transfer capture 
