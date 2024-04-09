import bpy
import bmesh
import numpy as np
import json
import os
from bpy.types import Gizmo, GizmoGroup
from mathutils import Vector, Quaternion

def get_object_bounds(obj):
    min_x, min_y, min_z = obj.bound_box[0]
    max_x, max_y, max_z = obj.bound_box[6]
    return min_x, min_y, min_z, max_x, max_y, max_z


def calculate_sphere_counts(interval, min_x, min_y, min_z, max_x, max_y, max_z):
    num_x_spheres = round((max_x - min_x) / interval)
    num_y_spheres = round((max_y - min_y) / interval)
    num_z_spheres = round((max_z - min_z) / interval)
    return num_x_spheres, num_y_spheres, num_z_spheres


def setup_bake_settings():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.bake.target = 'VERTEX_COLORS'
    scene.cycles.bake_type = 'DIFFUSE'
    scene.render.use_bake_selected_to_active = False
    scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = False
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.cycles.use_adaptive_sampling = False
    bpy.context.scene.cycles.use_denoising = False
    bpy.context.scene.cycles.device = 'CPU'



def get_parameters():
    scene = bpy.context.scene
    interval = scene.interval
    offset = scene.offset
    sphere_radius = scene.sphere_radius
    texture_option = scene.texture_option
    return interval, offset, sphere_radius, texture_option


class BakeAMVToJSON(bpy.types.Operator):
    bl_idname = "object.bake_amv_to_json"
    bl_label = "Bake AMV to JSON"

    def execute(self, context):
        

        if "Light" not in bpy.data.objects:
            self.report({"INFO"}, 'Light object is missing. Please create the light object.')
            return {'CANCELLED'}
        
        if not bpy.context.selected_objects:
            self.report({"INFO"}, "No mesh objects selected!")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        if obj.type != 'MESH':
            self.report({"INFO"}, "No mesh objects selected!")
            return {'CANCELLED'}

        setup_bake_settings()

        interval, offset, sphere_radius, texture_option = get_parameters()

        min_x, min_y, min_z, max_x, max_y, max_z = get_object_bounds(obj)

        num_x_spheres, num_y_spheres, num_z_spheres = calculate_sphere_counts(interval, min_x, min_y, min_z, max_x,
                                                                             max_y, max_z)

        total_spheres = num_x_spheres * num_y_spheres * num_z_spheres * 3

        colors_3d = []
        current = 0

        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=12, radius=sphere_radius)
        sphere_obj = bpy.context.object
        sphere_obj.select_set(True)
        bpy.context.view_layer.objects.active = sphere_obj

        probes_location_3d = json.loads(bpy.context.scene.probes_location_3d)
        should_use_saved_data = len(probes_location_3d) > 0
        light_rotation = bpy.data.objects['Light'].rotation_euler[2]

        for i in range(num_z_spheres):
            colors_2d = []
            for j in range(num_y_spheres):
                row_colors = []
                for k in range(num_x_spheres):
                    if should_use_saved_data:
                        x, y, z = probes_location_3d[i][j][k]
                        sphere_obj.location = (x, y, z)
                    else:
                        x = min_x + k * interval + offset[0]
                        y = min_y + j * interval + offset[1]
                        z = min_z + i * interval + offset[2]
                        sphere_obj.location = (x, y, z)

                    output_color = [0.0, 0.0, 0.0]
                    for r in range(3):
                        bpy.ops.geometry.color_attribute_add()
                        if texture_option == "TEXTURE_0":
                            if r == 0:
                                bpy.data.objects['Light'].rotation_euler[2] = light_rotation
                            elif r == 1:
                                bpy.data.objects['Light'].rotation_euler[2] = np.pi
                            else:
                                bpy.data.objects['Light'].rotation_euler[2] -= np.pi/2
                        else:
                            if r == 0:
                                bpy.data.objects['Light'].rotation_euler[2] = light_rotation
                            elif r == 1:
                                bpy.data.objects['Light'].rotation_euler[1] = -np.pi/2
                            else:
                                bpy.data.objects['Light'].rotation_euler[1] = np.pi/2

                        bpy.ops.object.bake(type='DIFFUSE')

                        vertex_colors = sphere_obj.data.color_attributes.active.data
                        colors = [vertex_colors[vertex.index].color[:] for vertex in sphere_obj.data.vertices]
                        bpy.ops.geometry.color_attribute_remove()
                        vertex_colors_array = np.array(colors)
                        average_color = np.mean(vertex_colors_array, axis=0)
                        output_color[r] = average_color[0] ## RGB ARE SAME
                        current += 1
                    row_colors.append(output_color)
                colors_2d.append(row_colors)
                bpy.context.scene.proggress = f"{total_spheres}/{current}"
                print(f"{current}/{total_spheres} spheres created", end='\r')
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

            colors_3d.append(colors_2d)

        bpy.data.objects.remove(sphere_obj, do_unlink=True)

        bpy.data.objects['Light'].rotation_euler[2] = light_rotation
        bpy.data.objects['Light'].rotation_euler[1] = 0

        print("\nSpheres creation finished.")

        filepath_full = bpy.path.abspath(bpy.context.scene.output_directory)
        json_filepath = os.path.join(filepath_full, "AMVJSON.json")

        with open(json_filepath, 'w') as json_file:
            json.dump(colors_3d, json_file)
        bpy.context.scene.proggress = "Bake to JSON"
        return {'FINISHED'}


