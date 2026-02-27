import bpy
import math
import json
import os
from bpy_extras.io_utils import ExportHelper, ImportHelper
from ..core.state import HUD_STATE
from ..core.main import get_active_group, get_limit, update_shapes
from ..ui.draw import draw_hud

class SHAPE_XY_OT_edit_values(bpy.types.Operator):
    bl_idname = "shape_xy.edit_values"
    bl_label = "Edit X and Y Values"
    bl_description = "Manually input exact X and Y coordinates for the current group's joystick"
    bl_options = {'REGISTER', 'UNDO'}

    input_x: bpy.props.FloatProperty(name="X Value")
    input_y: bpy.props.FloatProperty(name="Y Value")

    def invoke(self, context, event):
        obj = context.active_object
        group = get_active_group(obj)
        if not group:
            return {'CANCELLED'}
        limit = get_limit(group)
        self.input_x = group.joy_x * limit
        self.input_y = group.joy_y * limit
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if group:
            limit = get_limit(group)
            group.joy_x = max(-1.0, min(1.0, self.input_x / limit))
            group.joy_y = max(-1.0, min(1.0, self.input_y / limit))
            update_shapes(obj, group, limit)
            context.area.tag_redraw()
        return {'FINISHED'}

class SHAPE_XY_OT_reset_handle(bpy.types.Operator):
    bl_idname = "shape_xy.reset_handle"
    bl_label = "Reset Handle"
    bl_description = "Reset the joystick handle of the active group to center (0.0, 0.0)"
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if group:
            group.joy_x = 0.0
            group.joy_y = 0.0
            update_shapes(obj, group, get_limit(group))
            context.area.tag_redraw()
        return {'FINISHED'}

class SHAPE_XY_OT_reset_all(bpy.types.Operator):
    bl_idname = "shape_xy.reset_all"
    bl_label = "Reset All Handles"
    bl_description = "Reset ALL joystick handles across EVERY group and EVERY object back to center (0.0, 0.0)"
    
    def execute(self, context):
        for obj in context.scene.objects:
            if hasattr(obj, 'shape_xy_groups'):
                for group in obj.shape_xy_groups:
                    group.joy_x = 0.0
                    group.joy_y = 0.0
                    update_shapes(obj, group, get_limit(group))
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {'FINISHED'}

class SHAPE_XY_OT_keyframe_handle(bpy.types.Operator):
    bl_idname = "shape_xy.keyframe_handle"
    bl_label = "Keyframe Handle"
    bl_description = "Insert keyframes for the current group's joystick handle at the current frame"
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if group:
            group.keyframe_insert(data_path="joy_x")
            group.keyframe_insert(data_path="joy_y")
            self.report({'INFO'}, "Keyframes inserted for Handle")
        return {'FINISHED'}


class SHAPE_XY_OT_bake_animation(bpy.types.Operator):
    bl_idname = "shape_xy.bake_animation"
    bl_label = "Bake Animation to Shape Keys"
    bl_description = "Bake the animated joystick logic into raw Shape Key keyframes for exporting (e.g. FBX/GLTF)"
    bl_options = {'REGISTER', 'UNDO'}
    
    start_frame: bpy.props.IntProperty(name="Start Frame", default=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=250)
    step: bpy.props.IntProperty(name="Step", default=1, min=1)
    
    def invoke(self, context, event):
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end
        return context.window_manager.invoke_props_dialog(self)
        
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if not group or not hasattr(group, 'shape_xy_list'):
            return {'CANCELLED'}
            
        original_frame = context.scene.frame_current
        
        # Prepare shapekeys
        if not obj.data or not hasattr(obj.data, 'shape_keys') or not obj.data.shape_keys:
            self.report({'ERROR'}, "Object has no Shape Keys")
            return {'CANCELLED'}
            
        shape_names = [item.shape_name for item in group.shape_xy_list if item.shape_name in obj.data.shape_keys.key_blocks]
        if not shape_names:
            self.report({'ERROR'}, "No valid Shape Keys mapped in this group")
            return {'CANCELLED'}
            
        limit = get_limit(group)
        
        count = 0
        for f in range(self.start_frame, self.end_frame + 1, self.step):
            context.scene.frame_set(f)
            # The frame_change_post handler should auto update the shapes based on joy_x/y
            # But just in case, we also explicitly enforce the update here
            update_shapes(obj, group, limit)
            
            for name in shape_names:
                sk = obj.data.shape_keys.key_blocks[name]
                sk.keyframe_insert(data_path="value", frame=f)
                count += 1
                
        # Restore original frame
        context.scene.frame_set(original_frame)
        self.report({'INFO'}, f"Baked {count} keyframes from frame {self.start_frame} to {self.end_frame}")
        return {'FINISHED'}

