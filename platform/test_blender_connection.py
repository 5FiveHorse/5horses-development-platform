"""
Test Blender MCP Connection
Run with: python test_blender_connection.py
"""

import socket
import json

def test_connection():
    """Test connection to Blender MCP server"""
    print("=" * 60)
    print("🔌 Testing Blender MCP Connection")
    print("=" * 60)
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # 5 second timeout
            s.connect(('localhost', 9876))
            s.sendall(json.dumps({"type": "get_scene_info"}).encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            data = json.loads(response)
            
            print("\n✅ Connected to Blender MCP!")
            print(f"Response: {data}")
            
            if "result" in data and data["result"]:
                scene_info = data["result"]
                print(f"\n📊 Scene Information:")
                print(f"  Scene Name: {scene_info.get('name', 'Unknown')}")
                print(f"  Object Count: {scene_info.get('object_count', 0)}")
                print(f"  Materials Count: {scene_info.get('materials_count', 0)}")
                if scene_info.get('objects'):
                    print(f"  Objects: {len(scene_info['objects'])} (first 10 shown)")
            
            return True
            
    except socket.timeout:
        print("\n❌ Connection timeout!")
        print("   Make sure:")
        print("   1. Blender is running")
        print("   2. The Blender MCP addon is enabled")
        print("   3. The MCP server is started (click 'Connect to MCP server' in Blender)")
        return False
        
    except ConnectionRefusedError:
        print("\n❌ Connection refused!")
        print("   Make sure the Blender MCP server is running in Blender.")
        print("   Go to Blender → BlenderMCP tab → Click 'Connect to MCP server'")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()