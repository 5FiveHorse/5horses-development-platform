"""
Run the FiveHorses Web Application
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🏇 FiveHorses Property Development Platform")
    print("Web Interface")
    print("=" * 60)
    print("\n🚀 Starting server on port 8001...")
    print("📱 Open your browser at: http://localhost:8001")
    print("Press CTRL+C to stop the server\n")
    
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )