import gradio as gr
import uuid
import base64
import asyncio
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from modules.async_worker import AsyncTask
from modules.config import default_base_model_name

app = FastAPI()

class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    styles: Optional[List[str]] = []
    performance: Optional[str] = "Speed"
    aspect_ratio: Optional[str] = "1152×896"
    image_number: Optional[int] = 1
    seed: Optional[int] = -1
    base_model: Optional[str] = default_base_model_name
    # Add other parameters with proper typing


@app.post("/generate")
async def generate_image(request: GenerationRequest):
    try:
        # Create task arguments with proper types
        task_args = [
            str(uuid.uuid4()),  # task_id
            request.prompt,  # prompt
            request.negative_prompt,  # negative_prompt
            request.styles,  # style_selections
            request.performance,  # performance_selection
            request.aspect_ratio,  # aspect_ratios_selection
            request.image_number,  # image_number
            request.base_model,  # base_model (string)
            request.seed,  # seed (int)
            # Add other parameters in the EXACT ORDER expected by Fooocus
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