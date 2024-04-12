import bpy
import bmesh
import numpy as np
import json

from .main import  get_selected_zone
from .utils import calculate_sphere_counts 

class AMV_OT_DisplayProbes(bpy.types.Operator):
    bl_idname = "amv.display_probes"
    bl_label = "Display Probes"

    @classmethod
    def poll(cls, context):
        zone = get_selected_zone(context) 
        if zone is None:
            return False
        if 'Probes-' + zone.name in bpy.data.collections:
            return False
        if np.count_nonzero(zone.bb_max) == 0 and np.count_nonzero(zone.bb_min) == 0:
            return False
        return True


    def execute(self, context):

        zone = get_selected_zone(context) 

        interval, sphere_radius = zone.interval , zone.sphere_radius

        num_x_spheres, num_y_spheres, num_z_spheres = calculate_sphere_counts(interval, zone.bb_min, zone.bb_max)

        total_spheres = num_x_spheres * num_y_spheres * num_z_spheres
        

        collection_name = "Probes-" + zone.name
        probes_collection = bpy.data.collections.get(collection_name)
        if probes_collection is None:
            probes_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(probes_collection)

        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=sphere_radius)
        orig_sphere = bpy.context.active_object
        orig_sphere.name = "Probe"
        obj_old_coll = orig_sphere.users_collection
        probes_collection.objects.link(orig_sphere)
        
        for ob in obj_old_coll:
            ob.objects.unlink(orig_sphere)

 
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        obj_old_coll = plane.users_collection
        probes_collection.objects.link(plane)
        for ob in obj_old_coll:
            ob.objects.unlink(plane)
        bpy.context.object.instance_type = 'VERTS'
        me = plane.data
        bm = bmesh.new()

        probes_location_3d = json.loads(zone.probes_location_3d)

        if len(probes_location_3d) > 0:
            for i in range(num_z_spheres):
                for j in range(num_y_spheres):
                    for k in range(num_x_spheres):
                        x = probes_location_3d[i][j][k][0]
                        y = probes_location_3d[i][j][k][1]
                        z = probes_location_3d[i][j][k][2]
                        bm.verts.new().co = (x, y, z)

        else:
            for i in range(num_z_spheres):
                for j in range(num_y_spheres):
                    for k in range(num_x_spheres):
                        x = zone.bb_min[0] + k * interval
                        y = zone.bb_min[1] + j * interval
                        z = zone.bb_min[2] + i * interval
                        bm.verts.new().co = (x, y, z)
              

        bm.to_mesh(me)

        orig_sphere.parent = plane
        bpy.ops.object.duplicates_make_real()
        bpy.data.objects.remove(plane, do_unlink=True)
        bpy.data.objects.remove(orig_sphere, do_unlink=True)

        zone.size = (num_x_spheres, num_y_spheres, num_z_spheres)
        
        bpy.ops.object.shade_smooth()  
         
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                obj["offset"] = (0, 0, 0)
                
        if len(probes_location_3d) > 0:
            zone.offset = (0.0,0.0,0.0)
        else:
            start_offset = interval/2
            zone.offset = (start_offset,start_offset,start_offset)
                
  
     
        return {'FINISHED'}
    

class AMV_OT_DeleteProbes(bpy.types.Operator):
    bl_idname = "amv.delete_probes"
    bl_label = "Hide Probes"

    @classmethod
    def poll(cls, context):
        zone = get_selected_zone(context) 
        if zone is None:
            return False
        if not 'Probes-' + zone.name in bpy.data.collections:
            return False
        return True


    def execute(self, context):

        zone = get_selected_zone(context) 
        collection_name = 'Probes-' + zone.name
    
        if collection_name in bpy.data.collections:
            probes_collection = bpy.data.collections.get(collection_name)
            for obj in probes_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(probes_collection, do_unlink=True)
        return {'FINISHED'}


class AMV_OT_SaveProbesLocation(bpy.types.Operator):
    bl_idname = "amv.save_probes"
    bl_label = "Save Probes Location"


    @classmethod
    def poll(cls, context):
        zone = get_selected_zone(context) 
        if zone is None:
            return False
        if not 'Probes-' + zone.name in bpy.data.collections:
            return False
        return True

    def execute(self, context):
        zone = get_selected_zone(context) 

        probes_location_3d = []
        size = zone.size

        probes_location_3d = [[[0 for k in range(size[0])] for j in range(size[1])] for i in range(size[2])]

        collection_name = 'Probes-' + zone.name
        if collection_name in bpy.data.collections:
            probes_collection = bpy.data.collections.get(collection_name)

        index = 0
        for i in range(size[2]):
            for j in range(size[1]):
                for k in range(size[0]):
                    location = probes_collection.objects[index].location
                    probes_location_3d[i][j][k] = [location[0], location[1], location[2]]
                    index += 1

        zone.probes_location_3d = json.dumps(probes_location_3d)
        return {'FINISHED'}


class AMV_OT_ClearProbesLocation(bpy.types.Operator):
    bl_idname = "amv.clear_probes"
    bl_label = "Clear Probes location"

    @classmethod
    def poll(cls, context):
        zone = get_selected_zone(context) 
        if zone is None:
            return False
        return True

    def execute(self, context):
        zone = get_selected_zone(context) 
        zone.probes_location_3d = "[]"
        return {'FINISHED'}


classes = (
   
    AMV_OT_DisplayProbes,
    AMV_OT_DeleteProbes,
    AMV_OT_SaveProbesLocation,
    AMV_OT_ClearProbesLocation,
     
)
  

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)