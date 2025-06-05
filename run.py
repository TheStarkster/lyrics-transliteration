import uvicorn
import os
import signal
import sys

def handle_exit(signum, frame):
    print("\nShutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_exit)
    
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    os.makedirs("temp/output", exist_ok=True)
    
    try:
        # Run FastAPI server
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0) 