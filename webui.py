import gradio as gr
import json
import uuid
import base64
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from modules.config import default_base_model_name
from modules.async_worker import AsyncTask


app = FastAPI()


class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    styles: list = []
    performance: str = "Speed"
    aspect_ratio: str = "1152×896"
    image_number: int = 1
    seed: int = -1
    base_model: str = default_base_model_name


@app.post("/generate")
async def generate_image(request: GenerationRequest):
    try:
        task_id = str(uuid.uuid4())

        # Create task arguments matching Fooocus's worker expectations
        task_args = [
            task_id,
            request.prompt,
            request.negative_prompt,
            request.styles,
            request.performance,
            request.aspect_ratio,
            request.image_number,
            request.seed,
            request.base_model
        ]

        # Create AsyncTask instance
        task = AsyncTask(args=task_args)

        # Add task to processing queue
        shared.async_tasks.append(task)

        # Wait for completion
        while not task.finished:
            await asyncio.sleep(0.1)

        # Process results
        return {
            "task_id": task_id,
            "images": process_results(task.results)
        }

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