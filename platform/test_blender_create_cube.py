"""
Test creating a cube in Blender via MCP
Run with: python test_blender_create_cube.py
"""

import socket
import json

def create_cube():
    """Create a simple cube in Blender"""
    print("=" * 60)
    print("🧊 Creating Cube in Blender")
    print("=" * 60)
    
    code = """
import bpy

# Clear existing mesh objects (optional - comment out if you want to keep them)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(
    size=2, 
    location=(0, 0, 1)
)
cube = bpy.context.object
cube.name = "Test_Cube"

# Add a material to make it visible
mat = bpy.data.materials.new(name="Cube_Material")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.2, 0.6, 1.0, 1.0)  # Blue color
cube.data.materials.append(mat)

print("✅ Cube created successfully!")
print(f"   Name: {cube.name}")
print(f"   Location: ({cube.location.x:.2f}, {cube.location.y:.2f}, {cube.location.z:.2f})")
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
                print("\n✅ Cube created successfully!")
                return True
            else:
                print(f"\n❌ Error: {data.get('message', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_cube()