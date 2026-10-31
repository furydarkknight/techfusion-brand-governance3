import sys
import os
import uvicorn

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting TechFusion Brand Governance Platform on http://{host}:{port} ...")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
