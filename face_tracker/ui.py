import bpy

def draw_axis_settings(layout, group, axis):
    pfx = f"tracker_{axis}_"
    box = layout.box()
    box.label(text=f"{axis.upper()}-Axis Mapping", icon='CON_LOCLIKE')
    
    box.prop(group, pfx+"mode", text="Tracking Mode")
    
    row = box.row()
    row.prop(group, pfx+"pt_a", text="Point A")
    row.prop(group, pfx+"pt_b", text="Point B")
    
    col = box.column(align=True)
    col.label(text="Input Range:")
    col.prop(group, pfx+"rmin", text="Lower Bound")
    col.prop(group, pfx+"rmax", text="Upper Bound")
    
    row_cal = box.row(align=True)
    row_cal.operator(f"shape_xy.tracker_cal_min_{axis}", text="Capture Min", icon='TRIA_LEFT')
    row_cal.operator(f"shape_xy.tracker_cal_max_{axis}", text="Capture Max", icon='TRIA_RIGHT')
    
    col = box.column(align=True)
    col.label(text="Output Signal Tuning:")
    col.prop(group, pfx+"omin", text="Min Target")
    col.prop(group, pfx+"omax", text="Max Target")
    col.prop(group, pfx+"sens", text="Gain")
    col.prop(group, pfx+"exp", text="Curve (Exp)")
    
    col = box.column(align=True)
    col.label(text="Smoothing:")
    col.prop(group, pfx+"lerp_en", text="Enable Filter")
    if getattr(group, pfx+"lerp_en"):
        col.prop(group, pfx+"lerp_fac", text="Smooth Factor")

class SHAPE_XY_PG_tracker_target(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object, name="Object")
    group_name: bpy.props.StringProperty(name="Group")

class SHAPE_XY_UL_tracker_targets(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=f"List {index+1}:", icon='DOT')
        row.prop(item, "obj", text="")
        if item.obj and hasattr(item.obj, 'shape_xy_groups'):
            row.prop_search(item, "group_name", item.obj, "shape_xy_groups", text="")
        else:
            row.label(text="<Select>")

class SHAPE_XY_PT_tracker_panel(bpy.types.Panel):
    bl_label = "Face Tracker (Built-In)"
    bl_idname = "SHAPE_XY_PT_tracker_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shape Axis'
    
    def draw(self, context):
        layout = self.layout
        
        from .installer import check_dependencies
        status = context.scene.tracker_install_status
        
        if not check_dependencies():
            box = layout.box()
            box.label(text="Dependencies Missing!", icon='ERROR')
            box.operator("shape_xy.install_deps", icon='PLUGIN')
            if status:
                box.label(text=status)
            return

        from .core import TRACKER_RUNNING
        
        row = layout.row(align=True)
        if TRACKER_RUNNING:
            row.operator("shape_xy.tracker_native_stop", text="Stop Tracker", icon='CANCEL')
            layout.label(text=getattr(context.scene, "tracker_fps_status", ""), icon='TIME')
        else:
            row.prop(context.scene, "tracker_cam_index", text="Camera")
            row.operator("shape_xy.tracker_native_start", text="Start Tracker", icon='PLAY')
            
        layout.operator("shape_xy.tracker_open_map", text="Reference Map", icon='HELP')
        
        if hasattr(context.scene, "tracker_show_hud"):
            layout.prop(context.scene, "tracker_show_hud", text="Show Point HUD in Viewport")
            
        layout.separator()
        layout.label(text="Live List Group:", icon='OUTLINER_OB_GROUP_INSTANCE')
        
        row_list = layout.row()
        row_list.template_list("SHAPE_XY_UL_tracker_targets", "", context.scene, "tracker_targets", context.scene, "tracker_target_index", rows=3)
        
        col_list = row_list.column(align=True)
        col_list.operator("shape_xy.tracker_add_target", icon='ADD', text="")
        col_list.operator("shape_xy.tracker_remove_target", icon='REMOVE', text="")
        
        idx = context.scene.tracker_target_index
        if hasattr(context.scene, "tracker_targets") and 0 <= idx < len(context.scene.tracker_targets):
            target = context.scene.tracker_targets[idx]
            obj = target.obj
            if obj and target.group_name and hasattr(obj, 'shape_xy_groups'):
                if target.group_name in obj.shape_xy_groups:
                    group = obj.shape_xy_groups[target.group_name]
                    
                    layout.separator()
                    layout.label(text=f"Tracker Setup: {group.name}", icon='GROUP')
                    
                    row_preset = layout.row(align=True)
                    row_preset.operator("shape_xy.tracker_apply_preset", text="Mouth").preset_type = "MOUTH"
                    row_preset.operator("shape_xy.tracker_apply_preset", text="Eyes").preset_type = "EYES"
                    row_preset.operator("shape_xy.tracker_apply_preset", text="Blink").preset_type = "EYE_BLINK"
                    
                    layout.separator()
                    draw_axis_settings(layout, group, 'x')
                    draw_axis_settings(layout, group, 'y')

def register():
    bpy.utils.register_class(SHAPE_XY_PG_tracker_target)
    bpy.types.Scene.tracker_targets = bpy.props.CollectionProperty(type=SHAPE_XY_PG_tracker_target)
    bpy.types.Scene.tracker_target_index = bpy.props.IntProperty()
    bpy.utils.register_class(SHAPE_XY_UL_tracker_targets)
    bpy.utils.register_class(SHAPE_XY_PT_tracker_panel)

def unregister():
    bpy.utils.unregister_class(SHAPE_XY_PT_tracker_panel)
    bpy.utils.unregister_class(SHAPE_XY_UL_tracker_targets)
    if hasattr(bpy.types.Scene, "tracker_targets"):
        del bpy.types.Scene.tracker_targets
        del bpy.types.Scene.tracker_target_index
    bpy.utils.unregister_class(SHAPE_XY_PG_tracker_target)
