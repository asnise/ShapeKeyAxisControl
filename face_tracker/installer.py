import bpy
import sys
import subprocess
import threading
import importlib

def is_installed(package_name):
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def check_dependencies():
    return is_installed('cv2') and is_installed('mediapipe')

def install_dependencies_thread():
    if not hasattr(bpy.context, "scene"):
        return
    bpy.context.scene.tracker_install_status = "Installing (May take a few minutes)..."
    python_exe = sys.executable
    try:
        subprocess.check_call([python_exe, "-m", "pip", "install", "opencv-python", "mediapipe"])
        bpy.context.scene.tracker_install_status = "Installed Successfully"
    except Exception as e:
        bpy.context.scene.tracker_install_status = f"Error: {str(e)}"

class SHAPE_XY_OT_install_deps(bpy.types.Operator):
    bl_idname = "shape_xy.install_deps"
    bl_label = "Install Face Tracker Requirements"
    
    def execute(self, context):
        thread = threading.Thread(target=install_dependencies_thread, daemon=True)
        thread.start()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(SHAPE_XY_OT_install_deps)
    bpy.types.Scene.tracker_install_status = bpy.props.StringProperty(default="")

def unregister():
    bpy.utils.unregister_class(SHAPE_XY_OT_install_deps)
    del bpy.types.Scene.tracker_install_status
