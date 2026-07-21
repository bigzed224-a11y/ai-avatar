"""Test WebSocket connection."""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/pose"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send test pose data (simulated landmarks)
            test_pose = {
                "landmarks": [
                    {"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.9},  # nose
                    {"x": 0.4, "y": 0.5, "z": 0.0, "visibility": 0.8},  # left shoulder
                    {"x": 0.6, "y": 0.5, "z": 0.0, "visibility": 0.8},  # right shoulder
                ]
            }
            
            print("Sending test pose data...")
            await websocket.send(json.dumps(test_pose))
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            
            print(f"Received: {json.dumps(data, indent=2)}")
            print("\n✓ WebSocket test successful!")
            
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        print("\nMake sure server is running: python main.py")

if __name__ == "__main__":
    asyncio.run(test_websocket())
