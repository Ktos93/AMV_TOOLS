import bpy
import numpy as np
from mathutils import Vector, Quaternion


def bbox_center(min_coords, max_coords):
    center = np.array(min_coords) + np.array(max_coords)
    center /= 2
    return center

def rotate_point_around_center(point, center, angle):
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)],
                                [np.sin(angle), np.cos(angle)]])
    translated_point = point - center
    rotated_point = np.dot(rotation_matrix, translated_point)
    return rotated_point + center

def rotate_bbox(bbox, center, angle):
    rotated_bbox = []
    for point in bbox:
        rotated_point = point.copy()
        rotated_point[0], rotated_point[1] = rotate_point_around_center(point[:2], center[:2], angle)[:2]
        rotated_bbox.append(rotated_point)
    return np.array(rotated_bbox)

def bbox_dimensions(bbox):
    min_coords = np.min(bbox, axis=0)
    max_coords = np.max(bbox, axis=0)
    return (max_coords - min_coords) / 2


def calculate_sphere_counts(interval, min_bound, max_bound):
    num_spheres = [round((max_bound[i] - min_bound[i]) / interval) for i in range(3)]
    return tuple(num_spheres)


def setup_bake_settings():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.bake.target = 'VERTEX_COLORS'
    scene.cycles.bake_type = 'DIFFUSE'
    scene.render.use_bake_selected_to_active = False
    scene.render.bake.use_pass_direct = True

    if bpy.context.scene.bounces > 0:
        scene.render.bake.use_pass_indirect = True
        bpy.context.scene.cycles.max_bounces = bpy.context.scene.bounces
        bpy.context.scene.cycles.diffuse_bounces = bpy.context.scene.bounces
    else:
        scene.render.bake.use_pass_indirect = False
        bpy.context.scene.cycles.max_bounces = 0
        bpy.context.scene.cycles.diffuse_bounces = 0

    bpy.context.scene.cycles.glossy_bounces = 0
    bpy.context.scene.cycles.transmission_bounces = 0
    bpy.context.scene.cycles.volume_bounces = 0
    bpy.context.scene.cycles.transparent_max_bounces = 0

    scene.render.bake.use_pass_color = False
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.device = 'CPU'


def update_light_strength(self, context):
    if "EmissiveMaterial" in bpy.data.materials:
        bpy.data.materials["EmissiveMaterial"].node_tree.nodes["Emission"].inputs[1].default_value = self.light_strength


def update_probes_offset(self, context):
    selected_zone = get_selected_zone(context)
    offset = selected_zone.offset

    collection_name = 'Probes-'+ selected_zone.name

    if collection_name in bpy.data.collections:
        probes_collection = bpy.data.collections.get(collection_name)
        for obj in probes_collection.objects:
            new_offset = np.array(offset) - np.array(obj["offset"])
            obj.location += Vector(new_offset)
            obj["offset"] = offset


def draw_list_with_add_remove(layout: bpy.types.UILayout, add_operator: str, remove_operator: str, *temp_list_args, **temp_list_kwargs):
    """Draw a UIList with an add and remove button on the right column. Returns the left column."""
    row = layout.row()
    list_col = row.column()
    list_col.template_list(*temp_list_args, **temp_list_kwargs)
    side_col = row.column()
    col = side_col.column(align=True)
    col.operator(add_operator, text="", icon="ADD")
    col.operator(remove_operator, text="", icon="REMOVE")
    return list_col, side_col


def get_selected_vertices(obj):
    mode = obj.mode
    if obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    # We need to switch from Edit mode to Object mode so the vertex selection gets updated (disgusting!)
    verts = [obj.matrix_world @ Vector((v.co.x, v.co.y, v.co.z))
             for v in obj.data.vertices if v.select]
    bpy.ops.object.mode_set(mode=mode)
    return verts



def get_new_item_id(collection: bpy.types.bpy_prop_collection) -> int:
    ids = sorted({item.id for item in collection})
    if not ids:
        return 1
    for i, item_id in enumerate(ids):
        new_id = item_id + 1
        if new_id in ids:
            continue
        if i + 1 >= len(ids):
            return new_id
        next_item = ids[i + 1]
        if next_item > new_id:
            return new_id
    # Max id + 1
    return ids[-1] + 1
