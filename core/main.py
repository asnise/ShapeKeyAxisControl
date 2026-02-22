import bpy
import math

def get_active_group(obj):
    if obj and hasattr(obj, 'shape_xy_groups') and len(obj.shape_xy_groups) > 0:
        idx = obj.shape_xy_group_index
        if 0 <= idx < len(obj.shape_xy_groups):
            return obj.shape_xy_groups[idx]
    return None

def get_limit(group):
    if group and hasattr(group, 'shape_xy_list') and len(group.shape_xy_list) > 0:
        return max([abs(item.target_x) for item in group.shape_xy_list] + [abs(item.target_y) for item in group.shape_xy_list] + [1.0])
    return 1.0

def update_shapes(obj, group, limit):
    val_x = group.joy_x * limit
    val_y = group.joy_y * limit
    
    if obj and obj.type == 'MESH' and obj.data and hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
        shape_values = {}
        
        for item in group.shape_xy_list:
            if item.shape_name:
                shape_values[item.shape_name] = 0.0

        for item in group.shape_xy_list:
            if item.shape_name in obj.data.shape_keys.key_blocks:
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

                val = max(0.0, 1.0 - (dist / item.radius)) if item.radius > 0 else 0.0
                shape_values[item.shape_name] = max(shape_values.get(item.shape_name, 0.0), val)
                
        updated = False
        for sk_name, val in shape_values.items():
            if sk_name in obj.data.shape_keys.key_blocks:
                sk = obj.data.shape_keys.key_blocks[sk_name]
                if abs(sk.value - val) > 0.0001:
                    sk.value = val
                    updated = True
                    
        if updated:
            obj.data.update()
