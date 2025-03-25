import os
import json
import uuid
import time
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import modules.config as config
import modules.flags as flags
from modules.util import get_image_size_info
from extras.inpaint_mask import generate_mask_from_image, SAMOptions

app = FastAPI(title="Fooocus API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary storage for tasks (replace with database in production)
tasks = {}
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)


# Pydantic models
class GenerationParams(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    style_selections: List[str] = []
    performance: str = "Speed"
    aspect_ratio: str = "1152*896"
    image_number: int = 1
    seed: Optional[int] = None
    sharpness: float = 2.0
    guidance_scale: float = 4.0
    base_model: str = config.default_base_model_name
    refiner_model: Optional[str] = None
    loras: List[Dict[str, Any]] = []
    # Add other parameters as needed...


class InpaintRequest(BaseModel):
    image: UploadFile
    mask: Optional[UploadFile] = None
    prompt: str
    mode: str = "Inpaint"


class DescribeRequest(BaseModel):
    image: UploadFile
    modes: List[str] = ["Photo"]
    apply_styles: bool = True


@app.post("/generate")
async def generate_image(params: GenerationParams, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "start_time": time.time(),
        "params": params.dict(),
        "result": None
    }

    background_tasks.add_task(process_generation, task_id, params)

    return JSONResponse(content={"task_id": task_id})


async def process_generation(task_id: str, params: GenerationParams):
    try:
        # Implement actual generation logic using modules.config and worker
        # This is a simplified example
        tasks[task_id]["status"] = "processing"

        # Simulate generation process
        await asyncio.sleep(2)

        # Save mock result
        output_path = os.path.join(output_dir, f"{task_id}.png")
        # Replace with actual generation and saving code

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = {
            "images": [output_path],
            "metadata": params.dict()
        }

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "status": task["status"],
        "elapsed": time.time() - task["start_time"],
        "result": task.get("result"),
        "error": task.get("error")
    }


@app.post("/inpaint")
async def inpaint_image(request: InpaintRequest):
    try:
        image_data = await request.image.read()
        mask_data = await request.mask.read() if request.mask else None

        # Process inpaint using modules
        result = process_inpaint(image_data, mask_data, request.prompt, request.mode)

        return FileResponse(result["image_path"], media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_inpaint(image_data, mask_data, prompt, mode):
    # Implement actual inpainting logic
    # Example using generate_mask_from_image
    result_path = os.path.join(output_dir, f"inpaint_{uuid.uuid4()}.png")
    # ... processing code ...
    return {"image_path": result_path}


@app.post("/describe")
async def describe_image(request: DescribeRequest):
    try:
        image_data = await request.image.read()
        # Process description
        description = process_description(image_data, request.modes, request.apply_styles)
        return description
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_description(image_data, modes, apply_styles):
    # Implement actual description logic
    return {
        "prompt": "Generated description",
        "styles": ["Fooocus V2"] if apply_styles else []
    }


@app.get("/presets")
def get_presets():
    return {"presets": config.available_presets}


@app.get("/models")
def get_models():
    return {
        "base_models": config.model_filenames,
        "refiner_models": ["None"] + config.model_filenames,
        "loras": config.lora_filenames
    }


# Add more endpoints for style handling, configuration, etc.


import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)