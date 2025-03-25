import os
import time
import uuid
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import asyncio
import modules.config as config
import modules

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
output_dir = "/content/outputs"
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
        tasks[task_id]["status"] = "processing"

        # Map API parameters to Fooocus internal configuration
        args = prepare_generation_parameters(params)

        # Create and queue the async task
        task = worker.AsyncTask(args=args)
        worker.async_tasks.append(task)

        # Wait for task completion
        while not task.yields and task.processing:
            await asyncio.sleep(0.1)

        # Process task results
        output_paths = []
        while task.processing:
            await asyncio.sleep(0.1)
            if task.yields:
                flag, content = task.yields.pop(0)
                if flag == "finish":
                    output_paths = save_generated_images(content, task_id)

        if output_paths:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = {
                "images": output_paths,
                "metadata": params.dict()
            }
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = "No images generated"

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        raise


def prepare_generation_parameters(params: GenerationParams) -> list:
    """Convert API parameters to Fooocus-compatible arguments list"""
    args = []

    # Basic parameters
    args.append(False)  # generate_image_grid
    args.append(params.prompt)
    args.append(params.negative_prompt or "")
    args.append(params.styles or modules.config.default_styles.copy())

    # Performance settings
    performance = params.performance or modules.config.default_performance
    args.append(performance)

    # Aspect ratio calculation
    aspect_ratio = f"{params.width}×{params.height}"
    args.append(aspect_ratio)

    # Image settings
    args.append(params.num_images or 1)
    args.append(modules.config.default_output_format)
    args.append(params.seed or random.randint(0, 2 ** 32 - 1))
    args.append(False)  # read_wildcards_in_order
    args.append(params.sharpness or modules.config.default_sample_sharpness)
    args.append(params.guidance_scale or modules.config.default_cfg_scale)

    # Model configuration
    args.append(modules.config.default_base_model_name)
    args.append(modules.config.default_refiner_model_name)
    args.append(modules.config.default_refiner_switch)

    # Add default values for remaining parameters
    args += get_default_parameters()

    return args


def get_default_parameters():
    """Return default values for parameters not specified in the API"""
    return [
        # LoRA parameters (disabled)
        *([False, "None", 1.0] * modules.config.default_max_lora_number),
        # Image input parameters
        False, "uov",  # input_image_checkbox, current_tab
        # Upscale parameters
        flags.uov_list[0], None,  # uov_method, uov_input_image
        # Inpainting defaults
        [], None, "", None,  # outpaint_selections, inpaint_input_image, etc.
        # Preview/NSFW settings
        modules.config.default_black_out_nsfw,
        flags.Performance.has_restricted_features(modules.config.default_performance),
        False, modules.config.default_black_out_nsfw,
        # Advanced parameters
        1.5, 0.8, 0.3, modules.config.default_cfg_tsnr, modules.config.default_clip_skip,
        modules.config.default_sampler, modules.config.default_scheduler, modules.config.default_vae,
        # ... (remaining default parameters)
    ]


def save_generated_images(images, task_id: str) -> list:
    """Save generated images to output directory"""
    output_paths = []
    os.makedirs(output_dir, exist_ok=True)

    for idx, img in enumerate(images):
        output_path = os.path.join(output_dir, f"{task_id}_{idx}.png")
        img.save(output_path)
        output_paths.append(output_path)

    return output_paths

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
auth_token = "2uoywGCki1xWQ2wu9dkfM6ThACO_4dCUMURv8qK8HZC8QnbEq"
import ngrok
import nest_asyncio
# Set the authtoken
ngrok.set_auth_token(auth_token)
ngrok_tunnel = ngrok.connect(8000, hostname='seriously-distinct-bear.ngrok-free.app')
# print('Public URL:', ngrok_tunnel.public_url)
# Apply nest_asyncio
nest_asyncio.apply()
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
