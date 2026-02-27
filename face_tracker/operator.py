import bpy
from .core import start_tracker, stop_tracker, TRACKER_RUNNING
import os

def get_tracker_settings_group(context):
    idx = context.scene.tracker_target_index
    if not hasattr(context.scene, "tracker_targets") or idx < 0 or idx >= len(context.scene.tracker_targets):
        return None
    target = context.scene.tracker_targets[idx]
    obj = target.obj
    if obj and target.group_name and hasattr(obj, 'shape_xy_groups') and target.group_name in obj.shape_xy_groups:
        return obj.shape_xy_groups[target.group_name]
    return None

class SHAPE_XY_OT_tracker_native_start(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_native_start"
    bl_label = "Start Face Tracker"
    bl_description = "Start the built-in webcam face tracker"
    
    def execute(self, context):
        idx = context.scene.tracker_cam_index
        start_tracker(idx)
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_native_stop(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_native_stop"
    bl_label = "Stop Face Tracker"
    bl_description = "Stop the face tracker"
    
    def execute(self, context):
        stop_tracker()
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_open_map(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_open_map"
    bl_label = "Open Feature Map"
    bl_description = "View the point reference map"
    
    def execute(self, context):
        path = os.path.join(os.path.dirname(__file__), "assets", "face_mesh.png")
        if os.path.exists(path):
            if os.name == 'nt':
                os.startfile(path)
            else:
                import subprocess
                subprocess.call(["xdg-open", path])
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_cal_min_x(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_cal_min_x"
    bl_label = "Cal Min X"
    def execute(self, context):
        group = get_tracker_settings_group(context)
        if group:
            group.tracker_x_rmin = abs(context.scene.tracker_raw_x)
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_cal_max_x(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_cal_max_x"
    bl_label = "Cal Max X"
    def execute(self, context):
        group = get_tracker_settings_group(context)
        if group:
            group.tracker_x_rmax = abs(context.scene.tracker_raw_x)
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_cal_min_y(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_cal_min_y"
    bl_label = "Cal Min Y"
    def execute(self, context):
        group = get_tracker_settings_group(context)
        if group:
            group.tracker_y_rmin = abs(context.scene.tracker_raw_y)
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_cal_max_y(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_cal_max_y"
    bl_label = "Cal Max Y"
    def execute(self, context):
        group = get_tracker_settings_group(context)
        if group:
            group.tracker_y_rmax = abs(context.scene.tracker_raw_y)
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_apply_preset(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_apply_preset"
    bl_label = "Apply Tracking Preset"
    preset_type: bpy.props.StringProperty()
    
    def execute(self, context):
        group = get_tracker_settings_group(context)
        if not group:
            return {'CANCELLED'}
        
        if self.preset_type == "MOUTH":
            group.tracker_x_mode = '2pt (Dist)'
            group.tracker_x_pt_a = 291
            group.tracker_x_pt_b = 61
            group.tracker_x_rmin = 0.2935
            group.tracker_x_rmax = 0.3967
            group.tracker_x_omin = -1.0
            group.tracker_x_omax = 1.0
            group.tracker_x_sens = 1.0
            group.tracker_x_exp = 1.2
            group.tracker_y_mode = '2pt (Dist)'
            group.tracker_y_pt_a = 0
            group.tracker_y_pt_b = 16
            group.tracker_y_rmin = 0.0625
            group.tracker_y_rmax = 0.4397
            group.tracker_y_omin = -1.0
            group.tracker_y_omax = 1.0
            group.tracker_y_sens = 1.25
            group.tracker_y_exp = 1.2
            
        elif self.preset_type == "EYES":
            group.tracker_x_mode = 'iris'
            group.tracker_x_pt_a = 468
            group.tracker_x_pt_b = 33
            group.tracker_x_rmin = 0.02
            group.tracker_x_rmax = 0.25
            group.tracker_x_omin = 0.0
            group.tracker_x_omax = 1.0
            group.tracker_x_sens = 1.0
            group.tracker_x_exp = 0.75
            group.tracker_y_mode = 'iris'
            group.tracker_y_pt_a = 473
            group.tracker_y_pt_b = 386
            group.tracker_y_rmin = 0.02
            group.tracker_y_rmax = 0.25
            group.tracker_y_omin = 0.0
            group.tracker_y_omax = -1.0
            group.tracker_y_sens = 1.0
            group.tracker_y_exp = 1.2
            
        elif self.preset_type == "EYE_BLINK":
            group.tracker_x_mode = 'None'
            group.tracker_y_mode = '2pt (Dist)'
            group.tracker_y_pt_a = 374
            group.tracker_y_pt_b = 475
            group.tracker_y_rmin = 0.0415
            group.tracker_y_rmax = 0.1083
            group.tracker_y_omin = -1.0
            group.tracker_y_omax = 0.0
            group.tracker_y_sens = 1.5
            group.tracker_y_exp = 0.816
            
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_add_target(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_add_target"
    bl_label = "Add Target"
    def execute(self, context):
        context.scene.tracker_targets.add()
        context.scene.tracker_target_index = len(context.scene.tracker_targets) - 1
        return {'FINISHED'}

class SHAPE_XY_OT_tracker_remove_target(bpy.types.Operator):
    bl_idname = "shape_xy.tracker_remove_target"
    bl_label = "Remove Target"
    def execute(self, context):
        idx = context.scene.tracker_target_index
        if hasattr(context.scene, "tracker_targets") and 0 <= idx < len(context.scene.tracker_targets):
            context.scene.tracker_targets.remove(idx)
            context.scene.tracker_target_index = min(max(0, idx - 1), len(context.scene.tracker_targets) - 1)
        return {'FINISHED'}

classes = (
    SHAPE_XY_OT_tracker_native_start,
    SHAPE_XY_OT_tracker_native_stop,
    SHAPE_XY_OT_tracker_open_map,
    SHAPE_XY_OT_tracker_cal_min_x,
    SHAPE_XY_OT_tracker_cal_max_x,
    SHAPE_XY_OT_tracker_cal_min_y,
    SHAPE_XY_OT_tracker_cal_max_y,
    SHAPE_XY_OT_tracker_apply_preset,
    SHAPE_XY_OT_tracker_add_target,
    SHAPE_XY_OT_tracker_remove_target,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
