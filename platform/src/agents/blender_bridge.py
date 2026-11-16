"""
Blender Bridge - Connects FiveHorses agents to Blender MCP
"""

import socket
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

BLENDER_HOST = 'localhost'
BLENDER_PORT = 9876


class BlenderBridge:
    """Bridge between FiveHorses agents and Blender MCP"""

    def __init__(self, host: str = BLENDER_HOST, port: int = BLENDER_PORT):
        self.host = host
        self.port = port
        self.connected = False

    def send_command(self, command_type: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        command = {"type": command_type, "params": params}
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.host, self.port))
                s.sendall(json.dumps(command).encode('utf-8'))
                response = s.recv(4096).decode('utf-8')
                return json.loads(response)
        except socket.timeout:
            return {"status": "error", "message": "Connection timeout - is Blender running?"}
        except ConnectionRefusedError:
            return {"status": "error", "message": "Blender MCP server not running - start it in Blender"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_code(self, code: str) -> Dict[str, Any]:
        return self.send_command("execute_code", {"code": code})

    def get_scene_info(self) -> Dict[str, Any]:
        return self.send_command("get_scene_info")

    def clear_scene(self) -> Dict[str, Any]:
        code = """
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
print("Scene cleared!")
"""
        return self.execute_code(code)

    def create_house(self, home_type: str, bedrooms: int, bathrooms: int, area_sqm: float) -> Dict[str, Any]:
        code = f"""
import bpy
import mathutils

width = {area_sqm} ** 0.5 * 0.8
depth = {area_sqm} ** 0.5 * 0.8
height = 2.8

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height/2))
house = bpy.context.object
house.name = "House_{home_type}"
house.scale = (width/2, depth/2, height/2)

bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(width, depth)/1.4, depth=1.5, location=(0, 0, height + 0.5))
roof = bpy.context.object
roof.name = "Roof_{home_type}"

mat = bpy.data.materials.new(name="House_Material")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.9, 0.8, 0.7, 1.0)
house.data.materials.append(mat)

roof_mat = bpy.data.materials.new(name="Roof_Material")
roof_mat.use_nodes = True
roof_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.4, 0.2, 0.1, 1.0)
roof.data.materials.append(roof_mat)

print(f"Created {home_type} house: {bedrooms} beds, {bathrooms} baths, {area_sqm}sqm")
print(f"Dimensions: {{width:.1f}}m x {{depth:.1f}}m x {{height:.1f}}m")
"""
        return self.execute_code(code)

    def create_commercial_building(self, name: str, area_sqm: float, building_type: str) -> Dict[str, Any]:
        code = f"""
import bpy

width = {area_sqm} ** 0.5 * 0.6
depth = {area_sqm} ** 0.5 * 0.6
height = 3.5

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height/2))
building = bpy.context.object
building.name = "Commercial_{name}"
building.scale = (width/2, depth/2, height/2)

mat = bpy.data.materials.new(name="Glass_{name}")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.1, 0.3, 0.6, 1.0)
mat.node_tree.nodes["Principled BSDF"].inputs[16].default_value = 0.1
mat.node_tree.nodes["Principled BSDF"].inputs[17].default_value = 0.9
building.data.materials.append(mat)

print(f"Created commercial building: {name} ({area_sqm} sqm, {building_type})")
print(f"Dimensions: {{width:.1f}}m x {{depth:.1f}}m x {{height:.1f}}m")
"""
        return self.execute_code(code)

    def create_site_layout(self, buildings: List[Dict[str, Any]]) -> Dict[str, Any]:
        code_parts = ["import bpy, mathutils"]

        for i, building in enumerate(buildings):
            x_pos = (i % 3) * 10 - 10
            z_pos = (i // 3) * 10 - 5

            if building.get("type") == "house":
                area = building.get("area_sqm", 100)
                width = area ** 0.5 * 0.8
                depth = area ** 0.5 * 0.8
                height = 2.8
                home_type = building.get("home_type", f"house_{i}")

                code_parts.append(f"""
bpy.ops.mesh.primitive_cube_add(size=1, location=({x_pos}, {z_pos}, {height/2}))
house = bpy.context.object
house.name = "House_{i}"
house.scale = ({width/2}, {depth/2}, {height/2})
""")
            else:
                area = building.get("area_sqm", 200)
                width = area ** 0.5 * 0.6
                depth = area ** 0.5 * 0.6
                height = 3.5
                name = building.get("name", f"commercial_{i}")

                code_parts.append(f"""
bpy.ops.mesh.primitive_cube_add(size=1, location=({x_pos}, {z_pos}, {height/2}))
commercial = bpy.context.object
commercial.name = "Commercial_{i}"
commercial.scale = ({width/2}, {depth/2}, {height/2})
""")

        code_parts.append('print("Site layout created!")')
        code = "\n".join(code_parts)
        return self.execute_code(code)

    def render_scene(
        self,
        output_path: str,
        camera_location: tuple = (12, -12, 8),
        camera_rotation_deg: tuple = (60, 0, 45),
        resolution: tuple = (1280, 720),
        engine: str = "BLENDER_EEVEE_NEXT",
    ) -> Dict[str, Any]:
        """
        Set up camera + lighting and render the current scene to a still image.

        output_path must be a path Blender's own process can write to
        (i.e. on disk where Blender is running, not necessarily where this
        Python process is running, unless Blender and the agent share a filesystem).
        """
        safe_path = output_path.replace("\\", "/").replace('"', '')

        code = f"""
import bpy
import math

# Camera
cam_data = bpy.data.cameras.new("ArchitectCam")
cam_obj = bpy.data.objects.new("ArchitectCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = ({camera_location[0]}, {camera_location[1]}, {camera_location[2]})
cam_obj.rotation_euler = (
    math.radians({camera_rotation_deg[0]}),
    math.radians({camera_rotation_deg[1]}),
    math.radians({camera_rotation_deg[2]}),
)
bpy.context.scene.camera = cam_obj

# Simple three-point-ish lighting
sun_data = bpy.data.lights.new(name="SunLight", type='SUN')
sun_data.energy = 3.5
sun_obj = bpy.data.objects.new(name="SunLight", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.location = (10, -10, 15)
sun_obj.rotation_euler = (math.radians(45), 0, math.radians(45))

fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 200
fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-8, 8, 6)

# Render settings
scene = bpy.context.scene
try:
    scene.render.engine = "{engine}"
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = {resolution[0]}
scene.render.resolution_y = {resolution[1]}
scene.render.filepath = "{safe_path}"

bpy.ops.render.render(write_still=True)
print(f"RENDER_COMPLETE: {safe_path}")
"""
        result = self.execute_code(code)
        if result.get("status") == "success":
            result["render_path"] = output_path
        return result


_blender_bridge = None


def get_blender_bridge() -> BlenderBridge:
    global _blender_bridge
    if _blender_bridge is None:
        _blender_bridge = BlenderBridge()
    return _blender_bridge