class SHAPE_XY_OT_export_group(bpy.types.Operator, ExportHelper):
    bl_idname = "shape_xy.export_group"
    bl_label = "Export Group Settings"
    bl_description = "Export the current ShapeKey Group's mappings to a JSON file"
    
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if not group or not hasattr(group, 'shape_xy_list'):
            return {'CANCELLED'}
            
        data = {
            "group_name": group.name,
            "mappings": []
        }
        
        for item in group.shape_xy_list:
            if item.shape_name:
                data["mappings"].append({
                    "name": item.shape_name,
                    "target_x": item.target_x,
                    "target_y": item.target_y,
                    "radius": item.radius,
                    "blend_mode": item.blend_mode
                })
                
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        self.report({'INFO'}, f"Exported {len(data['mappings'])} mappings")
        return {'FINISHED'}

class SHAPE_XY_OT_import_group(bpy.types.Operator, ImportHelper):
    bl_idname = "shape_xy.import_group"
    bl_label = "Import Group Settings"
    bl_description = "Import ShapeKey Group mappings from a JSON file"
    
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, 'shape_xy_groups'):
            return {'CANCELLED'}
            
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}
            
        if "mappings" not in data:
            self.report({'ERROR'}, "Invalid JSON format")
            return {'CANCELLED'}
            
        # Create a new group for the imported data
        group = obj.shape_xy_groups.add()
        group.name = data.get("group_name", "Imported Group")
        obj.shape_xy_group_index = len(obj.shape_xy_groups) - 1
        
        count = 0
        for info in data["mappings"]:
            item = group.shape_xy_list.add()
            item.shape_name = info.get("name", "")
            item.target_x = info.get("target_x", 1.0)
            item.target_y = info.get("target_y", 0.0)
            item.radius = info.get("radius", 1.0)
            item.blend_mode = info.get("blend_mode", 'AUTO')
            count += 1
            
        self.report({'INFO'}, f"Imported new group with {count} mappings")
        return {'FINISHED'}

class SHAPE_XY_OT_reset_hud(bpy.types.Operator):
    bl_idname = "shape_xy.reset_hud"
    bl_label = "Reset Modal HUD"
    bl_description = "Reset the Axis UI position to default if it goes out of screen"
    
    def execute(self, context):
        HUD_STATE["x"] = 50
        HUD_STATE["y"] = 120
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {'FINISHED'}

