import bpy
import sys
import subprocess
import threading
import importlib

class SHAPE_XY_OT_report_message(bpy.types.Operator):
    bl_idname = "shape_xy.report_message"
    bl_label = "Report Message"
    
    message: bpy.props.StringProperty()
    msg_type: bpy.props.StringProperty(default="ERROR")

    def execute(self, context):
        self.report({self.msg_type}, self.message)
        return {'FINISHED'}

def trigger_report(msg, typ="ERROR"):
    # print to system console
    print(f"[Face Tracker] {typ}: {msg}")
    def _run():
        try:
            bpy.ops.shape_xy.report_message('EXEC_DEFAULT', message=str(msg)[:800], msg_type=typ)
        except Exception as e:
            print("Failed to report to Info Log:", e)
        return None
    if hasattr(bpy.app, "timers"):
        bpy.app.timers.register(_run, first_interval=0.1)

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
        # Ensure pip is installed
        subprocess.run([python_exe, "-m", "ensurepip"])
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Try installing without --user first, if it fails, try with --user
        result = subprocess.run([python_exe, "-m", "pip", "install", "opencv-python", "mediapipe"], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback to user installation in case of permission issues
            result = subprocess.run([python_exe, "-m", "pip", "install", "opencv-python", "mediapipe", "--user"], capture_output=True, text=True)
            
        if result.returncode == 0:
            bpy.context.scene.tracker_install_status = "Installed Successfully"
            trigger_report("Face Tracker Requirements Installed Successfully", "INFO")
        else:
            err = result.stderr.strip() if result.stderr else result.stdout.strip()
            # Show the last 200 characters of the error message for context
            short_err = err[-200:].replace('\n', ' ')
            bpy.context.scene.tracker_install_status = f"Failed. Check console. Err: {short_err}"
            print("--- PIP INSTALL FAILURE ---")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            trigger_report(f"PIP Install Failed: {short_err}", "ERROR")
            
    except Exception as e:
        bpy.context.scene.tracker_install_status = f"Error: {str(e)}"
        trigger_report(f"Installation Error: {str(e)}", "ERROR")

class SHAPE_XY_OT_install_deps(bpy.types.Operator):
    bl_idname = "shape_xy.install_deps"
    bl_label = "Install Face Tracker Requirements"
    
    def execute(self, context):
        thread = threading.Thread(target=install_dependencies_thread, daemon=True)
        thread.start()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(SHAPE_XY_OT_report_message)
    bpy.utils.register_class(SHAPE_XY_OT_install_deps)
    bpy.types.Scene.tracker_install_status = bpy.props.StringProperty(default="")

def unregister():
    bpy.utils.unregister_class(SHAPE_XY_OT_install_deps)
    bpy.utils.unregister_class(SHAPE_XY_OT_report_message)
    del bpy.types.Scene.tracker_install_status
