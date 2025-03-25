import gradio as gr
import base64
import asyncio
from fastapi import FastAPI, HTTPException
from modules.async_worker import AsyncTask
from typing import List, Optional, Dict
from pydantic import BaseModel
import uuid
app = FastAPI()



class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    styles: Optional[List[str]] = []
    performance: Optional[str] = "Speed"
    aspect_ratio: Optional[str] = "1152×896"
    image_number: Optional[int] = 1
    seed: Optional[int] = -1
    base_model: Optional[str] = "juggernautXL_v8Rundiffusion.safetensors"
    refiner_model: Optional[str] = "None"
    refiner_switch: Optional[float] = 0.5
    loras: Optional[Dict[int, tuple]] = {}  # {0: (True, "None", 1.0)}
    sharpness: Optional[float] = 2.0
    guidance_scale: Optional[float] = 4.0
    input_image: Optional[str] = None  # Base64 encoded image
    # Add other parameters as needed...


@app.post("/generate")
async def generate_image(request: GenerationRequest):
    try:
        # Prepare all parameters in EXACT order expected by Fooocus worker
        task_args = [
            str(uuid.uuid4()),  # 0: task_id
            True,  # 1: generate_image_grid
            request.prompt,  # 2: prompt
            request.negative_prompt,  # 3: negative_prompt
            request.styles,  # 4: style_selections
            request.performance,  # 5: performance_selection
            request.aspect_ratio,  # 6: aspect_ratios_selection
            request.image_number,  # 7: image_number
            request.base_model,  # 8: base_model
            request.refiner_model,  # 9: refiner_model
            request.refiner_switch,  # 10: refiner_switch
            # LoRA parameters (matches original structure)
            *[item for lora in request.loras.values() for item in lora],
            # Image parameters
            request.sharpness,  # Sharpness
            request.guidance_scale,  # Guidance scale
            # Add other parameters in EXACT order...
            # ...
        ]

        task = AsyncTask(args=task_args)
        shared.async_tasks.append(task)

        while not task.finished:
            await asyncio.sleep(0.1)

        return {"images": process_results(task.results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_results(results):
    return [image_to_base64(img) for img in results]


def image_to_base64(img):
    if isinstance(img, str):  # File path
        with open(img, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    elif hasattr(img, "save"):  # PIL Image
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    return ""




with gr.Blocks():
    # Minimal UI for testing
    gr.Markdown("## Fooocus API Server")
    gr.Button(value="API Docs").click(
        None,
        _js="() => window.open('http://localhost:7860/docs')"
    )

app = gr.mount_gradio_app(app, gr.Blocks(), path="/ui")

auth_token = "2up3ov6yLf17M6gkjrK91ZoqlZO_6MjbVjwYQJfbqHFS1XZQJ"
import ngrok
import nest_asyncio
# Set the authtoken
ngrok.set_auth_token(auth_token)

# Connect to ngrok
ngrok_tunnel = ngrok.connect(7860, hostname='seriously-distinct-bear.ngrok-free.app')


# print('Public URL:', ngrok_tunnel.public_url)

# Apply nest_asyncio
nest_asyncio.apply()
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=7860)