class DisplayProbes(bpy.types.Operator):
    bl_idname = "object.display_probes"
    bl_label = "Display Probes"

    def execute(self, context):
        
        if 'Probes' in bpy.data.collections:
            self.report({"INFO"}, "Probes already displayed!")
            return {'CANCELLED'}
        
        if not bpy.context.selected_objects:
            self.report({"INFO"}, "No mesh objects selected!")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        if obj.type != 'MESH':
            self.report({"INFO"}, "No mesh objects selected!")
            return {'CANCELLED'}

        interval, offset, sphere_radius, _ = get_parameters()

        min_x, min_y, min_z, max_x, max_y, max_z = get_object_bounds(obj)

        num_x_spheres, num_y_spheres, num_z_spheres = calculate_sphere_counts(interval, min_x, min_y, min_z, max_x,
                                                                             max_y, max_z)

        total_spheres = num_x_spheres * num_y_spheres * num_z_spheres * 3
        
        bpy.context.scene.proggress = f"Bake to JSON [{total_spheres}]"

        collection_name = "Probes"
        probes_collection = bpy.data.collections.get(collection_name)
        if probes_collection is None:
            probes_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(probes_collection)

        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=sphere_radius)
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

        probes_location_3d = json.loads(bpy.context.scene.probes_location_3d)

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
                        x = min_x + k * interval
                        y = min_y + j * interval
                        z = min_z + i * interval
                        bm.verts.new().co = (x, y, z)
              

        bm.to_mesh(me)

        orig_sphere.parent = plane
        bpy.ops.object.duplicates_make_real()
        bpy.data.objects.remove(plane, do_unlink=True)
        bpy.data.objects.remove(orig_sphere, do_unlink=True)

        objects_in_collection = probes_collection.objects

        bpy.context.scene.size = (num_x_spheres, num_y_spheres, num_z_spheres)
        
        bpy.ops.object.shade_smooth()  
         
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                obj["offset"] = (0, 0, 0)
                
        if len(probes_location_3d) > 0:
            bpy.context.scene.offset = (0.0,0.0,0.0)
        else:
            start_offset = interval/2
            bpy.context.scene.offset = (start_offset,start_offset,start_offset)
                
  
     
        return {'FINISHED'}
    

