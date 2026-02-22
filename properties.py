import bpy
from .core import get_active_group, get_limit, update_shapes
from .state import HUD_STATE

def on_property_update(self, context):
    if HUD_STATE["running"]:
        obj = context.active_object
        if obj:
            group = get_active_group(obj)
            if group:
                limit = get_limit(group)
                update_shapes(obj, group, limit)
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

class SHAPE_XY_PG_item(bpy.types.PropertyGroup):
    shape_name: bpy.props.StringProperty(update=on_property_update)
    target_x: bpy.props.FloatProperty(default=1.0, update=on_property_update)
    target_y: bpy.props.FloatProperty(default=0.0, update=on_property_update)
    radius: bpy.props.FloatProperty(default=1.0, min=0.001, update=on_property_update)
    blend_mode: bpy.props.EnumProperty(
        name="Blend Mode",
        items=[
            ('AUTO', "Auto", ""),
            ('BOX', "Box Falloff", ""),
            ('RADIAL', "Radial Falloff", ""),
            ('AXIS_X', "X-Axis", ""),
            ('AXIS_Y', "Y-Axis", "")
        ],
        default='AUTO',
        update=on_property_update
    )

class SHAPE_XY_PG_preset_state(bpy.types.PropertyGroup):
    obj_name: bpy.props.StringProperty()
    group_name: bpy.props.StringProperty()
    joy_x: bpy.props.FloatProperty(default=0.0)
    joy_y: bpy.props.FloatProperty(default=0.0)

class SHAPE_XY_PG_preset(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="New Preset")
    states: bpy.props.CollectionProperty(type=SHAPE_XY_PG_preset_state)

def on_preset_change(self, context):
    pass

class SHAPE_XY_PG_group(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="New Group")
    joy_x: bpy.props.FloatProperty(default=0.0, update=on_property_update)
    joy_y: bpy.props.FloatProperty(default=0.0, update=on_property_update)
    shape_xy_list: bpy.props.CollectionProperty(type=SHAPE_XY_PG_item)
    shape_xy_index: bpy.props.IntProperty()
