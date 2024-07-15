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
    for i in range(3):
        if min_bound[i] > max_bound[i]:
            min_bound[i], max_bound[i] = max_bound[i], min_bound[i]
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
    if "Emission" in bpy.data.worlds["World"].node_tree.nodes:
        bpy.data.worlds["World"].node_tree.nodes["Emission"].inputs[1].default_value = self.light_strength

def rot(x, k):
    return ((x << k) & 0xFFFFFFFF) | (x >> (32 - k))

def mix(a, b, c):
    a = (a - c) & 0xFFFFFFFF; a ^= rot(c, 4); c = (c + b) & 0xFFFFFFFF
    b = (b - a) & 0xFFFFFFFF; b ^= rot(a, 6); a = (a + c) & 0xFFFFFFFF
    c = (c - b) & 0xFFFFFFFF; c ^= rot(b, 8); b = (b + a) & 0xFFFFFFFF
    a = (a - c) & 0xFFFFFFFF; a ^= rot(c, 16); c = (c + b) & 0xFFFFFFFF
    b = (b - a) & 0xFFFFFFFF; b ^= rot(a, 19); a = (a + c) & 0xFFFFFFFF
    c = (c - b) & 0xFFFFFFFF; c ^= rot(b, 4); b = (b + a) & 0xFFFFFFFF
    return a, b, c

def final(a, b, c):
    c ^= b; c = (c - rot(b, 14)) & 0xFFFFFFFF
    a ^= c; a = (a - rot(c, 11)) & 0xFFFFFFFF
    b ^= a; b = (b - rot(a, 25)) & 0xFFFFFFFF
    c ^= b; c = (c - rot(b, 16)) & 0xFFFFFFFF
    a ^= c; a = (a - rot(c, 4)) & 0xFFFFFFFF
    b ^= a; b = (b - rot(a, 14)) & 0xFFFFFFFF
    c ^= b; c = (c - rot(b, 24)) & 0xFFFFFFFF
    return a, b, c

def compute_probe_hash(k, initval = 0):
    length = len(k)
    a = b = c = (0xdeadbeef + (length << 2) + initval) & 0xFFFFFFFF

    while length > 3:
        a = (a + k[0]) & 0xFFFFFFFF
        b = (b + k[1]) & 0xFFFFFFFF
        c = (c + k[2]) & 0xFFFFFFFF
        a, b, c = mix(a, b, c)
        length -= 3
        k = k[3:]

    if length == 3:
        c = (c + k[2]) & 0xFFFFFFFF
    if length >= 2:
        b = (b + k[1]) & 0xFFFFFFFF
    if length >= 1:
        a = (a + k[0]) & 0xFFFFFFFF
        a, b, c = final(a, b, c)

    return c

def gen_hash(text):
    if text is None:
        return 0
    h = 0
    for char in text:
        h += ord(char)
        h &= 0xFFFFFFFF
        h += (h << 10)
        h &= 0xFFFFFFFF
        h ^= (h >> 6)
        h &= 0xFFFFFFFF
    
    h += (h << 3)
    h &= 0xFFFFFFFF
    h ^= (h >> 11)
    h &= 0xFFFFFFFF
    h += (h << 15)
    h &= 0xFFFFFFFF

    return h & 0xFFFFFFFF


######################################################
################ SOLLUMZ CODE <3 <3 ###################
######################################################

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