class DeleteProbes(bpy.types.Operator):
    bl_idname = "object.delete_probes"
    bl_label = "Delete Probes"

    def execute(self, context):
        collection_name = 'Probes'
    
        if collection_name in bpy.data.collections:
            probes_collection = bpy.data.collections.get(collection_name)
            for obj in probes_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(probes_collection, do_unlink=True)
        return {'FINISHED'}


class SaveProbesLocation(bpy.types.Operator):
    bl_idname = "object.save_probes"
    bl_label = "Save Probes Location"

    def execute(self, context):
        probes_location_3d = []
        size = bpy.context.scene.size

        probes_location_3d = [[[0 for k in range(size[0])] for j in range(size[1])] for i in range(size[2])]

        collection_name = 'Probes'
        if collection_name in bpy.data.collections:
            probes_collection = bpy.data.collections.get(collection_name)

        index = 0
        for i in range(size[2]):
            for j in range(size[1]):
                for k in range(size[0]):
                    location = probes_collection.objects[index].location
                    probes_location_3d[i][j][k] = [location[0], location[1], location[2]]
                    index += 1

        bpy.context.scene.probes_location_3d = json.dumps(probes_location_3d)
        return {'FINISHED'}


class ClearProbesLocation(bpy.types.Operator):
    bl_idname = "object.clear_probes"
    bl_label = "Clear Probes location"

    def execute(self, context):
        bpy.context.scene.probes_location_3d = "[]"
        return {'FINISHED'}


