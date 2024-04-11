import bpy
from bpy.types import Gizmo, GizmoGroup
from mathutils import Vector

from .main import get_selected_zone

class BoundingBoxGizmo(Gizmo):
    bl_idname = "OBJECT_GT_bounding_box"

    @staticmethod
    def get_bbox_verts(obj):
        # Calculate bounding box corners relative to center
        bbox_corners = [Vector(corner) for corner in [
            (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5),
            (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5),
        ]]
        scale = (1 /(bpy.context.scene.sphere_radius * 2)) * bpy.context.scene.interval
        bbox_corners = [Vector(corner) * scale for corner in obj.bound_box]

        # Construct list of vertices representing bbox lines
        bbox_lines = [bbox_corners[i] for edge in [(0, 1), (1, 2), (2, 3), (3, 0),
                                                   (4, 5), (5, 6), (6, 7), (7, 4),
                                                   (0, 4), (1, 5), (2, 6), (3, 7)] for i in edge]
        return bbox_lines

    def draw(self, context):
        obj = context.active_object
        if obj:
            for obj in context.selected_objects:
                bbox_verts = self.get_bbox_verts(obj)
                self.color = 0.9, 0.55, 0.55
                self.custom_shape = self.new_custom_shape("LINES", bbox_verts)
                self.draw_custom_shape(self.custom_shape, matrix=obj.matrix_world)

class BoundingBoxGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_BoundingBox"
    bl_label = "Bounding Box Gizmo"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and 'probe' in obj.name.lower()

    def setup(self, context):
        pass
    
    def draw_prepare(self, context):
        self.gizmos.clear()
        bbox_gizmo = self.gizmos.new("OBJECT_GT_bounding_box")



class ZoneGizmo(bpy.types.Gizmo):
    bl_idname = "OBJECT_GT_zone"

    def __init__(self):
        super().__init__()
        self.linked_room = None

    @staticmethod
    def get_verts(bbmin, bbmax):
        return [
            bbmin,
            Vector((bbmin.x, bbmin.y, bbmax.z)),

            bbmin,
            Vector((bbmax.x, bbmin.y, bbmin.z)),

            bbmin,
            Vector((bbmin.x, bbmax.y, bbmin.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            Vector((bbmax.x, bbmin.y, bbmin.z)),

            Vector((bbmin.x, bbmin.y, bbmax.z)),
            Vector((bbmin.x, bbmax.y, bbmax.z)),

            Vector((bbmin.x, bbmax.y, bbmin.z)),
            Vector((bbmin.x, bbmax.y, bbmax.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            Vector((bbmax.x, bbmin.y, bbmax.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            Vector((bbmin.x, bbmin.y, bbmax.z)),

            Vector((bbmax.x, bbmin.y, bbmin.z)),
            Vector((bbmax.x, bbmax.y, bbmin.z)),

            Vector((bbmin.x, bbmax.y, bbmin.z)),
            Vector((bbmax.x, bbmax.y, bbmin.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            bbmax,

            Vector((bbmin.x, bbmax.y, bbmax.z)),
            bbmax,

            Vector((bbmax.x, bbmax.y, bbmin.z)),
            bbmax
        ]

    def draw(self, context):
        selected_zone = get_selected_zone(context)
        
        zone = self.linked_zone

        self.color = 0.31, 0.38, 1
        self.alpha = 0.7
        self.use_draw_scale = False

        if zone == selected_zone:
            self.color = self.color * 2
            self.alpha = 0.9

        self.custom_shape = self.new_custom_shape("LINES", ZoneGizmo.get_verts(zone.bb_min, zone.bb_max))
        self.draw_custom_shape(self.custom_shape)


class ZoneGizmoGroup(bpy.types.GizmoGroup):
    bl_idname = "OBJECT_GGT_Zone"
    bl_label = "Zone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT"}

    @classmethod
    def poll(cls, context):
        selected_zone = get_selected_zone(context)
        if selected_zone is None:
            return False
        return True

    def setup(self, context):
        pass

    def draw_prepare(self, context):
        zones = context.scene.zones
        self.gizmos.clear()
        for zone in zones:
            gz = self.gizmos.new(ZoneGizmo.bl_idname)
            gz.linked_zone = zone




classes = (

    BoundingBoxGizmo,
    BoundingBoxGizmoGroup,
    ZoneGizmo,
    ZoneGizmoGroup
     
)
  

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)