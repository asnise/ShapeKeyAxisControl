bl_info = {
    "name": "Bone Axis Control",
    "author": "Axnise",
    "version": (5, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Bone XY",
    "description": "Control bone/object transforms across multiple objects using a 2D Axis Controller",
    "category": "Animation",
}

if "bpy" in locals():
    import importlib
    importlib.reload(core.state)
    importlib.reload(core.main)
    importlib.reload(ui.properties)
    importlib.reload(ui.draw)
    importlib.reload(operators.main)
    importlib.reload(ui.panel)
    importlib.reload(interface.tracker)
else:
    from .core import state
    from .core import main as core
    from .ui import properties
    from .ui import draw
    from .operators import main as operators
    from .ui import panel as ui
    from .interface import tracker

import bpy

classes = (
    properties.bone_xy_PG_item,
    properties.bone_xy_PG_preset_state,
    properties.bone_xy_PG_preset,
    properties.bone_xy_PG_group,
    operators.bone_xy_OT_edit_values,
    operators.bone_xy_OT_reset_handle,
    operators.bone_xy_OT_reset_all,
    operators.bone_xy_OT_keyframe_handle,
    operators.bone_xy_OT_bake_animation,
    operators.bone_xy_OT_export_group,
    operators.bone_xy_OT_import_group,
    operators.bone_xy_OT_reset_hud,
    operators.bone_xy_OT_ui_joystick,
    operators.bone_xy_OT_move_item,
    operators.bone_xy_OT_mirror_mappings,
    operators.bone_xy_OT_move_group,
    operators.bone_xy_OT_move_preset,
    operators.bone_xy_OT_add_preset,
    operators.bone_xy_OT_remove_preset,
    operators.bone_xy_OT_set_preset,
    operators.bone_xy_OT_call_preset,
    operators.bone_xy_OT_keyframe_preset,
    ui.bone_xy_UL_group_list,
    ui.bone_xy_UL_list,
    ui.bone_xy_UL_preset_list,
    ui.bone_xy_OT_add_group,
    ui.bone_xy_OT_remove_group,
    ui.bone_xy_OT_add,
    ui.bone_xy_OT_remove,
    ui.bone_xy_PT_panel,
)

def register():
    tracker.register()
    bpy.types.Scene.bone_xy_allow_drag = bpy.props.BoolProperty(name="Enable Drag Point", default=True)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.bone_xy_groups = bpy.props.CollectionProperty(type=properties.bone_xy_PG_group)
    bpy.types.Object.bone_xy_group_index = bpy.props.IntProperty(update=properties.on_property_update)
    bpy.types.Scene.bone_xy_presets = bpy.props.CollectionProperty(type=properties.bone_xy_PG_preset)
    bpy.types.Scene.bone_xy_preset_index = bpy.props.IntProperty(update=properties.on_preset_change)
    
    # Register Frame Change Handler
    bpy.app.handlers.frame_change_post.append(frame_handler)

def frame_handler(scene):
    # This ensures that when the frame changes (scrubbing), 
    # the bone/object transforms are updated if the joy_x/y handles are animated.
    for obj in bpy.data.objects:
        if hasattr(obj, 'bone_xy_groups'):
            for group in obj.bone_xy_groups:
                core.update_transforms(obj, group, core.get_limit(group))

def unregister():
    tracker.unregister()
    # Remove Frame Change Handler
    if frame_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(frame_handler)
    
    if state.HUD_STATE["running"]:
        state.HUD_STATE["running"] = False
        if state.HUD_STATE["handle"]:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(state.HUD_STATE["handle"], 'WINDOW')
            except:
                pass
            state.HUD_STATE["handle"] = None
            
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.bone_xy_groups
    del bpy.types.Object.bone_xy_group_index
    del bpy.types.Scene.bone_xy_allow_drag
    del bpy.types.Scene.bone_xy_presets
    del bpy.types.Scene.bone_xy_preset_index

if __name__ == "__main__":
    register()


