import bpy
import socket
import threading
import queue
import json
from ..core.main import update_transforms, get_limit

TRACKER_QUEUE = queue.Queue()
TRACKER_THREAD = None
TRACKER_SOCKET = None
TRACKER_RUNNING = False

def udp_server_thread(port):
    global TRACKER_SOCKET, TRACKER_RUNNING
    try:
        TRACKER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        TRACKER_SOCKET.bind(("0.0.0.0", port))
        TRACKER_SOCKET.settimeout(1.0)
    except Exception as e:
        print(f"ShapeKey Tracker Error: {e}")
        TRACKER_RUNNING = False
        return

    while TRACKER_RUNNING:
        try:
            data, addr = TRACKER_SOCKET.recvfrom(1024)
            message = json.loads(data.decode('utf-8'))
            
            # Check for special commands like GET_GROUPS
            if "type" in message and message["type"] == "GET_GROUPS":
                TRACKER_QUEUE.put({"_GET_GROUPS_REQUEST_": addr})
                continue

            # Support old format {"x": 0.5, "y": 0.2} and new format {"Mouth": {"x": 0.5, "y": 0.2}}
            elif "x" in message and "y" in message:
                TRACKER_QUEUE.put({"_ACTIVE_GROUP_": {"x": float(message["x"]), "y": float(message["y"])}})
            else:
                # Expecting dictionary of groups
                parsed_msg = {}
                for k, v in message.items():
                    if isinstance(v, dict) and "x" in v and "y" in v:
                        parsed_msg[k] = {"x": float(v["x"]), "y": float(v["y"])}
                if parsed_msg:
                    TRACKER_QUEUE.put(parsed_msg)
        except socket.timeout:
            continue
        except Exception as e:
            # Ignore malformed JSON or other unexpected data
            pass

    try:
        TRACKER_SOCKET.close()
    except:
        pass

def process_tracker_queue():
    if not TRACKER_RUNNING:
        return None  # Stop blender timer

    if not TRACKER_QUEUE.empty():
        # Consume all to get the most recent message (avoids lag)
        latest_msg = None
        while not TRACKER_QUEUE.empty():
            latest_msg = TRACKER_QUEUE.get()
        
        if latest_msg:
            # Check context
            if getattr(bpy.context, "scene", None) and hasattr(bpy.context.scene, "objects"):
                for obj in bpy.data.objects:
                    if hasattr(obj, 'bone_xy_groups') and getattr(obj, "bone_xy_groups", None):
                        
                        # Handle GET_GROUPS request
                        if "_GET_GROUPS_REQUEST_" in latest_msg:
                            addr = latest_msg["_GET_GROUPS_REQUEST_"]
                            groups_set = set()
                            for o in bpy.data.objects:
                                if hasattr(o, 'bone_xy_groups') and getattr(o, "bone_xy_groups", None):
                                    for g in o.bone_xy_groups:
                                        groups_set.add(f"{o.name}_{g.name}")
                            
                            # Send back via socket
                            if TRACKER_SOCKET:
                                try:
                                    response = json.dumps({"type": "GROUPS", "groups": list(groups_set)})
                                    TRACKER_SOCKET.sendto(response.encode('utf-8'), addr)
                                except Exception as e:
                                    print(f"Error sending groups: {e}")
                            
                            continue # Process next object (though this handles all objects globally really, but safe to continue)
                        
                        # Handle legacy single tracking for active group
                        elif "_ACTIVE_GROUP_" in latest_msg:
                            index = obj.bone_xy_group_index
                            if 0 <= index < len(obj.bone_xy_groups):
                                group = obj.bone_xy_groups[index]
                                group.joy_x = max(-1.0, min(1.0, latest_msg["_ACTIVE_GROUP_"]["x"]))
                                group.joy_y = max(-1.0, min(1.0, latest_msg["_ACTIVE_GROUP_"]["y"]))
                                limit = get_limit(group)
                                update_transforms(obj, group, limit)
                        
                        # Handle multi-group dictionary payload
                        else:
                            for group in obj.bone_xy_groups:
                                group_id = f"{obj.name}_{group.name}"
                                if group_id in latest_msg:
                                    group.joy_x = max(-1.0, min(1.0, latest_msg[group_id]["x"]))
                                    group.joy_y = max(-1.0, min(1.0, latest_msg[group_id]["y"]))
                                    limit = get_limit(group)
                                    update_transforms(obj, group, limit)

    return 0.05  # Run 20 times a second

def start_tracker(port):
    global TRACKER_THREAD, TRACKER_RUNNING
    if TRACKER_RUNNING:
        return
    TRACKER_RUNNING = True
    TRACKER_THREAD = threading.Thread(target=udp_server_thread, args=(port,), daemon=True)
    TRACKER_THREAD.start()
    
    # Clear queue
    while not TRACKER_QUEUE.empty():
        TRACKER_QUEUE.get()
        
    bpy.app.timers.register(process_tracker_queue)

def stop_tracker():
    global TRACKER_RUNNING
    TRACKER_RUNNING = False

class bone_xy_OT_tracker_start(bpy.types.Operator):
    bl_idname = "bone_xy.tracker_start"
    bl_label = "Start Tracker"
    bl_description = "Start listening for external tracker input on the specified UDP port"
    
    def execute(self, context):
        port = context.scene.bone_xy_tracker_port
        start_tracker(port)
        return {'FINISHED'}

class bone_xy_OT_tracker_stop(bpy.types.Operator):
    bl_idname = "bone_xy.tracker_stop"
    bl_label = "Stop Tracker"
    bl_description = "Stop listening for tracker input"
    
    def execute(self, context):
        stop_tracker()
        return {'FINISHED'}

def is_tracker_running():
    return TRACKER_RUNNING

def register():
    bpy.utils.register_class(bone_xy_OT_tracker_start)
    bpy.utils.register_class(bone_xy_OT_tracker_stop)
    bpy.types.Scene.bone_xy_tracker_port = bpy.props.IntProperty(
        name="Port", default=5000, min=1024, max=65535,
        description="UDP Port to listen for tracking data"
    )

def unregister():
    stop_tracker()
    bpy.utils.unregister_class(bone_xy_OT_tracker_start)
    bpy.utils.unregister_class(bone_xy_OT_tracker_stop)
    if hasattr(bpy.types.Scene, "bone_xy_tracker_port"):
        del bpy.types.Scene.bone_xy_tracker_port


