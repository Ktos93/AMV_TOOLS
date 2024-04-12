import bpy

class AMV_OT_SetupLight(bpy.types.Operator):
    bl_idname = "amv.setup_light"
    bl_label = "Setup Light"

    @classmethod
    def poll(cls, context):
        if "Emission" not in bpy.data.worlds["World"].node_tree.nodes:
            return True
        return False

    def execute(self, context):

        world = bpy.data.worlds["World"]

        world.use_nodes = True

        world.node_tree.nodes.clear()

        emission_node = world.node_tree.nodes.new(type='ShaderNodeEmission')

        emission_node.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)

        world_output_node = world.node_tree.nodes.new(type='ShaderNodeOutputWorld')
        world.node_tree.links.new(emission_node.outputs[0], world_output_node.inputs[0])
        world.node_tree.nodes["Emission"].inputs[1].default_value = bpy.context.scene.light_strength

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