class SHAPE_XY_OT_ui_joystick(bpy.types.Operator):
    bl_idname = "shape_xy.ui_joystick"
    bl_label = "Toggle Axis UI"
    bl_description = "Start or Stop the interactive 2D HUD Axis Controller in the 3D Viewport"
    
    def modal(self, context, event):
        if not HUD_STATE["running"]:
            self.finish(context)
            return {'CANCELLED'}
            
        if not context.area:
            return {'PASS_THROUGH'}
            
        window_region = None
        for region in context.area.regions:
            if region.type == 'WINDOW':
                window_region = region
                break
                
        if not window_region:
            return {'PASS_THROUGH'}
            
        is_in_window = (window_region.x <= event.mouse_x <= window_region.x + window_region.width and
                        window_region.y <= event.mouse_y <= window_region.y + window_region.height)
        
        x, y, size = HUD_STATE["x"], HUD_STATE["y"], HUD_STATE["size"]
        
        obj = context.active_object
        group = get_active_group(obj)
        limit = get_limit(group) if group else 1.0
        
        # Object Auto-refresh mechanism
        obj_name = obj.name if obj else ""
        group_name = group.name if group else ""
        last_obj = HUD_STATE.get("last_obj_name", "")
        last_grp = HUD_STATE.get("last_group_name", "")
        
        if obj_name != last_obj or group_name != last_grp:
            HUD_STATE["last_obj_name"] = obj_name
            HUD_STATE["last_group_name"] = group_name
            if group:
                update_shapes(obj, group, limit)
            context.area.tag_redraw()
            
        is_in_window = (window_region.x <= event.mouse_x <= window_region.x + window_region.width and
                        window_region.y <= event.mouse_y <= window_region.y + window_region.height)
        
        x, y, size = HUD_STATE["x"], HUD_STATE["y"], HUD_STATE["size"]
        
        obj = context.active_object
        group = get_active_group(obj)
        limit = get_limit(group) if group else 1.0

        if is_in_window:
            mx = event.mouse_x - window_region.x
            my = event.mouse_y - window_region.y
            in_joy = (x <= mx <= x + size) and (y <= my <= y + size)
            in_header = (x <= mx <= x + size) and (y + size <= my <= y + size + 25)
            in_reset = (x <= mx <= x + size) and (y - 35 <= my <= y - 5)
            in_edit  = (x <= mx <= x + size) and (y - 75 <= my <= y - 40)
            in_prev_group = (x <= mx <= x + 30) and (y - 105 <= my <= y - 80)
            in_next_group = (x + size - 30 <= mx <= x + size) and (y - 105 <= my <= y - 80)
        else:
            mx = event.mouse_region_x
            my = event.mouse_region_y
            in_joy = False
            in_header = False
            in_reset = False
            in_edit = False
            in_prev_group = False
            in_next_group = False

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                if is_in_window and obj and obj.type == 'MESH' and group and hasattr(group, 'shape_xy_list') and context.scene.shape_xy_allow_drag:
                    cx, cy = x + size/2, y + size/2
                    for idx, item in enumerate(group.shape_xy_list):
                        px = cx + (item.target_x / limit) * (size/2)
                        py = cy + (item.target_y / limit) * (size/2)
                        if math.hypot(mx - px, my - py) < 12:
                            HUD_STATE["dragging_target_idx"] = idx
                            HUD_STATE["drag_start_limit"] = limit
                            return {'RUNNING_MODAL'}

                if in_header:
                    HUD_STATE["dragging_hud"] = True
                    HUD_STATE["drag_offset_x"] = mx - x
                    HUD_STATE["drag_offset_y"] = my - y
                    return {'RUNNING_MODAL'}
                elif in_joy and group:
                    HUD_STATE["dragging"] = True
                    return {'RUNNING_MODAL'}
                elif in_reset:
                    bpy.ops.shape_xy.reset_handle()
                    return {'RUNNING_MODAL'}
                elif in_edit:
                    bpy.ops.shape_xy.edit_values('INVOKE_DEFAULT')
                    return {'RUNNING_MODAL'}
                elif in_prev_group and obj and hasattr(obj, 'shape_xy_groups') and obj.shape_xy_groups:
                    obj.shape_xy_group_index = (obj.shape_xy_group_index - 1) % len(obj.shape_xy_groups)
                    return {'RUNNING_MODAL'}
                elif in_next_group and obj and hasattr(obj, 'shape_xy_groups') and obj.shape_xy_groups:
                    obj.shape_xy_group_index = (obj.shape_xy_group_index + 1) % len(obj.shape_xy_groups)
                    return {'RUNNING_MODAL'}

        # I-key shortcut: insert keyframe for joy handle while hovering over HUD
        if event.type == 'I' and event.value == 'PRESS':
            if is_in_window and group:
                hud_bound = (x - 4 <= mx <= x + size + 4) and (y - 112 <= my <= y + size + 25)
                if hud_bound:
                    bpy.ops.shape_xy.keyframe_handle()
                    return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            HUD_STATE["dragging"] = False
            HUD_STATE["dragging_hud"] = False
            HUD_STATE["dragging_target_idx"] = -1
            context.area.tag_redraw()
        
        if event.type == 'MOUSEMOVE':
            if HUD_STATE.get("dragging_target_idx", -1) >= 0:
                idx = HUD_STATE["dragging_target_idx"]
                if group and 0 <= idx < len(group.shape_xy_list):
                    item = group.shape_xy_list[idx]
                    cx, cy = x + size/2, y + size/2
                    drag_limit = HUD_STATE.get("drag_start_limit", 1.0)
                    
                    new_tx = ((mx - cx) / (size/2)) * drag_limit
                    new_ty = ((my - cy) / (size/2)) * drag_limit
                    
                    new_tx = max(-drag_limit, min(drag_limit, new_tx))
                    new_ty = max(-drag_limit, min(drag_limit, new_ty))
                    
                    item.target_x = new_tx
                    item.target_y = new_ty
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            elif HUD_STATE.get("dragging_hud", False):
                HUD_STATE["x"] = mx - HUD_STATE["drag_offset_x"]
                HUD_STATE["y"] = my - HUD_STATE["drag_offset_y"]
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            elif HUD_STATE["dragging"] and group:
                cx = (mx - (x + size/2)) / (size/2)
                cy = (my - (y + size/2)) / (size/2)
                group.joy_x = max(-1.0, min(1.0, cx))
                group.joy_y = max(-1.0, min(1.0, cy))
                
                update_shapes(obj, group, limit)
                
                if context.scene.tool_settings.use_keyframe_insert_auto:
                    group.keyframe_insert(data_path="joy_x")
                    group.keyframe_insert(data_path="joy_y")
                
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
        
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if HUD_STATE["dragging"] or HUD_STATE.get("dragging_target_idx", -1) >= 0 or HUD_STATE.get("dragging_hud", False):
                HUD_STATE["dragging"] = False
                HUD_STATE["dragging_hud"] = False
                HUD_STATE["dragging_target_idx"] = -1
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
        
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if HUD_STATE["running"]:
            HUD_STATE["running"] = False
            return {'CANCELLED'}
        
        HUD_STATE["running"] = True
        HUD_STATE["handle"] = bpy.types.SpaceView3D.draw_handler_add(draw_hud, (), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    def finish(self, context):
        if HUD_STATE["handle"]:
            bpy.types.SpaceView3D.draw_handler_remove(HUD_STATE["handle"], 'WINDOW')
            HUD_STATE["handle"] = None

class SHAPE_XY_OT_move_item(bpy.types.Operator):
    bl_idname = "shape_xy.move_item"
    bl_label = "Move Mapping"
    bl_description = "Move the selected ShapeKey mapping up or down in the list"
    
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ''), ('DOWN', 'Down', '')))
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if group and hasattr(group, 'shape_xy_list'):
            idx = group.shape_xy_index
            new_idx = idx + (-1 if self.direction == 'UP' else 1)
            if 0 <= new_idx < len(group.shape_xy_list):
                group.shape_xy_list.move(idx, new_idx)
                group.shape_xy_index = new_idx
        return {'FINISHED'}

