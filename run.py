import uvicorn
import os

if __name__ == "__main__":
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    os.makedirs("temp/output", exist_ok=True)
    
    # Run FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 