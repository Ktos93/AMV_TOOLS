bl_info = {
    "name": "AMV TOOLS",
    "author": "ktos93",
    "version": (0, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Tools",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

import bpy

register, unregister = bpy.utils.register_submodule_factory(__package__, (
    'main', 
    'probes',
    'bake',
    'light',
    'gizmo',
))

if __name__ == "__main__":
    register()
   