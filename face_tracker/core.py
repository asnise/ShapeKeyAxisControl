import bpy
import threading
import time
import math
import os

TRACKER_RUNNING = False
TRACKER_THREAD = None
CAMERA_PIXELS = None
CURRENT_CONFIG = {}
CURRENT_RESULTS = {}
FPS_STAT = "0"
RAW_VALUES = {"x": 0.0, "y": 0.0}
CURRENT_LANDMARKS = []

EYE_R = {"iris": 468, "inner": 133, "outer": 33, "top": 159, "bottom": 145}
EYE_L = {"iris": 473, "inner": 362, "outer": 263, "top": 386, "bottom": 374}

def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def normalize_value(val, radius_min, radius_max, out_min, out_max):
    if radius_max <= radius_min: return out_min
    if val <= radius_min: return out_min
    elif val >= radius_max: return out_max
    normalized = (val - radius_min) / (radius_max - radius_min)
    return out_min + (out_max - out_min) * normalized

def tracker_loop(cam_idx):
    global TRACKER_RUNNING, CAMERA_PIXELS, CURRENT_RESULTS, FPS_STAT, CURRENT_CONFIG, RAW_VALUES
    try:
        import cv2
        import numpy as np
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
    except ImportError:
        TRACKER_RUNNING = False
        return

    model_path = os.path.join(os.path.dirname(__file__), "assets", "face_landmarker.task")
    if not os.path.exists(model_path):
        TRACKER_RUNNING = False
        return

    try:
        landmarker = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO, output_face_blendshapes=True
        ))
    except Exception:
        TRACKER_RUNNING = False
        return

    cap = cv2.VideoCapture(cam_idx)
    if not cap.isOpened():
        TRACKER_RUNNING = False
        return

    last_t = time.time()
    iris_ema = {"R": {"x": 0.0, "y": 0.0}, "L": {"x": 0.0, "y": 0.0}}
    lerp_values = {}

    while TRACKER_RUNNING:
        success, raw_frame = cap.read()
        if not success:
            continue
            
        raw_frame = cv2.flip(raw_frame, 1)
        f_h, f_w = raw_frame.shape[:2]
        rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        results = landmarker.detect_for_video(mp_img, int(time.time() * 1000))
        
        payload = {}
        raw_out = {"x": 0.0, "y": 0.0}

        if results.face_landmarks:
            lms = results.face_landmarks[0]
            f_width = calculate_distance(lms[234], lms[454]) or 1.0
            fx_v = (lms[454].x-lms[234].x, lms[454].y-lms[234].y, lms[454].z-lms[234].z)
            fy_v = (lms[152].x-lms[10].x, lms[152].y-lms[10].y, lms[152].z-lms[10].z)
            
            cfg = CURRENT_CONFIG.copy()
            for gn, mapings in cfg.items():
                out_d = {"x": 0.0, "y": 0.0}
                for axis in ["x", "y"]:
                    m = mapings.get(axis, {})
                    mode = m.get("mode", "None")
                    ia = m.get("pt_a", 0)
                    ib = m.get("pt_b", 0)
                    
                    raw = 0.0
                    if mode == "None":
                        raw = 0.0
                    elif "iris" in mode:
                        ek = "L" if ib == EYE_L["outer"] or ib == EYE_L["top"] else "R"
                        e = EYE_L if ek == "L" else EYE_R
                        pa, pi, po = lms[e["iris"]], lms[e["inner"]], lms[e["outer"]]
                        pt, pb = lms[e["top"]], lms[e["bottom"]]
                        ew = abs(pi.x-po.x) or 1.0
                        eh = abs(pt.y-pb.y) or 0.1
                        if eh > 0.05 * ew:
                            if axis == "x":
                                inst = (pa.x - (pi.x+po.x)/2)/ew
                            else:
                                inst = (pa.y - (pt.y+pb.y)/2)/ew * 2.0
                            iris_ema[ek][axis] += 0.3 * (inst - iris_ema[ek][axis])
                        
                        raw = iris_ema[ek][axis]
                        pex = m.get("exp", 1.2)
                        raw = math.copysign(abs(raw)**pex, raw)
                    elif "1pt" in mode:
                        pa, pb = lms[ia], lms[ib]
                        vec = (pa.x-pb.x, pa.y-pb.y, pa.z-pb.z)
                        f_v = fx_v if axis=="x" else fy_v
                        dot = (vec[0]*f_v[0] + vec[1]*f_v[1] + vec[2]*f_v[2])
                        raw = (dot / f_width) * 10.0
                    elif "2pt" in mode:
                        raw = calculate_distance(lms[ia], lms[ib]) / f_width
                    
                    if gn == mapings.get("_active_group"):
                        raw_out[axis] = raw

                    rmin, rmax = m.get("rmin", 0.0), m.get("rmax", 1.0)
                    omin, omax = m.get("omin", 0.0), m.get("omax", 1.0)
                    
                    if "2pt" in mode: 
                        val = normalize_value(raw, rmin, rmax, omin, omax)
                    else: 
                        val = normalize_value(abs(raw), rmin, rmax, omin, omax) * math.copysign(1, raw)
                    
                    val *= m.get("sens", 1.0)
                    if m.get("lerp_en"):
                        lk = gn+axis
                        if lk not in lerp_values: lerp_values[lk] = val
                        lerp_values[lk] += (val - lerp_values[lk]) * m.get("lerp_fac", 0.15)
                        val = lerp_values[lk]
                    
                    out_d[axis] = max(-1.0, min(1.0, val))
                payload[gn] = out_d
            
            CURRENT_RESULTS = payload
            RAW_VALUES = raw_out
            CURRENT_LANDMARKS = [(lm.x, lm.y) for lm in lms]
            
            active_pts = set()
            for gn, mapings in cfg.items():
                for axis in ["x", "y"]:
                    m = mapings.get(axis, {})
                    mode = m.get("mode", "None")
                    ia = m.get("pt_a", 0)
                    ib = m.get("pt_b", 0)
                    if "iris" in mode:
                        ek = "L" if ib == EYE_L["outer"] or ib == EYE_L["top"] else "R"
                        e = EYE_L if ek == "L" else EYE_R
                        active_pts.update([e["iris"], e["inner"], e["outer"], e["top"], e["bottom"]])
                    elif "1pt" in mode or "2pt" in mode:
                        active_pts.update([ia, ib])
                        
            # Privacy mode: blank out actual video feed
            rgb = np.zeros_like(rgb)
            
            for i, lm in enumerate(lms):
                px, py = int(lm.x*f_w), int(lm.y*f_h)
                if i in active_pts:
                    # Highlight active tracker points in Red
                    cv2.circle(rgb, (px, py), 3, (255, 50, 50), -1)
                else:
                    cv2.circle(rgb, (px, py), 1, (0, 255, 100), -1)

        f_res = cv2.resize(rgb, (320, 240))
        rgba = cv2.cvtColor(f_res, cv2.COLOR_RGB2RGBA)
        rgba = cv2.flip(rgba, 0)
        CAMERA_PIXELS = (rgba.astype(np.float32) / 255.0).flatten()
        
        ctime = time.time()
        FPS_STAT = f"FPS: {int(1.0/max(ctime-last_t, 0.001))}"
        last_t = ctime

    cap.release()

