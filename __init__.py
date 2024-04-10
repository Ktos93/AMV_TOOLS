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

from . import main

classes = (
    main.BakeAMVToJSON,
    main.DisplayProbes,
    main.DeleteProbes,
    main.SaveProbesLocation,
    main.ClearProbesLocation,
    main.SetupLight,
    main.AMV_PT_TOOLS,
    main.AMV_PT_LOCATION_TOOLS,
    main.CalculatePosition,
    main.AMV_PT_ADVANCED_TOOLS,
    main.BoundingBoxGizmo,
    main.BoundingBoxGizmoGroup,
    main.GenerateUUID,
    
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    main.register()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    main.unregister()

if __name__ == "__main__":
    register()
   
