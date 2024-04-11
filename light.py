import bpy

class AMV_OT_SetupLight(bpy.types.Operator):
    bl_idname = "amv.setup_light"
    bl_label = "Setup Light"

    def execute(self, context):

        if "Light" in bpy.data.objects:
            self.report({"INFO"}, "Light object already exist!")
            return {'CANCELLED'}


        bpy.ops.mesh.primitive_uv_sphere_add(radius=400, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        obj = bpy.context.object
        obj.name = "Light"

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
        bpy.context.scene.light_strength = bpy.context.scene.light_strength
        return {'FINISHED'}

classes = (
    AMV_OT_SetupLight,  
)
  
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)