class SHAPE_XY_OT_mirror_mappings(bpy.types.Operator):
    bl_idname = "shape_xy.mirror_mappings"
    bl_label = "Mirror Mappings"
    bl_description = "Automatically generate symmetrical ShapeKey mappings for .L / .R suffixes"
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if not group or not hasattr(group, 'shape_xy_list'):
            return {'CANCELLED'}
            
        new_items = []
        for item in group.shape_xy_list:
            name = item.shape_name
            if not name:
                continue
                
            mirrored_name = None
            if name.endswith('.L'): mirrored_name = name[:-2] + '.R'
            elif name.endswith('.R'): mirrored_name = name[:-2] + '.L'
            elif name.endswith('_L'): mirrored_name = name[:-2] + '_R'
            elif name.endswith('_R'): mirrored_name = name[:-2] + '_L'
            elif name.endswith(' L'): mirrored_name = name[:-2] + ' R'
            elif name.endswith(' R'): mirrored_name = name[:-2] + ' L'
            
            # Check if this mirrored shapekey actually exists on the mesh
            if mirrored_name and obj.data and hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                if mirrored_name in obj.data.shape_keys.key_blocks:
                    # Check if it's already mapped in this group
                    already_exists = any(mapped.shape_name == mirrored_name for mapped in group.shape_xy_list)
                    if not already_exists:
                        # Prepare mapping info, flipping the target_x across the Y axis
                        new_items.append({
                            'name': mirrored_name,
                            'target_x': -item.target_x,
                            'target_y': item.target_y,
                            'radius': item.radius,
                            'blend_mode': item.blend_mode
                        })
                        
        count = 0
        for info in new_items:
            new_item = group.shape_xy_list.add()
            new_item.shape_name = info['name']
            new_item.target_x = info['target_x']
            new_item.target_y = info['target_y']
            new_item.radius = info['radius']
            new_item.blend_mode = info['blend_mode']
            count += 1
            
        group.shape_xy_index = len(group.shape_xy_list) - 1
        self.report({'INFO'}, f"Auto-Mirrored {count} ShapeKeys")
        return {'FINISHED'}

class SHAPE_XY_OT_move_group(bpy.types.Operator):
    bl_idname = "shape_xy.move_group"
    bl_label = "Move Group"
    bl_description = "Move the selected ShapeKey Group up or down in the list"
    
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ''), ('DOWN', 'Down', '')))
    
    def execute(self, context):
        obj = context.active_object
        if obj and hasattr(obj, 'shape_xy_groups'):
            idx = obj.shape_xy_group_index
            new_idx = idx + (-1 if self.direction == 'UP' else 1)
            if 0 <= new_idx < len(obj.shape_xy_groups):
                obj.shape_xy_groups.move(idx, new_idx)
                obj.shape_xy_group_index = new_idx
        return {'FINISHED'}

