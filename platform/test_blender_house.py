"""
Test creating a house in Blender via MCP
Run with: python test_blender_house.py
"""

import socket
import json

def create_house(home_type, bedrooms, bathrooms, area_sqm):
    """Create a house model in Blender"""
    print("=" * 60)
    print(f"🏠 Creating House: {home_type} ({bedrooms} bed, {bathrooms} bath)")
    print("=" * 60)
    
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

print("SUCCESS: House created in Blender!")
print(f"Type: {home_type}, Bedrooms: {bedrooms}, Bathrooms: {bathrooms}, Area: {area_sqm}sqm")
print(f"Dimensions: {{width:.1f}}m x {{depth:.1f}}m x {{height:.1f}}m")
"""
    
    command = {
        "type": "execute_code",
        "params": {"code": code}
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect(('localhost', 9876))
            s.sendall(json.dumps(command).encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            data = json.loads(response)
            
            if data.get("status") == "success":
                print("\n✅ House created successfully in Blender!")
                if "result" in data and "result" in data["result"]:
                    print(f"\n📝 Blender Output:\n{data['result']['result']}")
                return True
            else:
                print(f"\n❌ Error: {data.get('message', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_house("3x2", 3, 2, 140)