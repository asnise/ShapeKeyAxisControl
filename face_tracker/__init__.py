import bpy
from . import installer
from . import core
from . import ui
from . import operator
from . import draw_hud

def register():
    installer.register()
    core.register()
    operator.register()
    draw_hud.register()
    ui.register()

def unregister():
    ui.unregister()
    draw_hud.unregister()
    operator.unregister()
    core.unregister()
    installer.unregister()
