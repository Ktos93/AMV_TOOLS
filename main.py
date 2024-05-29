import bpy
import numpy as np
from mathutils import Vector, Quaternion

from .utils import draw_list_with_add_remove , bbox_center, rotate_bbox, bbox_dimensions, get_new_item_id, update_light_strength, get_selected_vertices


class AMV_PT_Tools(bpy.types.Panel):
    bl_label = "AMV Tools"
    bl_idname = "AMV_PT_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AMV'
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = True

        list_col, _ = draw_list_with_add_remove(layout, "amv.create_zone", "amv.delete_zone",
                                                AMV_UL_ZONES_LIST.bl_idname, "", context.scene, "zones", context.scene, "zone_index", rows=3)
        row = list_col.row()


        selected_zone = get_selected_zone(context)
        if not selected_zone:
            return

        layout.separator()
        for prop_name in Zone_Properties.__annotations__:
            if prop_name in ["id", "size", "probes_location_3d"]:
                continue
            layout.prop(selected_zone, prop_name)

        list_col.operator("amv.set_bounds_from_selection", icon="GROUP_VERTEX")
        list_col.operator("amv.bake_amv_to_json", text=str(bpy.context.scene.proggress), icon="RENDERLAYERS")
        list_col.operator("amv.bake_reflection_probes", icon="RENDERLAYERS")
        list_col.operator("amv.calculate_position")
        list_col.operator("amv.generate_uuid")
        row = list_col.row()
        pie = row.menu_pie()
  
        pie.operator("amv.display_probes", icon="HIDE_OFF")
        pie.operator("amv.delete_probes", icon="HIDE_ON")
        row = list_col.row()
        pie = row.menu_pie()
        pie.operator("amv.save_probes", icon="FILE_TICK")
        pie.operator("amv.clear_probes", icon="TRASH")
        
        


class AMV_PT_Location_Tools(bpy.types.Panel):
    bl_label = "Interior Info"
    bl_idname = "AMV_PT_Location_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AMV'
    bl_order = 2

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = True
        column = layout.column()
        column.prop(context.scene, "interior_name", text="Interior Name")
        column.prop(context.scene, "input_location", text="Interior Location")
        column.prop(context.scene, "input_rotation", text="Interior Rotation")
       


class AMV_OT_Calculate_Position(bpy.types.Operator):
    bl_idname = "amv.calculate_position"
    bl_label = "Calculate Position"

    @classmethod
    def poll(cls, context):
        return get_selected_zone(context) is not None

    def execute(self, context):
        zone = get_selected_zone(context)

        min_coords = np.array(zone.bb_min)
        max_coords = np.array(zone.bb_max)

        bbox = np.array([
            [min_coords[0], min_coords[1], min_coords[2]],
            [max_coords[0], min_coords[1], min_coords[2]],
            [max_coords[0], max_coords[1], min_coords[2]],
            [min_coords[0], max_coords[1], min_coords[2]],
            [min_coords[0], min_coords[1], max_coords[2]],
            [max_coords[0], min_coords[1], max_coords[2]],
            [max_coords[0], max_coords[1], max_coords[2]],
            [min_coords[0], max_coords[1], max_coords[2]]
        ])

        quaternion_value = bpy.context.scene.input_rotation
        quaternion_value = (quaternion_value[3], quaternion_value[0], quaternion_value[1], quaternion_value[2])
        rotation_quaternion = Quaternion(quaternion_value)
        rotation_quaternion.normalize()
        euler_rotation = rotation_quaternion.to_euler()

        origin = bbox_center(np.min(bbox, axis=0), np.max(bbox, axis=0))

        translated_bbox = bbox + np.array(bpy.context.scene.input_location)

        center = bbox_center(np.min(translated_bbox, axis=0), np.max(translated_bbox, axis=0))

        rotated_bbox = rotate_bbox(translated_bbox, center - origin, euler_rotation[2])

        center = bbox_center(np.min(rotated_bbox, axis=0), np.max(rotated_bbox, axis=0))

        zone.output_location_rotation = (center[0], center[1], center[2], -np.degrees(euler_rotation[2]))

        dimensions = bbox_dimensions(bbox)
     
        zone.scale = (dimensions[0], dimensions[1], dimensions[2])

        return {'FINISHED'}

class AMV_PT_General_Tools(bpy.types.Panel):
    bl_label = "General"
    bl_idname = "AMV_PT_General_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AMV'
    bl_order = 0

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("amv.setup_light", text="Setup Light", icon="LIGHT")
        row.prop(context.scene, "light_strength", text="Strength")
        layout.prop(context.scene, "bounces", text="Bounces")

        layout.use_property_split = True
        layout.prop(context.scene, "output_directory", text="Output Directory")
        layout.use_property_split = False

        


class AMV_OT_Generate_UUID(bpy.types.Operator):
    bl_idname = "amv.generate_uuid"
    bl_label = "Generate UUID"

    @classmethod
    def poll(cls, context):
        return get_selected_zone(context) is not None

    def execute(self, context):
        random_bytes = np.random.bytes(8)
        hex_bytes = ''.join(f"{x:02X}" for x in random_bytes)
        formatted_uuid = '0x' + hex_bytes[:16]

        random_bytes = np.random.bytes(8)
        hex_bytes = ''.join(f"{x:02X}" for x in random_bytes)
        formatted_guid = '0x' + hex_bytes[:16]
        zone = get_selected_zone(context)

        zone.uuid = formatted_uuid
        zone.guid = formatted_guid

        return {'FINISHED'}


