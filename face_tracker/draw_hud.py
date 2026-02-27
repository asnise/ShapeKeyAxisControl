import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from .core import CURRENT_LANDMARKS, TRACKER_RUNNING

handler = None

def draw_callback_px():
    if not TRACKER_RUNNING or not CURRENT_LANDMARKS:
        return
    
    if not getattr(bpy.context.scene, "tracker_show_hud", True):
        return
        
    width = bpy.context.region.width
    height = bpy.context.region.height

    size = 200
    offset_x = width - size - 20
    offset_y = 20

    points = []
    for lm in CURRENT_LANDMARKS:
        x = offset_x + int(lm[0] * size)
        y = offset_y + int((1.0 - lm[1]) * size)
        points.append((x, y))
        
    if not points:
        return

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    
    try:
        gpu.state.point_size_set(3.0)
    except:
        import bgl
        try:
            bgl.glPointSize(3.0)
        except: pass
        
    shader.bind()
    shader.uniform_float("color", (0.0, 1.0, 0.5, 1.0))
    batch.draw(shader)

def register():
    global handler
    bpy.types.Scene.tracker_show_hud = bpy.props.BoolProperty(name="Show HUD", default=True)
    handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (), 'WINDOW', 'POST_PIXEL')

def unregister():
    global handler
    if handler:
        bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        handler = None
    if hasattr(bpy.types.Scene, "tracker_show_hud"):
        del bpy.types.Scene.tracker_show_hud
