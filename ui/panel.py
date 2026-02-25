import bpy
from ..core.state import HUD_STATE
from ..core.main import get_active_group
from ..interface.tracker import is_tracker_running

class bone_xy_UL_group_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name, icon='GROUP')

class bone_xy_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        name_str = item.bone_name if item.target_type == 'BONE' else "Object"
        axis_str = "X" if item.axis_index == '0' else ("Y" if item.axis_index == '1' else "Z")
        layout.label(text=f"{name_str} [{item.prop_type} {axis_str}]")
        layout.label(text=f"X:{item.target_x:.1f} Y:{item.target_y:.1f}")

class bone_xy_UL_preset_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name, icon='USER')

class bone_xy_OT_add_group(bpy.types.Operator):
    bl_idname = "bone_xy.add_group"
    bl_label = "Add Group"
    bl_description = "Create a new ShapeKey Control Group for the active object"
    
    def execute(self, context):
        obj = context.active_object
        new_group = obj.bone_xy_groups.add()
        new_group.name = f"Group {len(obj.bone_xy_groups)}"
        obj.bone_xy_group_index = len(obj.bone_xy_groups) - 1
        return {'FINISHED'}

class bone_xy_OT_remove_group(bpy.types.Operator):
    bl_idname = "bone_xy.remove_group"
    bl_label = "Remove Group"
    bl_description = "Delete the currently selected ShapeKey Control Group"
    
    def execute(self, context):
        obj = context.active_object
        if obj.bone_xy_groups:
            obj.bone_xy_groups.remove(obj.bone_xy_group_index)
            obj.bone_xy_group_index = min(max(0, obj.bone_xy_group_index - 1), len(obj.bone_xy_groups) - 1)
        return {'FINISHED'}

class bone_xy_OT_add(bpy.types.Operator):
    bl_idname = "bone_xy.add_item"
    bl_label = "Add Mapping"
    bl_description = "Add a new ShapeKey mapping to the current group"
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if group:
            group.bone_xy_list.add()
            group.bone_xy_index = len(group.bone_xy_list) - 1
        return {'FINISHED'}

class bone_xy_OT_remove(bpy.types.Operator):
    bl_idname = "bone_xy.remove_item"
    bl_label = "Remove Mapping"
    bl_description = "Remove the currently selected ShapeKey mapping from the group"
    
    def execute(self, context):
        obj = context.active_object
        group = get_active_group(obj)
        if group and group.bone_xy_list:
            group.bone_xy_list.remove(group.bone_xy_index)
            group.bone_xy_index = min(max(0, group.bone_xy_index - 1), len(group.bone_xy_list) - 1)
        return {'FINISHED'}

