import bpy
import math
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from ..core.state import HUD_STATE
from ..core.main import get_active_group, get_limit

def get_shader():
    try:
        return gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    except:
        return gpu.shader.from_builtin('UNIFORM_COLOR')

def draw_hud():
    if not HUD_STATE["running"]:
        return
        
    try:
        gpu.state.blend_set('ALPHA')
    except:
        pass
        
    shader = get_shader()
    x, y, size = HUD_STATE["x"], HUD_STATE["y"], HUD_STATE["size"]
    
    obj = bpy.context.active_object
    group = get_active_group(obj)
    limit = get_limit(group) if group else 1.0
    
    jx = group.joy_x if group else 0.0
    jy = group.joy_y if group else 0.0
    
    # Main Panel Background (Covers buttons below the joystick)
    panel_y_min = y - 112
    p_verts = ((x-4, panel_y_min), (x+size+4, panel_y_min), (x+size+4, y+size), (x-4, y+size))
    p_batch = batch_for_shader(shader, 'TRIS', {"pos": p_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.bind()
    shader.uniform_float("color", (0.18, 0.18, 0.18, 0.98))
    p_batch.draw(shader)
    
    # Draw Panel Outline
    out_verts = ((x-4, panel_y_min), (x+size+4, panel_y_min), (x+size+4, y+size), (x-4, y+size))
    out_batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": out_verts})
    shader.uniform_float("color", (0.3, 0.3, 0.3, 0.98))
    out_batch.draw(shader)
    
    # Draggable Header Box
    h_verts = ((x-4, y+size), (x+size+4, y+size), (x+size+4, y+size+25), (x-4, y+size+25))
    h_batch = batch_for_shader(shader, 'TRIS', {"pos": h_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", (0.12, 0.12, 0.12, 0.98))
    h_batch.draw(shader)
    
    blf.position(0, x + 8, y + size + 7, 0)
    blf.size(0, 14)
    blf.color(0, 0.9, 0.9, 0.9, 1.0)
    blf.draw(0, "ShapeKey Axis Control")

    # Joystick Grid Background (Sunken Area)
    bg_verts = ((x, y), (x+size, y), (x+size, y+size), (x, y+size))
    bg_batch = batch_for_shader(shader, 'TRIS', {"pos": bg_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", (0.11, 0.11, 0.11, 1.0))
    bg_batch.draw(shader)
    
    # Joystick Outersquare Border
    bg_out_batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": bg_verts})
    shader.uniform_float("color", (0.05, 0.05, 0.05, 1.0))
    bg_out_batch.draw(shader)

    cx, cy = x + size/2, y + size/2
    
    if group and hasattr(group, 'shape_xy_list'):
        # Enable Scissor testing to crop drawings to the joystick bounds
        try:
            bgl_ok = True
            import bgl
        except ImportError:
            bgl_ok = False
            
        if bgl_ok:
            bgl.glEnable(bgl.GL_SCISSOR_TEST)
            # Scissor parameters: x, y, width, height
            # Note: bgl scissor uses screen coordinates, which match viewport directly here
            bgl.glScissor(int(x), int(y), int(size), int(size))
            
        for item in group.shape_xy_list:
            px = cx + (item.target_x / limit) * (size/2)
            py = cy + (item.target_y / limit) * (size/2)
            pr = (item.radius / limit) * (size/2)
            
            circle_verts = [(px + math.cos(i/32 * 2*math.pi)*pr, py + math.sin(i/32 * 2*math.pi)*pr) for i in range(33)]
            circle_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": circle_verts})
            shader.uniform_float("color", (1.0, 0.2, 0.2, 0.6))
            circle_batch.draw(shader)
            
            p_verts = ((px-3, py-3), (px+3, py-3), (px+3, py+3), (px-3, py+3))
            p_batch = batch_for_shader(shader, 'TRIS', {"pos": p_verts}, indices=((0, 1, 2), (2, 3, 0)))
            shader.uniform_float("color", (0.8, 0.8, 0.8, 1.0))
            p_batch.draw(shader)
            
            if item.shape_name:
                blf.position(0, px + 5, py + 5, 0)
                blf.size(0, 12)
                blf.color(0, 1.0, 1.0, 1.0, 1.0)
                blf.draw(0, item.shape_name)
        
        # Disable Scissor Testing
        if bgl_ok:
            bgl.glDisable(bgl.GL_SCISSOR_TEST)

    line_verts = ((cx, y), (cx, y+size), (x, cy), (x+size, cy))
    line_batch = batch_for_shader(shader, 'LINES', {"pos": line_verts})
    shader.uniform_float("color", (0.2, 0.2, 0.2, 1.0))
    line_batch.draw(shader)
    
    if group:
        dot_x = cx + (jx * size/2)
        dot_y = cy + (jy * size/2)
        dot_verts = ((dot_x-8, dot_y-8), (dot_x+8, dot_y-8), (dot_x+8, dot_y+8), (dot_x-8, dot_y+8))
        dot_batch = batch_for_shader(shader, 'TRIS', {"pos": dot_verts}, indices=((0, 1, 2), (2, 3, 0)))
        shader.uniform_float("color", (0.3, 0.6, 1.0, 1.0))
        dot_batch.draw(shader)
    
    # Standard Blender UI Colors for Buttons
    b_col = (0.32, 0.32, 0.32, 1.0)
    t_col = (0.85, 0.85, 0.85, 1.0)
    
    # Reset Button
    btn_r_y = y - 35
    r_verts = ((x, btn_r_y), (x+size, btn_r_y), (x+size, btn_r_y+30), (x, btn_r_y+30))
    r_batch = batch_for_shader(shader, 'TRIS', {"pos": r_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", b_col)
    r_batch.draw(shader)
    r_out = batch_for_shader(shader, 'LINE_LOOP', {"pos": r_verts})
    shader.uniform_float("color", (0.1, 0.1, 0.1, 1.0))
    r_out.draw(shader)
    
    # Edit Values Display
    btn_e_y = y - 75
    e_verts = ((x, btn_e_y), (x+size, btn_e_y), (x+size, btn_e_y+35), (x, btn_e_y+35))
    e_batch = batch_for_shader(shader, 'TRIS', {"pos": e_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", (0.11, 0.11, 0.11, 1.0))
    e_batch.draw(shader)
    e_out = batch_for_shader(shader, 'LINE_LOOP', {"pos": e_verts})
    shader.uniform_float("color", (0.1, 0.1, 0.1, 1.0))
    e_out.draw(shader)

    val_x = jx * limit
    val_y = jy * limit

    # Separate Group Selection Boxes [ < ] [ Group Name ] [ > ]
    btn_g_y = y - 105

    # Left Box
    gL_verts = ((x, btn_g_y), (x+30, btn_g_y), (x+30, btn_g_y+25), (x, btn_g_y+25))
    gL_batch = batch_for_shader(shader, 'TRIS', {"pos": gL_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", b_col)
    gL_batch.draw(shader)
    gL_out = batch_for_shader(shader, 'LINE_LOOP', {"pos": gL_verts})
    shader.uniform_float("color", (0.1, 0.1, 0.1, 1.0))
    gL_out.draw(shader)

    # Middle Box
    gM_verts = ((x+35, btn_g_y), (x+size-35, btn_g_y), (x+size-35, btn_g_y+25), (x+35, btn_g_y+25))
    gM_batch = batch_for_shader(shader, 'TRIS', {"pos": gM_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", (0.22, 0.22, 0.22, 1.0))
    gM_batch.draw(shader)
    gM_out = batch_for_shader(shader, 'LINE_LOOP', {"pos": gM_verts})
    shader.uniform_float("color", (0.1, 0.1, 0.1, 1.0))
    gM_out.draw(shader)

    # Right Box
    gR_verts = ((x+size-30, btn_g_y), (x+size, btn_g_y), (x+size, btn_g_y+25), (x+size-30, btn_g_y+25))
    gR_batch = batch_for_shader(shader, 'TRIS', {"pos": gR_verts}, indices=((0, 1, 2), (2, 3, 0)))
    shader.uniform_float("color", b_col)
    gR_batch.draw(shader)
    gR_out = batch_for_shader(shader, 'LINE_LOOP', {"pos": gR_verts})
    shader.uniform_float("color", (0.1, 0.1, 0.1, 1.0))
    gR_out.draw(shader)

    blf.position(0, x + 50, btn_r_y + 8, 0)
    blf.size(0, 14)
    blf.color(0, t_col[0], t_col[1], t_col[2], 1.0)
    blf.draw(0, "Reset Position")

    blf.position(0, x + 10, btn_e_y + 12, 0)
    blf.size(0, 14)
    blf.color(0, 0.9, 0.9, 0.9, 1.0)
    blf.draw(0, f"X: {val_x:.3f}     Y: {val_y:.3f}")

    group_name = group.name if group else "None"

    blf.position(0, x + 11, btn_g_y + 7, 0)
    blf.size(0, 13)
    blf.color(0, t_col[0], t_col[1], t_col[2], 1.0)
    blf.draw(0, "<")

    blf.position(0, x + 42, btn_g_y + 7, 0)
    blf.size(0, 12)
    blf.color(0, 1.0, 1.0, 1.0, 1.0)
    blf.draw(0, f"{group_name}")

    blf.position(0, x + size - 19, btn_g_y + 7, 0)
    blf.size(0, 13)
    blf.color(0, t_col[0], t_col[1], t_col[2], 1.0)
    blf.draw(0, ">")

    try:
        gpu.state.blend_set('NONE')
    except:
        pass