class SHAPE_XY_OT_move_preset(bpy.types.Operator):
    bl_idname = "shape_xy.move_preset"
    bl_label = "Move Preset"
    bl_description = "Move the selected Global Animation Preset up or down in the list"
    
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ''), ('DOWN', 'Down', '')))
    
    def execute(self, context):
        presets = context.scene.shape_xy_presets
        idx = context.scene.shape_xy_preset_index
        new_idx = idx + (-1 if self.direction == 'UP' else 1)
        if 0 <= new_idx < len(presets):
            presets.move(idx, new_idx)
            context.scene.shape_xy_preset_index = new_idx
        return {'FINISHED'}

class SHAPE_XY_OT_add_preset(bpy.types.Operator):
    bl_idname = "shape_xy.add_preset"
    bl_label = "Add Global Preset"
    bl_description = "Create a new Global Animation Preset"
    
    def execute(self, context):
        presets = context.scene.shape_xy_presets
        preset = presets.add()
        preset.name = f"Preset {len(presets)}"
        context.scene.shape_xy_preset_index = len(presets) - 1
        return {'FINISHED'}

class SHAPE_XY_OT_remove_preset(bpy.types.Operator):
    bl_idname = "shape_xy.remove_preset"
    bl_label = "Remove Global Preset"
    bl_description = "Delete the currently selected Global Animation Preset"
    
    def execute(self, context):
        presets = context.scene.shape_xy_presets
        idx = context.scene.shape_xy_preset_index
        if presets:
            presets.remove(idx)
            if len(presets) > 0:
                context.scene.shape_xy_preset_index = min(max(0, idx - 1), len(presets) - 1)
        return {'FINISHED'}

class SHAPE_XY_OT_set_preset(bpy.types.Operator):
    bl_idname = "shape_xy.set_preset"
    bl_label = "Set Global Preset"
    bl_description = "Snapshot current joystick coordinates of ALL groups across ALL objects into this preset"
    
    def execute(self, context):
        presets = context.scene.shape_xy_presets
        idx = context.scene.shape_xy_preset_index
        if 0 <= idx < len(presets):
            preset = presets[idx]
            preset.states.clear()
            
            for obj in context.scene.objects:
                if hasattr(obj, 'shape_xy_groups'):
                    for group in obj.shape_xy_groups:
                        state = preset.states.add()
                        state.obj_name = obj.name
                        state.group_name = group.name
                        state.joy_x = group.joy_x
                        state.joy_y = group.joy_y
        return {'FINISHED'}

class SHAPE_XY_OT_call_preset(bpy.types.Operator):
    bl_idname = "shape_xy.call_preset"
    bl_label = "Call Global Preset"
    bl_description = "Apply the saved joystick coordinates from this preset to ALL groups across ALL objects"
    
    def execute(self, context):
        presets = context.scene.shape_xy_presets
        idx = context.scene.shape_xy_preset_index
        if 0 <= idx < len(presets):
            preset = presets[idx]
            
            for state in preset.states:
                obj = context.scene.objects.get(state.obj_name)
                if obj and hasattr(obj, 'shape_xy_groups'):
                    group = obj.shape_xy_groups.get(state.group_name)
                    if group:
                        group.joy_x = state.joy_x
                        group.joy_y = state.joy_y
                        update_shapes(obj, group, get_limit(group))
            
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
        return {'FINISHED'}

class SHAPE_XY_OT_keyframe_preset(bpy.types.Operator):
    bl_idname = "shape_xy.keyframe_preset"
    bl_label = "Insert Keyframe for Global Preset"
    bl_description = "Call this preset and immediately insert keyframes for all affected shapekeys"
    
    def execute(self, context):
        presets = context.scene.shape_xy_presets
        idx = context.scene.shape_xy_preset_index
        if 0 <= idx < len(presets):
            preset = presets[idx]
            
            # Step 1: Call the Preset to update values
            for state in preset.states:
                obj = context.scene.objects.get(state.obj_name)
                if obj and hasattr(obj, 'shape_xy_groups'):
                    group = obj.shape_xy_groups.get(state.group_name)
                    if group:
                        group.joy_x = state.joy_x
                        group.joy_y = state.joy_y
                        update_shapes(obj, group, get_limit(group))
                        
                        # Step 2: Keyframe all affected shapekeys for this object
                        if obj.data and hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                            for item in group.shape_xy_list:
                                if item.shape_name in obj.data.shape_keys.key_blocks:
                                    sk = obj.data.shape_keys.key_blocks[item.shape_name]
                                    sk.keyframe_insert(data_path="value")
            
            # Refresh Viewport
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
        return {'FINISHED'}