class AMV_UL_ZONES_LIST(bpy.types.UIList):
    bl_idname = "AMV_UL_ZONES_LIST"
    item_icon = "PRESET"


class AMV_OT_Create_Zone(bpy.types.Operator):
    bl_idname = "amv.create_zone"
    bl_label = "Create Zone"

    def execute(self, context):
        zones = context.scene.zones
        item_id = get_new_item_id(zones)
        item = zones.add()
        item.id = item_id
        item.name = f"Zone.{item.id}"
        return {'FINISHED'}
    

class AMV_OT_Delete_Zone(bpy.types.Operator):
    bl_idname = "amv.delete_zone"
    bl_label = "Delete Zone"

    @classmethod
    def poll(cls, context):
        return get_selected_zone(context) is not None
    
    def execute(self, context):
       
        zone = get_selected_zone(context) 
        collection_name = 'Probes-' + zone.name
    
        if collection_name in bpy.data.collections:
            probes_collection = bpy.data.collections.get(collection_name)
            for obj in probes_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(probes_collection, do_unlink=True)
            
        zones = context.scene.zones
        zone_index = context.scene.zone_index 
        zones.remove(zone_index)   
        context.space_data.show_gizmo = context.space_data.show_gizmo
        return {'FINISHED'}
  

class AMV_OT_Set_Bounds_From_Selection(bpy.types.Operator):
    bl_idname = "amv.set_bounds_from_selection"
    bl_label = "Set Bounds From Selection"

    @classmethod
    def poll(cls, context):
        return get_selected_zone(context) is not None and (context.active_object and context.active_object.mode == "EDIT")

    def execute(self, context):
        selected_zone = get_selected_zone(context)
        selected_verts = []
        for obj in context.objects_in_mode:
            selected_verts.extend(get_selected_vertices(obj))
        if not len(selected_verts) > 1:
            self.message("You must select at least 2 vertices!")
            return False
        
        vec_array = np.array(selected_verts)

        max_components = np.max(vec_array, axis=0)
        min_components = np.min(vec_array, axis=0)

        selected_zone.bb_max = Vector(max_components)
        selected_zone.bb_min = Vector(min_components)

        return {'FINISHED'}  


def get_selected_zone(context) -> 'Zone_Properties':
    zones = context.scene.zones
    zone_index = context.scene.zone_index
    if 0 <= zone_index < len(zones):
        return zones[zone_index]
    else:
        return None

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


class Zone_Properties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    bb_min: bpy.props.FloatVectorProperty(name="Bounds Min", subtype="XYZ")
    bb_max: bpy.props.FloatVectorProperty(name="Bounds Max", subtype="XYZ")
    uuid: bpy.props.StringProperty(name="UUID", default="00000000000000000000")
    guid: bpy.props.StringProperty(name="GUID", default="00000000000000000000")
    interval: bpy.props.FloatProperty(name="Interval", default=1.0, min=0.1)
    offset: bpy.props.FloatVectorProperty(name="Offset", default=(0.5, 0.5, 0.5), update=update_probes_offset)
    sphere_radius: bpy.props.FloatProperty(name="Sphere Radius", default=0.15, min=0.05)
    output_location_rotation: bpy.props.FloatVectorProperty(name="Location + Rot", size=4)
    scale: bpy.props.FloatVectorProperty(name="Scale", default=(0.0, 0.0, 0.0))
    force_color: bpy.props.FloatProperty(name="Force Color", default=0.0, min=0.0, max=1.0)


    id: bpy.props.IntProperty(name="Id")
    size: bpy.props.IntVectorProperty(name="Size", default=(0, 0, 0))
    probes_location_3d: bpy.props.StringProperty(name="Probes Location 3D Array", default="[]")


classes = (
    AMV_PT_Tools,
    AMV_PT_Location_Tools,
    AMV_OT_Calculate_Position,
    AMV_PT_General_Tools,
    AMV_OT_Generate_UUID,
    AMV_OT_Create_Zone,
    AMV_OT_Delete_Zone,
    Zone_Properties,
    AMV_UL_ZONES_LIST,
    AMV_OT_Set_Bounds_From_Selection
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.output_directory = bpy.props.StringProperty(name="Output Directory", subtype='DIR_PATH')
    bpy.types.Scene.interior_name = bpy.props.StringProperty(name="Interior Name")
    bpy.types.Scene.input_location = bpy.props.FloatVectorProperty(name="Interior Location")
    bpy.types.Scene.input_rotation = bpy.props.FloatVectorProperty(name="Interior Rotation", size=4)
    bpy.types.Scene.light_strength = bpy.props.FloatProperty(name="Light Strength", update=update_light_strength, default=0.5)
    bpy.types.Scene.zones = bpy.props.CollectionProperty(type=Zone_Properties, name="Zones")
    bpy.types.Scene.zone_index = bpy.props.IntProperty(name="Zone Index", default=0)
    bpy.types.Scene.proggress = bpy.props.StringProperty(default="Bake AMV")
    bpy.types.Scene.bounces = bpy.props.IntProperty(name="Bounces", default=0)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.output_directory
    del bpy.types.Scene.input_location
    del bpy.types.Scene.input_rotation
    del bpy.types.Scene.interior_name
    del bpy.types.Scene.light_strength
    del bpy.types.Scene.zones
    del bpy.types.Scene.zone_index


if __name__ == "__main__":
    register()
