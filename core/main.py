import bpy
import math

def get_active_group(obj):
    if obj and hasattr(obj, 'bone_xy_groups') and len(obj.bone_xy_groups) > 0:
        idx = obj.bone_xy_group_index
        if 0 <= idx < len(obj.bone_xy_groups):
            return obj.bone_xy_groups[idx]
    return None

def get_limit(group):
    if group and hasattr(group, 'bone_xy_list') and len(group.bone_xy_list) > 0:
        return max([abs(item.target_x) for item in group.bone_xy_list] + [abs(item.target_y) for item in group.bone_xy_list] + [1.0])
    return 1.0

def update_transforms(obj, group, limit):
    val_x = group.joy_x * limit
    val_y = group.joy_y * limit
    
    transform_deltas = {}

    for item in group.bone_xy_list:
        target_key = (item.target_type, item.bone_name, item.prop_type, int(item.axis_index))
        
        mode = item.blend_mode
        if mode == 'AUTO':
            is_x = abs(item.target_y) < 0.001 and abs(item.target_x) > 0.001
            is_y = abs(item.target_x) < 0.001 and abs(item.target_y) > 0.001
            if is_x:
                mode = 'AXIS_X'
            elif is_y:
                mode = 'AXIS_Y'
            else:
                mode = 'BOX'
        
        if mode == 'AXIS_X':
            dist = abs(val_x - item.target_x)
        elif mode == 'AXIS_Y':
            dist = abs(val_y - item.target_y)
        elif mode == 'BOX':
            dist = max(abs(val_x - item.target_x), abs(val_y - item.target_y))
        else:
            dist = math.hypot(val_x - item.target_x, val_y - item.target_y)

        weight = max(0.0, 1.0 - (dist / item.radius)) if item.radius > 0 else 0.0
        
        # Accumulate the delta
        if target_key not in transform_deltas:
            transform_deltas[target_key] = 0.0
        transform_deltas[target_key] += weight * item.max_value
        
    for key, delta in transform_deltas.items():
        t_type, b_name, p_type, a_index = key
        
        target = None
        if t_type == 'BONE' and obj.type == 'ARMATURE':
            if b_name and b_name in obj.pose.bones:
                target = obj.pose.bones[b_name]
        elif t_type == 'OBJECT':
            target = obj
            
        if target:
            if p_type == 'LOCATION':
                target.location[a_index] = delta
            elif p_type == 'ROTATION':
                target.rotation_euler[a_index] = delta
            elif p_type == 'SCALE':
                # Base scale is typically 1.0, so base 0.0 logic means: scale = 1.0 + delta
                # But to keep it consistent with translation, the user might expect it to act directly.
                # However, scale 0 is bad. We map delta from 0 base to 1.0 scale base?
                # The user will set max_value to the absolute added scale. So base is 1.0.
                # Wait, if we use 0.0 base for delta, Scale should probably be 1.0 + delta.
                target.scale[a_index] = 1.0 + delta