class SetupLight(bpy.types.Operator):
    bl_idname = "object.setup_light"
    bl_label = "SetupLight"

    def execute(self, context):

        if "Light" in bpy.data.objects:
            self.report({"INFO"}, "Light object already exist!")
            return {'CANCELLED'}

        # Define the radius of the half-sphere
        radius = 400.0
        segments = 32

        # Create a new mesh
        mesh = bpy.data.meshes.new("Light")

        # Create a new object and link it to the mesh
        obj = bpy.data.objects.new("Light", mesh)
        bpy.context.collection.objects.link(obj)

        # Create a bmesh
        bm = bmesh.new()

        # Generate the half-sphere vertices with rotation
        for i in range(segments + 1):
            theta = np.pi * i / segments
            for j in range(segments // 2 + 1):
                phi = 2 * np.pi * j / segments
                x = radius * np.sin(theta) * np.cos(phi)
                y = radius * np.sin(theta) * np.sin(phi)
                z = radius * np.cos(theta)
                # Rotate the vertex
                x_rot = x * np.cos(-np.pi / 2) - y * np.sin(-np.pi / 2)
                y_rot = x * np.sin(-np.pi / 2) + y * np.cos(-np.pi / 2)
                bm.verts.new((x_rot, y_rot, z))

        # Create faces
        bm.verts.ensure_lookup_table()
        for i in range(segments):
            for j in range(segments // 2):
                v1 = bm.verts[i * (segments // 2 + 1) + j]
                v2 = bm.verts[(i + 1) * (segments // 2 + 1) + j]
                v3 = bm.verts[(i + 1) * (segments // 2 + 1) + j + 1]
                v4 = bm.verts[i * (segments // 2 + 1) + j + 1]
                bm.faces.new((v1, v2, v3, v4))

        # Update the mesh with the bmesh data
        bm.to_mesh(mesh)
        bm.free()

        # Check if the material already exists
        material_name = "EmissiveMaterial"
        if material_name in bpy.data.materials:
            mat = bpy.data.materials[material_name]
        else:
            # Create a new material if it doesn't exist
            mat = bpy.data.materials.new(name=material_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            emission_node = nodes.new(type='ShaderNodeEmission')
            emission_node.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)  # Adjust the emission color here
            # Link the emission node to the material output
            material_output = nodes.get("Material Output")
            links = mat.node_tree.links
            links.new(emission_node.outputs[0], material_output.inputs[0])

        # Assign the material to the object
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        # hacky refresh
        bpy.context.scene.texture_option = bpy.context.scene.texture_option
        return {'FINISHED'}


def update_light_strength(self, context):
    if "EmissiveMaterial" in bpy.data.materials:
        bpy.data.materials["EmissiveMaterial"].node_tree.nodes["Emission"].inputs[1].default_value = self.light_strength
    

class AMV_PT_TOOLS(bpy.types.Panel):
    bl_label = "AMV Tools"
    bl_idname = "AMV_PT_TOOLS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AMV'
    bl_order = 0

    def draw(self, context):
        layout = self.layout

        layout.operator("object.bake_amv_to_json", text=str(bpy.context.scene.proggress), icon="RENDERLAYERS")
        row = layout.row()
        row.operator("object.setup_light", text="SetupLight", icon="LIGHT")
        row.prop(context.scene, "light_strength", text="Strength")
        
        row = layout.row()
        row.operator("object.display_probes", text="Display Probes", icon="HIDE_OFF")
        row.operator("object.delete_probes", text="Hide Probes", icon="HIDE_ON")
        row = layout.row()
        row.operator("object.save_probes", text="Save Probes Location", icon="FILE_TICK")
        row.operator("object.clear_probes", text="Clear Probes Location", icon="TRASH")
        
        row = layout.row()
        row.prop(context.scene, "offset", text="Offset", icon="MOD_OFFSET")
        row = layout.row()
        row.prop(context.scene, "size", text="Size")
        row.enabled = False
        
        row = layout.row()
        row.prop(context.scene, "output_directory", text="Output Directory")
        row = layout.row()
        row.prop(context.scene, "texture_option", text="Texture Type", icon="TEXTURE")

        
class AMV_PT_LOCATION_TOOLS(bpy.types.Panel):
    bl_label = "Location"
    bl_idname = "AMV_PT_LOCATION_TOOLS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AMV'
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        column.prop(context.scene, "input_location", text="Interior Location")
        column = layout.column()
        column.prop(context.scene, "input_rotation", text="Interior Rotation")
        layout.operator("object.calculate_position", text="Calculate Position")
        column = layout.column()
        column.prop(context.scene, "output_location_rotation", text="Output XYZ + Rot")
        
        
class CalculatePosition(bpy.types.Operator):
    bl_idname = "object.calculate_position"
    bl_label = "Calculate Position"

    def execute(self, context):
        
        if not bpy.context.selected_objects:
            self.report({"INFO"}, "No mesh objects selected!")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        if obj.type != 'MESH':
            self.report({"INFO"}, "No mesh objects selected!")
            return {'CANCELLED'}
        
        
        quaternion_value = bpy.context.scene.input_rotation
        quaternion_value = (quaternion_value[3], quaternion_value[0], quaternion_value[1], quaternion_value[2])

        rotation_quaternion = Quaternion(quaternion_value)
        rotation_quaternion.normalize()
        euler_rotation = rotation_quaternion.to_euler()
        
        obj.location = bpy.context.scene.input_location
        obj.rotation_euler[2] = euler_rotation[2]
        bpy.context.view_layer.update()

        euler_rotation_degrees = [np.degrees(angle) for angle in euler_rotation]

        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        
        bbox_corners_array = np.array([corner[:] for corner in bbox_corners])
        dimensions = np.ptp(bbox_corners_array, axis=0) / 2  # Compute the range (max - min) along each axis

        print("Dimensions (width, height, depth):", dimensions)
    
        # Oblicz środek bound boxa
        center = sum(bbox_corners, Vector()) / 8
    
        bpy.context.scene.output_location_rotation = (center[0], center[1],center[2],-euler_rotation_degrees[2])
        
        
        obj.location = (0,0,0)
        obj.rotation_euler = (0,0,0)
        return {'FINISHED'}
    
class AMV_PT_ADVANCED_TOOLS(bpy.types.Panel):
    bl_label = "Advanced"
    bl_idname = "AMV_PT_ADVANCED_TOOLS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AMV'
    bl_order = 2

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene, "interval", text="Interval", icon="DRIVER_DISTANCE")
        row.prop(context.scene, "sphere_radius", text="Sphere Radius")    


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



def updateProbesOffset(self, context):
    collection_name = 'Probes'
    
    offset = bpy.context.scene.offset
    if collection_name in bpy.data.collections:
        probes_collection = bpy.data.collections.get(collection_name)
        for obj in probes_collection.objects:
            new_offset =  np.array(offset) - np.array(obj["offset"])
            obj.location.x += new_offset[0]
            obj.location.y += new_offset[1]
            obj.location.z += new_offset[2]   
            obj["offset"] = offset

def updateLightDirection(self, context):

    obj = bpy.data.objects['Light']
    # Your code here
    if self.texture_option == "TEXTURE_0":
        target_position = Vector((5.0, 0.0, 0.0))

    else:
        target_position = Vector((-5.0, 0.0, 0.0))

    # Calculate the direction vector from the object to the target
    direction = target_position - obj.location
    direction.normalize()

    # Calculate the rotation quaternion
    rotation_quaternion = direction.to_track_quat('Z', 'Y')

    # Apply the rotation to the object
    obj.rotation_euler = rotation_quaternion.to_euler()

    # If you want to only rotate along Z-axis, you can modify the Euler rotation accordingly
    obj.rotation_euler.x = 0
    obj.rotation_euler.y = 0
    if self.texture_option == "TEXTURE_0":
        obj.rotation_euler.z += -np.pi/2


def register():mo
    bpy.types.Scene.interval = bpy.props.FloatProperty(name="Interval", default=1.0, min=0.1)
    bpy.types.Scene.offset = bpy.props.FloatVectorProperty(name="Offset", default=(0.5, 0.5, 0.5), update=updateProbesOffset)
    bpy.types.Scene.sphere_radius = bpy.props.FloatProperty(name="Sphere Radius", default=0.15, min=0.05)
    bpy.types.Scene.size = bpy.props.IntVectorProperty(name="Size", default=(0, 0, 0))
    bpy.types.Scene.probes_location_3d = bpy.props.StringProperty(name="Probes Location 3D Array", default="[]")
    bpy.types.Scene.output_directory = bpy.props.StringProperty(name="Output Directory", subtype='DIR_PATH')
    bpy.types.Scene.texture_option = bpy.props.EnumProperty(
        items=[('TEXTURE_0', "Texture 0", ""),
               ('TEXTURE_1', "Texture 1", "")],
        name="Texture Option",
        update=updateLightDirection
    )
    bpy.types.Scene.input_location = bpy.props.FloatVectorProperty(name="Interior Location")
    bpy.types.Scene.input_rotation = bpy.props.FloatVectorProperty(name="Interior Rotation" ,size=4)
    bpy.types.Scene.output_location_rotation = bpy.props.FloatVectorProperty(name="My Vector",size=4)
    bpy.types.Scene.show_gizmo = bpy.props.BoolProperty(name="Show Gizmo", default=True)
    bpy.types.Scene.proggress = bpy.props.StringProperty(default="Bake to JSON")
    bpy.types.Scene.light_strength = bpy.props.FloatProperty(name="Light Strength",update=update_light_strength, default=1.0)


def unregister():
    del bpy.types.Scene.interval
    del bpy.types.Scene.offset
    del bpy.types.Scene.sphere_radius
    del bpy.types.Scene.size
    del bpy.types.Scene.probes_location_3d
    del bpy.types.Scene.output_directory
    del bpy.types.Scene.texture_option
    del bpy.types.Scene.input_location
    del bpy.types.Scene.input_rotation
    del bpy.types.Scene.output_location_rotation
    del bpy.types.Scene.show_gizmo
    del bpy.types.Scene.proggress
    del bpy.types.Scene.light_strength




if __name__ == "__main__":
    register()