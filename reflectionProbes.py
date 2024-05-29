import bpy
import os
from mathutils import Quaternion
from .main import get_selected_zone
from.converRefProbes import convertRefProbes
from.utils import gen_hash, compute_probe_hash
from .xml import create_xml_file_reflection_probes_room

camera_names = ['z+', 'z-', 'y+', 'y-', 'x+', 'x-']

camera_directions = [
    (0, 0, -3.146), 
    (0, 3.146, 3.146), 
    (-1.5708, 0, 0), 
    (1.5708, 0, 0),  
    (0, -1.5708, 3.146), 
    (0, 1.5708, 3.146)
]

texture_types = ["normal", "depth", "color", "ao"]

def SetupProbesComposting(type):
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_depth = '8'
    bpy.context.scene.render.image_settings.color_mode = 'RGB'

    # Włącz tryb kompozytowy
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    # Usuń istniejące węzły
    for node in tree.nodes:
        tree.nodes.remove(node)
        
    bpy.context.scene.view_settings.look = 'None'   
    bpy.context.scene.view_settings.exposure = 0
    bpy.context.scene.view_settings.gamma = 1
    
        
    match type:
        case "depth":
            bpy.context.scene.view_settings.view_transform = 'AgX'
            bpy.context.scene.sequencer_colorspace_settings.name = 'Non-Color'
            bpy.context.scene.view_layers["ViewLayer"].use_pass_z = True
            render_layers = tree.nodes.new(type='CompositorNodeRLayers')
            normalize = tree.nodes.new(type='CompositorNodeNormalize')
            composite = tree.nodes.new(type='CompositorNodeComposite')
            tree.links.new(render_layers.outputs['Depth'], normalize.inputs['Value'])
            tree.links.new(normalize.outputs['Value'], composite.inputs['Image'])    
            
        case "ao":
            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 1
            bpy.context.scene.view_settings.view_transform = 'AgX'
            bpy.context.scene.sequencer_colorspace_settings.name = 'Non-Color'
            bpy.context.scene.view_layers["ViewLayer"].use_pass_ambient_occlusion = True
            render_layers = tree.nodes.new(type='CompositorNodeRLayers')
            composite = tree.nodes.new(type='CompositorNodeComposite')
            tree.links.new(render_layers.outputs['AO'], composite.inputs['Image'])
            
        case "color":
            bpy.context.scene.view_settings.view_transform = 'AgX'
            bpy.context.scene.sequencer_colorspace_settings.name = 'sRGB'
            bpy.context.scene.view_layers["ViewLayer"].use_pass_diffuse_color = True
            render_layers = tree.nodes.new(type='CompositorNodeRLayers')
            composite = tree.nodes.new(type='CompositorNodeComposite')
            tree.links.new(render_layers.outputs['DiffCol'], composite.inputs['Image'])
            
        case "normal":
            bpy.context.scene.view_settings.view_transform = 'Raw'
            bpy.context.scene.sequencer_colorspace_settings.name = 'Non-Color'
            bpy.context.scene.view_layers["ViewLayer"].use_pass_normal = True
            
            render_layers = tree.nodes.new(type='CompositorNodeRLayers')
            composite = tree.nodes.new(type='CompositorNodeComposite')
            
            multiply = tree.nodes.new(type='CompositorNodeMixRGB')
            multiply.blend_type = 'MULTIPLY'
            multiply.inputs[0].default_value = 1.0

            combine_xyz_1 = tree.nodes.new(type='CompositorNodeCombineXYZ')
            combine_xyz_1.inputs['X'].default_value = 0.5
            combine_xyz_1.inputs['Y'].default_value = 0.5
            combine_xyz_1.inputs['Z'].default_value = 0.5

            add = tree.nodes.new(type='CompositorNodeMixRGB')
            add.blend_type = 'ADD'
            add.inputs[0].default_value = 1.0

            combine_xyz_2 = tree.nodes.new(type='CompositorNodeCombineXYZ')
            combine_xyz_2.inputs['X'].default_value = 0.5
            combine_xyz_2.inputs['Y'].default_value = 0.5
            combine_xyz_2.inputs['Z'].default_value = 0.5

            tree.links.new(render_layers.outputs['Normal'], multiply.inputs[1])
            tree.links.new(combine_xyz_1.outputs['Vector'], multiply.inputs[2])
            tree.links.new(multiply.outputs['Image'], add.inputs[1])
            tree.links.new(combine_xyz_2.outputs['Vector'], add.inputs[2])
            tree.links.new(add.outputs['Image'], composite.inputs['Image'])
                        
import numpy as np
class AMV_OT_BakeReflectionProbes(bpy.types.Operator):
    bl_idname = "amv.bake_reflection_probes"
    bl_label = "Bake Reflection Probes"

    @classmethod
    def poll(cls, context):
        zone = get_selected_zone(context) 
        if zone is None:
            return False
        return True


    def execute(self, context):
        
        zone = get_selected_zone(context) 

        center = tuple((min_val + max_val) / 2 for min_val, max_val in zip(zone.bb_min, zone.bb_max))

        quaternion_value = bpy.context.scene.input_rotation
        quaternion_value = (quaternion_value[3], quaternion_value[0], quaternion_value[1], quaternion_value[2])
        rotation_quaternion = Quaternion(quaternion_value)
        rotation_quaternion.normalize()
        interior_rotation = rotation_quaternion.to_euler()

        print(np.degrees(interior_rotation[2]))

        for type in texture_types:

            SetupProbesComposting(type)

            for i, (name, direction) in enumerate(zip(camera_names, camera_directions)):
                bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=center, rotation=(0, 0, 0))
                bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))

                camera = bpy.context.object
                camera.name = name
                camera.rotation_mode = 'XYZ'
                camera.rotation_euler =  tuple(a - b for a, b in zip(direction, interior_rotation))

                camera.data.lens = 16
                camera.data.angle = 1.570
                camera.data.type = 'PERSP'

                bpy.context.scene.render.resolution_x = 1024
                bpy.context.scene.render.resolution_y = 1024
                
                bpy.context.scene.camera = camera

                bpy.ops.render.render(write_still=True)

                filepath_full = bpy.path.abspath(bpy.context.scene.output_directory)

                dir_name = zone.name + "_ref_probes"
 
                new_folder_path = os.path.join(filepath_full, dir_name)

                type_folder_path = os.path.join(new_folder_path, type)

                file_path = os.path.join(type_folder_path, f"{name}.png")
        
                bpy.data.images['Render Result'].save_render(file_path)
                bpy.data.objects.remove(camera, do_unlink=True)

        tree = bpy.context.scene.node_tree
        for node in tree.nodes:
            tree.nodes.remove(node)

        bpy.context.scene.use_nodes = False

        interior_name = bpy.context.scene.interior_name
        interior_hash = gen_hash(interior_name)
        guid = int(zone.guid, 16)
        data = [guid >> 32, guid & 0xFFFFFFFF, interior_hash]
        probe_hash = compute_probe_hash(data, 0)

        convertRefProbes(new_folder_path, probe_hash)
        xml_ytyp_filename = os.path.join(new_folder_path, "output", f"{probe_hash}_YTYP.xml")
        create_xml_file_reflection_probes_room(xml_ytyp_filename, zone)
        return {'FINISHED'}
    

classes = (
    AMV_OT_BakeReflectionProbes,
)
  

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)