class bone_xy_PT_panel(bpy.types.Panel):
    bl_label = "Bone Axis Control"
    bl_idname = "bone_xy_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Bone Axis'

    def draw(self, context):
        layout = self.layout
        try:
            obj = context.active_object

            if not obj or obj.type != 'MESH':
                layout.label(text="Select a Mesh object")
                return

            if HUD_STATE.get("running", False):
                layout.operator("bone_xy.ui_joystick", text="Clear Axis UI", icon='CANCEL')
            else:
                layout.operator("bone_xy.ui_joystick", text="Start Axis UI", icon='PLAY')
                
            row = layout.row(align=True)
            row.operator("bone_xy.reset_handle", text="Reset", icon='FILE_REFRESH')
            row.operator("bone_xy.reset_all", text="Reset All", icon='FILE_REFRESH')
            row.operator("bone_xy.reset_hud", text="Reset HUD", icon='MODIFIER')
                
            layout.separator()
            if hasattr(context.scene, "bone_xy_allow_drag"):
                layout.prop(context.scene, "bone_xy_allow_drag")
            layout.separator()
            
            layout.label(text="Groups:")
            
            if not hasattr(obj, "bone_xy_groups") or len(obj.bone_xy_groups) == 0:
                layout.alert = True
                layout.operator("bone_xy.add_group", text="Create First Group To Setup!", icon='ADD')
                layout.alert = False
            else:
                row = layout.row()
                row.template_list("bone_xy_UL_group_list", "", obj, "bone_xy_groups", obj, "bone_xy_group_index")
                col = row.column(align=True)
                col.operator("bone_xy.add_group", icon='ADD', text="")
                col.operator("bone_xy.remove_group", icon='REMOVE', text="")
                col.separator()
                col.operator("bone_xy.move_group", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("bone_xy.move_group", icon='TRIA_DOWN', text="").direction = 'DOWN'
            
            group = get_active_group(obj)
            if group:
                layout.prop(group, "name", text="Group Name")
                row_h = layout.row(align=True)
                row_h.operator("bone_xy.reset_handle", text="Reset Handle", icon='FILE_REFRESH')
                row_h.operator("bone_xy.keyframe_handle", text="Key Handle  [I]", icon='KEY_HLT')
                layout.operator("bone_xy.bake_animation", icon='ACTION_TWEAK')

                box_val = layout.box()
                row_val = box_val.row()
                row_val.prop(group, "joy_x", text="X (Driveable)")
                row_val.prop(group, "joy_y", text="Y (Driveable)")
                
                row_io = layout.row(align=True)
                row_io.operator("bone_xy.import_group", text="Import JSON", icon='IMPORT')
                row_io.operator("bone_xy.export_group", text="Export JSON", icon='EXPORT')
                layout.separator()
                
                layout.label(text="Mappings:")
                row = layout.row()
                row.template_list("bone_xy_UL_list", "", group, "bone_xy_list", group, "bone_xy_index")

                col = row.column(align=True)
                col.operator("bone_xy.add_item", icon='ADD', text="")
                col.operator("bone_xy.remove_item", icon='REMOVE', text="")
                col.separator()
                col.operator("bone_xy.move_item", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("bone_xy.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
                col.separator()
                col.operator("bone_xy.mirror_mappings", icon='MOD_MIRROR', text="")

                if 0 <= group.bone_xy_index < len(group.bone_xy_list):
                    item = group.bone_xy_list[group.bone_xy_index]
                    box = layout.box()
                    
                    row_type = box.row()
                    row_type.prop(item, "target_type", expand=True)
                    
                    if item.target_type == 'BONE':
                        if obj.type == 'ARMATURE':
                            box.prop_search(item, "bone_name", obj.data, "bones", text="Bone")
                        else:
                            box.prop(item, "bone_name", text="Bone (Need Armature)")
                            
                    row_prop = box.row()
                    row_prop.prop(item, "prop_type", text="")
                    row_prop.prop(item, "axis_index", text="")
                    
                    box.prop(item, "max_value")
                    
                    row_coord = box.row()
                    row_coord.prop(item, "target_x", text="X")
                    row_coord.prop(item, "target_y", text="Y")
                    
                    row_blend = box.row()
                    row_blend.prop(item, "radius", text="Radius")
                    row_blend.prop(item, "blend_mode", text="Blend")
                
            else:
                layout.separator()
                layout.label(text="Mappings:")
                layout.label(text="<- (Click 'Add' to create a Group first)", icon='INFO')
                
            layout.separator()
            layout.label(text="Global Animation Presets:")
            row_preset = layout.row()
            row_preset.template_list("bone_xy_UL_preset_list", "", context.scene, "bone_xy_presets", context.scene, "bone_xy_preset_index")
            
            p_col = row_preset.column(align=True)
            p_col.operator("bone_xy.add_preset", icon='ADD', text="")
            p_col.operator("bone_xy.remove_preset", icon='REMOVE', text="")
            p_col.separator()
            p_col.operator("bone_xy.move_preset", icon='TRIA_UP', text="").direction = 'UP'
            p_col.operator("bone_xy.move_preset", icon='TRIA_DOWN', text="").direction = 'DOWN'
            
            if 0 <= context.scene.bone_xy_preset_index < len(context.scene.bone_xy_presets):
                preset = context.scene.bone_xy_presets[context.scene.bone_xy_preset_index]
                layout.prop(preset, "name", text="Preset Name")
                
                # Global Action Buttons for active preset
                p_ops = layout.row(align=True)
                p_ops.operator("bone_xy.set_preset", text="Set", icon='GREASEPENCIL')
                p_ops.operator("bone_xy.call_preset", text="Call", icon='RESTRICT_SELECT_OFF')
                p_ops.operator("bone_xy.keyframe_preset", text="Key", icon='KEY_HLT')

            layout.separator()
            layout.label(text="Tracker Interface:", icon='CAMERA_DATA')
            box_trk = layout.box()
            if hasattr(context.scene, "bone_xy_tracker_port"):
                box_trk.prop(context.scene, "bone_xy_tracker_port")
            if is_tracker_running():
                box_trk.operator("bone_xy.tracker_stop", text="Stop UDP Server", icon='CANCEL')
            else:
                box_trk.operator("bone_xy.tracker_start", text="Start UDP Server", icon='PLAY')
        except Exception as e:
            box = layout.box()
            box.alert = True
            box.label(text="UI Error:")
            box.label(text=str(e))
            import traceback
            for line in traceback.format_exc().split('\n')[-4:]:
                if line.strip():
                    box.label(text=line)


