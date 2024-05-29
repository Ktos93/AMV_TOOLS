import bpy
import xml.etree.ElementTree as ET

def create_xml_file(file_path, zone):
    # Tworzenie głównego elementu <Item>
    item_element = ET.Element("Item")
    
    # Dodawanie podelementów do elementu <Item>
    ET.SubElement(item_element, "enabled", value="True")
    
    loc_rot = zone.output_location_rotation
    ET.SubElement(item_element, "position", x="{:.4f}".format(loc_rot[0]), y="{:.4f}".format(loc_rot[1]), z="{:.4f}".format(loc_rot[2]))
    
    ET.SubElement(item_element, "rotation", x="{:.4f}".format(loc_rot[3]), y="0", z="0")
   
    scale = zone.scale
    ET.SubElement(item_element, "scale", x="{:.5f}".format(scale[0]), y="{:.5f}".format(scale[1]), z="{:.5f}".format(scale[2]))

    ET.SubElement(item_element, "falloffScaleMin", x="1", y="1", z="1")
    
    ET.SubElement(item_element, "falloffScaleMax", x="1.2", y="1.2", z="1.2")
    
    ET.SubElement(item_element, "samplingOffsetStrength", value="0")
    
    ET.SubElement(item_element, "falloffPower", value="12")
    
    ET.SubElement(item_element, "distance", value="-1")
    
    size = scale = zone.size
    ET.SubElement(item_element, "cellCountX", value=str(size[0]))
    
    ET.SubElement(item_element, "cellCountY", value=str(size[1]))
    
    ET.SubElement(item_element, "cellCountZ", value=str(size[2]))
    
    ET.SubElement(item_element, "clipPlane0", x="0", y="0", z="0", w="1")
    
    ET.SubElement(item_element, "clipPlane1", x="0", y="0", z="0", w="1")
    
    ET.SubElement(item_element, "clipPlane2", x="0", y="0", z="0", w="1")
    
    ET.SubElement(item_element, "clipPlane3", x="0", y="0", z="0", w="1")
    
    ET.SubElement(item_element, "clipPlaneBlend0", value="0")
    
    ET.SubElement(item_element, "clipPlaneBlend1", value="0")
    
    ET.SubElement(item_element, "clipPlaneBlend2", value="0")
    
    ET.SubElement(item_element, "clipPlaneBlend3", value="0")
    
    ET.SubElement(item_element, "blendingMode").text = "BM_Lerp"
    
    ET.SubElement(item_element, "layer", value="0")
    
    ET.SubElement(item_element, "order", value="5")
    
    ET.SubElement(item_element, "natural", value="True")
    
    ET.SubElement(item_element, "attachedToDoor", value="False")
    
    ET.SubElement(item_element, "interior", value="True")
    
    ET.SubElement(item_element, "exterior", value="False")
    
    ET.SubElement(item_element, "vehicleInterior", value="False")
    
    ET.SubElement(item_element, "sourceFolder").text = "AMV_TOOL"
    
    uuid = zone.uuid
    ET.SubElement(item_element, "uuid", value=uuid)
    
    ET.SubElement(item_element, "iplHash", value="0")
    
    tree = ET.ElementTree(item_element)
    
    ET.indent(tree, space="\t", level=0)
    
    tree.write(file_path, xml_declaration=True, encoding="utf-8")    


def create_xml_file_reflection_probes(file_path, uuid):
    root = ET.Element("RDR2TextureDictionary", version="1")

    textures = ET.SubElement(root, "Textures")

    common_dimension = "TextureCube"
    common_flags = "402685954"

    items = [
        {"Name": f"{uuid}_d", "SRVUnknown08": "5378212016"},
        {"Name": f"{uuid}_1"},
        {"Name": f"{uuid}_0"}
    ]

    for item_data in items:
        item = ET.SubElement(textures, "Item")
        name = ET.SubElement(item, "Name")
        name.text = item_data["Name"]

        dimension = ET.SubElement(item, "Dimension")
        dimension.text = common_dimension

        ET.SubElement(item, "Flags", value=common_flags)
        
        if "SRVUnknown08" in item_data:
            ET.SubElement(item, "SRVUnknown08", value=item_data["SRVUnknown08"])


    tree = ET.ElementTree(root)
    
    ET.indent(tree, space="\t", level=0)

    tree.write(file_path, xml_declaration=True, encoding="utf-8")    


def create_xml_file_reflection_probes_room(file_path, zone):
    root = ET.Element("reflectionProbes", itemType="CReflectionProbeData")

    item = ET.SubElement(root, "Item")

    bbmin = zone.bb_min
    bbmax = zone.bb_max
    min_extents = ET.SubElement(item, "minExtents")
    min_extents.set("x", "{:.6f}".format(bbmin[0]))
    min_extents.set("y", "{:.6f}".format(bbmin[1]))
    min_extents.set("z", "{:.6f}".format(bbmin[2]))

    max_extents = ET.SubElement(item, "maxExtents")
    max_extents.set("x", "{:.6f}".format(bbmax[0]))
    max_extents.set("y", "{:.6f}".format(bbmax[1]))
    max_extents.set("z", "{:.6f}".format(bbmax[2]))

    rotation = ET.SubElement(item, "rotation")
    rotation.set("x", "0")
    rotation.set("y", "0")
    rotation.set("z", "0")
    rotation.set("w", "1")

    center_offset = ET.SubElement(item, "centerOffset")
    center_offset.set("x", "0")
    center_offset.set("y", "0")
    center_offset.set("z", "0")

    influence_extents = ET.SubElement(item, "influenceExtents")
    influence_extents.set("x", "1")
    influence_extents.set("y", "1")
    influence_extents.set("z", "1")

    probe_priority = ET.SubElement(item, "probePriority")
    probe_priority.set("value", "255")

    guid = ET.SubElement(item, "guid")
    guid.set("value", zone.guid)

    tree = ET.ElementTree(root)
    
    ET.indent(tree, space="\t", level=0)

    tree.write(file_path, xml_declaration=True, encoding="utf-8")    