def process_blender_timer():
    global TRACKER_RUNNING, CAMERA_PIXELS, CURRENT_RESULTS, CURRENT_CONFIG, RAW_VALUES
    if not TRACKER_RUNNING:
        return None

    cfg = {}
    
    if not hasattr(bpy.context.scene, "tracker_targets"):
        return 0.05
    
    # Loop over all global tracking targets defined by the user
    for target in bpy.context.scene.tracker_targets:
        obj = target.obj
        if obj and target.group_name and hasattr(obj, 'shape_xy_groups'):
            if target.group_name in obj.shape_xy_groups:
                g = obj.shape_xy_groups[target.group_name]
                uid = f"{obj.name}_{g.name}"
                
                cfg[uid] = {
                    "_active_group": uid, # Treat each as active to get raw values out
                    "x": {
                        "mode": g.tracker_x_mode, "pt_a": g.tracker_x_pt_a, "pt_b": g.tracker_x_pt_b,
                        "rmin": g.tracker_x_rmin, "rmax": g.tracker_x_rmax, "omin": g.tracker_x_omin,
                        "omax": g.tracker_x_omax, "sens": g.tracker_x_sens, "exp": g.tracker_x_exp,
                        "lerp_en": g.tracker_x_lerp_en, "lerp_fac": g.tracker_x_lerp_fac
                    },
                    "y": {
                        "mode": g.tracker_y_mode, "pt_a": g.tracker_y_pt_a, "pt_b": g.tracker_y_pt_b,
                        "rmin": g.tracker_y_rmin, "rmax": g.tracker_y_rmax, "omin": g.tracker_y_omin,
                        "omax": g.tracker_y_omax, "sens": g.tracker_y_sens, "exp": g.tracker_y_exp,
                        "lerp_en": g.tracker_y_lerp_en, "lerp_fac": g.tracker_y_lerp_fac
                    }
                }
    
    CURRENT_CONFIG = cfg

    res = CURRENT_RESULTS
    if res:
        from ..core.main import update_shapes, get_limit
        for target in bpy.context.scene.tracker_targets:
            obj = target.obj
            if obj and target.group_name and hasattr(obj, 'shape_xy_groups'):
                if target.group_name in obj.shape_xy_groups:
                    g = obj.shape_xy_groups[target.group_name]
                    uid = f"{obj.name}_{g.name}"
                    if uid in res:
                        g.joy_x = res[uid].get("x", g.joy_x)
                        g.joy_y = res[uid].get("y", g.joy_y)
                        limit = get_limit(g)
                        update_shapes(obj, g, limit)

    if CAMERA_PIXELS is not None:
        if "FaceTracker_Preview" in bpy.data.images:
            img = bpy.data.images["FaceTracker_Preview"]
            if img.size[0] == 320 and img.size[1] == 240:
                img.pixels.foreach_set(CAMERA_PIXELS)

    if hasattr(bpy.context.scene, "tracker_fps_status"):
        bpy.context.scene.tracker_fps_status = FPS_STAT
        bpy.context.scene.tracker_raw_x = RAW_VALUES.get("x", 0.0)
        bpy.context.scene.tracker_raw_y = RAW_VALUES.get("y", 0.0)

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

    return 0.05

