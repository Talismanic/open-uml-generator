from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from uml_agent_runner import generate_uml

app = FastAPI()

# Allow frontend (localhost:3000) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class RequirementRequest(BaseModel):
    requirement: str
    mode: int = 2

app.mount("/diagrams", StaticFiles(directory="diagrams"), name="diagrams")


# POST endpoint for UML generation
@app.post("/generate")
async def generate_endpoint(req: RequirementRequest):
    try:
        diagram_url = await generate_uml(req.requirement, req.mode)
        if not diagram_url:
            raise HTTPException(status_code=500, detail="Failed to generate diagram")
        return {"diagram_url": diagram_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # GET endpoint to serve .puml files
# @app.get("/diagrams/{filename}")
# async def get_diagram_file(filename: str):
#     file_path = os.path.join("diagrams", filename)
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Diagram not found")
#     return FileResponse(file_path, media_type="text/plain")
