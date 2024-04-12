# AMV TOOLS (Ambient Mask Volume) - Blender Addon

## Introduction
This addon is specifically designed to assist in creating ambient mask volumes within the Blender environment

## Features
- **Efficient Volume Creation**: Easily create ambient mask volumes for environments directly within Blender.
- **Customization Options**: Adjust various parameters to fine-tune the appearance and behavior of ambient mask volumes.

## Installation
1. Download the addon ZIP file from the releases section.
2. Open Blender and navigate to Edit > Preferences > Add-ons.
3. Click "Install" and select the downloaded ZIP file.
4. Enable the addon by checking the box next to "AMV TOOLS" in the Add-ons list.

## Usage
1. After installation, you can find the addon's features within the Blender interface.
2. Refer to the documentation or tooltips provided within Blender for detailed instructions on each feature.
3. Once you've created your AMV and saved it as a JSON file (e.g., AMVJSON.json), drag and drop this file onto the JSON_TO_AMV.bat file to convert it to the DDS format with the appropriate settings.

## Credits
This addon utilizes the `texconv` tool developed by Microsoft. Special thanks to Microsoft for providing this invaluable tool for texture conversion.
   
## License
This addon is distributed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html). See the LICENSE file for details.


## Detailed Usage
1. Install AMV Tools plugin to Blender. If you're getting an error "No module named 'tifffile'", restart Blender.
2. Choose your output directory, where generated XML and .DDS files will be saved.
![2-directory](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/1a026172-643a-4aa7-86ce-ad2f275517c4)

3. Open a scene with your model or import it.
![3-import](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/d75b73ec-1433-4820-9f45-cdb263edc1ed)

4. Click on the + icon to create a new AMV entry.
![4-create](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/f5c02a68-aa6d-4cc7-bcee-9af5b743cff8)

5. Go to Edit mode, select all vertices and click Set Bounds From Selection.
![5-editmode](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/e7c23a62-7361-43ba-b98f-83396089a66e)

![5-setbounds](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/4afc1ade-4748-435b-a3e8-fff9bd5d8a9b)

6. Return to Object mode, click on Calculate Position and Generate UUID buttons. Your AMV position and unique name will be generated.
![6-generatepos](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/eca3eaf5-74d0-42b6-9d45-974215817838)

7. Next, click on Setup Light button, this is going to enable world's lighting in Blender scene.
![7-light](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/24b32306-bce8-4df1-b611-3832849e5e2f)

8. This step isn't necessary, so feel free to move to next one. But if you're eager to checkit , you can click on Display Probes button to visualize how many pixels your AMV texture will have. Then choose Hide Probes.
![8-probes](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/877cb9e9-10b2-4e66-a5cd-1305dc571129)

9. Now, click Bake to JSON. Script will bake two textures and save it to .DDS files. This step may take a shorter or longer while, patience is the key.
![9-bake](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/26058803-be02-4145-a3ac-5ac828347f0e)

10. Open the folder selected in Output Directory. You'll notice a folder with a hexadecimal name.
![10-baked](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/22ca3287-4ff1-4005-9ed1-7d08fded0696)

11. Open CodeX Explorer and type amv_zone_0.ymt in the search bar. Click on the second .YMT file, which is located in RDR2\update4.rpf.
![11-zones](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/81d57e4c-16cb-4e16-923b-a692dc9e98ca)

12. Head down to the end of the file, click at the last </Item> entry.
![12-ymt](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/cb589855-36d5-4833-a785-6df26b1b2ae2)

13. Open generated .XML file, copy the whole content except first line and paste it in .YMT file.
![13-copy](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/f3982c2b-1c02-4cbd-b498-1ef3f3ae8cee)
![13-paste](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/56002bdd-c8d2-4555-86de-8ada52102dbf)


14. Save the file by choosing Save As.
![14-save](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/ca3a5dab-dfbc-475e-8a77-4ed0ea5e7a92)

15. Now, return to CodeX Explorer and type amv_zone_0.ytd in the search bar. Click on the second .YTD file, which is located in RDR2\update4.rpf.
![15-ytd](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/66a7d3bb-b020-4d17-9c31-9200b85d027d)

16. In the Texture Editor, click on the + icon to add two .DDS files.
![16-addtex](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/4633c020-fc29-4665-99d5-ed291229721e)

17. After adding your textures, find them on the list, click on Details tab, find Dimension column and change Texture2D to Texture3D. Do the same thing for the second texture.
![17-texture3d](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/32620ee6-ec6a-4525-9e80-ce7306e69044)

18. Save your .YTD file by choosing Save As.
![18-saveytd](https://github.com/Ktos93/AMV_TOOLS/assets/54397041/61bed4a7-d7b5-4e41-ac16-8e60a811eaa1)

19. Now move your .YMT and .YTD file to RedM resource and that's all!
