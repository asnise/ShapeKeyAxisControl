bl_info = {
    "name": "ShapeKey Axis Control",
    "author": "Axnise",
    "version": (5, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Shape XY",
    "description": "Control shape keys across multiple objects using a 2D Axis Controller",
    "category": "Animation",
}

if "bpy" in locals():
    import importlib
    importlib.reload(state)
    importlib.reload(core)
    importlib.reload(properties)
    importlib.reload(draw)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import state
    from . import core
    from . import properties
    from . import draw
    from . import operators
    from . import ui

import bpy

classes = (
    properties.SHAPE_XY_PG_item,
    properties.SHAPE_XY_PG_preset_state,
    properties.SHAPE_XY_PG_preset,
    properties.SHAPE_XY_PG_group,
    operators.SHAPE_XY_OT_edit_values,
    operators.SHAPE_XY_OT_reset_handle,
    operators.SHAPE_XY_OT_reset_all,
    operators.SHAPE_XY_OT_keyframe_handle,
    operators.SHAPE_XY_OT_bake_animation,
    operators.SHAPE_XY_OT_export_group,
    operators.SHAPE_XY_OT_import_group,
    operators.SHAPE_XY_OT_reset_hud,
    operators.SHAPE_XY_OT_ui_joystick,
    operators.SHAPE_XY_OT_move_item,
    operators.SHAPE_XY_OT_mirror_mappings,
    operators.SHAPE_XY_OT_move_group,
    operators.SHAPE_XY_OT_move_preset,
    operators.SHAPE_XY_OT_add_preset,
    operators.SHAPE_XY_OT_remove_preset,
    operators.SHAPE_XY_OT_set_preset,
    operators.SHAPE_XY_OT_call_preset,
    operators.SHAPE_XY_OT_keyframe_preset,
    ui.SHAPE_XY_UL_group_list,
    ui.SHAPE_XY_UL_list,
    ui.SHAPE_XY_UL_preset_list,
    ui.SHAPE_XY_OT_add_group,
    ui.SHAPE_XY_OT_remove_group,
    ui.SHAPE_XY_OT_add,
    ui.SHAPE_XY_OT_remove,
    ui.SHAPE_XY_PT_panel,
)

def register():
    bpy.types.Scene.shape_xy_allow_drag = bpy.props.BoolProperty(name="Enable Drag Point", default=True)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.shape_xy_groups = bpy.props.CollectionProperty(type=properties.SHAPE_XY_PG_group)
    bpy.types.Object.shape_xy_group_index = bpy.props.IntProperty(update=properties.on_property_update)
    bpy.types.Scene.shape_xy_presets = bpy.props.CollectionProperty(type=properties.SHAPE_XY_PG_preset)
    bpy.types.Scene.shape_xy_preset_index = bpy.props.IntProperty(update=properties.on_preset_change)
    
    # Register Frame Change Handler
    bpy.app.handlers.frame_change_post.append(frame_handler)

def frame_handler(scene):
    # This ensures that when the frame changes (scrubbing), 
    # the shape keys are updated if the joy_x/y handles are animated.
    for obj in bpy.data.objects:
        if hasattr(obj, 'shape_xy_groups'):
            for group in obj.shape_xy_groups:
                core.update_shapes(obj, group, core.get_limit(group))

def unregister():
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
    del bpy.types.Object.shape_xy_groups
    del bpy.types.Object.shape_xy_group_index
    del bpy.types.Scene.shape_xy_allow_drag
    del bpy.types.Scene.shape_xy_presets
    del bpy.types.Scene.shape_xy_preset_index

if __name__ == "__main__":
    register()
