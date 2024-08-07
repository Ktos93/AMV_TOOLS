import bpy
import numpy as np
import json
import os
import subprocess
import tifffile as tiff
from .main import get_selected_zone
from .xml import create_xml_file
from .utils import setup_bake_settings , calculate_sphere_counts


def process_colors_3d(colors_3d, intuuid, index, new_folder_path, texconv_path):
    images = []
    if isinstance(colors_3d, list):
        for two_d_array in colors_3d:
            image_data = np.array(two_d_array, dtype=np.float32)
            images.append(image_data)
            
        output_tiff_path = os.path.join(new_folder_path, f"{intuuid}_{index}.tiff")
        tiff.imwrite(output_tiff_path, np.array(images, dtype=np.float32))

        subprocess.run([
            texconv_path,
            '-f', 'R11G11B10_FLOAT',
            '-y',
            '-m', '1',
            '-o', new_folder_path,
            output_tiff_path
        ])
        os.remove(output_tiff_path)


class AMV_OT_BakeAMVToJSON(bpy.types.Operator):
    bl_idname = "amv.bake_amv_to_json"
    bl_label = "Bake AMV to JSON"

    @classmethod
    def poll(cls, context):
        zone = get_selected_zone(context) 
        if zone is None:
            return False
        if 'Probes-' + zone.name in bpy.data.collections:
            return False
        if "Emission" not in bpy.data.worlds["World"].node_tree.nodes:
            return False
        return True


    def execute(self, context):
        
        setup_bake_settings()

        zone = get_selected_zone(context) 

        interval, sphere_radius, offset, force_color = zone.interval , zone.sphere_radius , zone.offset, zone.force_color

        num_x_spheres, num_y_spheres, num_z_spheres = calculate_sphere_counts(interval, zone.bb_min, zone.bb_max)

        total_spheres = num_x_spheres * num_y_spheres * num_z_spheres
        
        colors_3d_0 = []
        colors_3d_1 = []
        current = 0

        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=sphere_radius)
        sphere_obj = bpy.context.object
        sphere_obj.select_set(True)
        bpy.context.view_layer.objects.active = sphere_obj

        probes_location_3d = json.loads(zone.probes_location_3d)
        should_use_saved_data = len(probes_location_3d) > 0

        for i in range(num_z_spheres):
            colors_2d_0 = []
            colors_2d_1 = []
            for j in range(num_y_spheres):
                row_colors_0 = []
                row_colors_1 = []
                for k in range(num_x_spheres):
                    if should_use_saved_data:
                        x, y, z = probes_location_3d[i][j][k]
                        sphere_obj.location = (x, y, z)
                    else:
                        x = zone.bb_min[0] + k * interval + offset[0]
                        y = zone.bb_min[1] + j * interval + offset[1]
                        z = zone.bb_min[2] + i * interval + offset[2]
                        sphere_obj.location = (x, y, z)
                    if force_color > 0:
                        output_color_0 = [force_color,force_color,force_color]
                        output_color_1 = [force_color,force_color,force_color] 
                        
                        row_colors_0.append(output_color_0)
                        row_colors_1.append(output_color_1)   

                    else:    
                        bpy.ops.geometry.color_attribute_add()
                                
                        bpy.ops.object.bake(type='DIFFUSE')
                                    
                        vertices = sphere_obj.data.vertices
                        vertex_colors = sphere_obj.data.color_attributes.active.data
                                
                        median_x = sum([v.co.x for v in vertices]) / len(vertices)
                        median_y = sum([v.co.y for v in vertices]) / len(vertices)
                        median_z = sum([v.co.z for v in vertices]) / len(vertices)
                        
                        color_array = [[],[],[],[],[],[]]
                        
                        for v in vertices:

                            if v.co.x >= median_x:
                                color_array[0].append(vertex_colors[v.index].color[:])
                            else:
                                color_array[1].append(vertex_colors[v.index].color[:])   
                        
                        for v in vertices:
                            if v.co.y >= median_y:
                                color_array[2].append(vertex_colors[v.index].color[:])
                            else:
                                color_array[3].append(vertex_colors[v.index].color[:])   
                        
                        for v in vertices:
                            if v.co.z >= median_z:
                                color_array[4].append(vertex_colors[v.index].color[:])
                            else:
                                color_array[5].append(vertex_colors[v.index].color[:])
                                
                    
                        r_0 =  np.mean(np.array(color_array[0]), axis=0)
                        g_0 =  np.mean(np.array(color_array[1]), axis=0)
                        b_0 =  np.mean(np.array(color_array[2]), axis=0)
                        
                        r_1 =  np.mean(np.array(color_array[3]), axis=0)
                        g_1 =  np.mean(np.array(color_array[4]), axis=0)
                        b_1 =  np.mean(np.array(color_array[5]), axis=0)
                    
                        r_0 =  np.mean(r_0[:3])
                        g_0 =  np.mean(g_0[:3])
                        b_0 =  np.mean(b_0[:3])
                        
                        r_1 =  np.mean(r_1[:3])
                        g_1 =  np.mean(g_1[:3])
                        b_1 =  np.mean(b_1[:3])
    
                        current += 1
                        output_color_0 = [r_0,g_0,b_0]
                        output_color_1 = [r_1,g_1,b_1]
                                
                        bpy.ops.geometry.color_attribute_remove() 
                        
                        row_colors_0.append(output_color_0)
                        row_colors_1.append(output_color_1)
                    
                colors_2d_0.append(row_colors_0)
                colors_2d_1.append(row_colors_1)
                
                bpy.context.scene.proggress = f"{total_spheres}/{current}"
                print(f"{current}/{total_spheres} spheres created", end='\r')
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

            colors_3d_0.append(colors_2d_0)
            colors_3d_1.append(colors_2d_1)

        bpy.data.objects.remove(sphere_obj, do_unlink=True)

        print("\nSpheres baking finished.")

        filepath_full = bpy.path.abspath(bpy.context.scene.output_directory)
        
        uuid = zone.uuid
        
        new_folder_path = os.path.join(filepath_full, uuid)
        
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
         
        intuuid = str(int(uuid, 16))
        addon_directory = os.path.dirname(__file__)
        texconv_path = os.path.join(addon_directory, "[CONVERTER]", "texconv.exe")
       
        process_colors_3d(colors_3d_0, intuuid, 0, new_folder_path, texconv_path)
        process_colors_3d(colors_3d_1, intuuid, 1, new_folder_path, texconv_path)
        
        xml_filepath = os.path.join(new_folder_path, uuid + ".xml")
        create_xml_file(xml_filepath, zone)     
            
        bpy.context.scene.proggress = "Bake AMV"
        return {'FINISHED'}
    

classes = (
    AMV_OT_BakeAMVToJSON,
)
  

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)