def start_tracker(cam_idx=0):
    global TRACKER_RUNNING, TRACKER_THREAD
    if TRACKER_RUNNING:
        return
        
    if "FaceTracker_Preview" not in bpy.data.images:
        bpy.data.images.new("FaceTracker_Preview", width=320, height=240, alpha=True)
        
    TRACKER_RUNNING = True
    TRACKER_THREAD = threading.Thread(target=tracker_loop, args=(cam_idx,), daemon=True)
    TRACKER_THREAD.start()
    bpy.app.timers.register(process_blender_timer)

def stop_tracker():
    global TRACKER_RUNNING
    TRACKER_RUNNING = False

def register():
    bpy.types.Scene.tracker_fps_status = bpy.props.StringProperty(default="Stopped")
    bpy.types.Scene.tracker_raw_x = bpy.props.FloatProperty()
    bpy.types.Scene.tracker_raw_y = bpy.props.FloatProperty()
    bpy.types.Scene.tracker_cam_index = bpy.props.IntProperty(name="Camera Index", default=0, min=0)

def unregister():
    stop_tracker()
    if hasattr(bpy.types.Scene, "tracker_fps_status"):
        del bpy.types.Scene.tracker_fps_status
        del bpy.types.Scene.tracker_raw_x
        del bpy.types.Scene.tracker_raw_y
        del bpy.types.Scene.tracker_cam_index
