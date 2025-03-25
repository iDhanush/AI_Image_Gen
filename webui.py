import gradio as gr
import json
import uuid
import base64
import asyncio
import numpy as np
from io import BytesIO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from modules import config, worker, async_worker

app = FastAPI()


# Simplified Configuration
class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    styles: list = []
    performance: str = "Speed"
    aspect_ratio: str = "1152×896"
    image_number: int = 1
    seed: int = -1
    base_model: str = config.default_base_model_name
    # Add other parameters as needed...


@app.post("/generate")
async def generate_image(request: GenerationRequest):
    try:
        # Create async task
        task_id = str(uuid.uuid4())
        task = worker.AsyncTask(
            args=[
                task_id,
                request.prompt,
                request.negative_prompt,
                request.styles,
                request.performance,
                request.aspect_ratio,
                request.image_number,
                request.seed,
                request.base_model,
                # Add other parameters...
            ]
        )

        # Add task to worker
        async_worker.async_tasks.append(task)

        # Wait for task completion
        while not task.finished:
            await asyncio.sleep(0.1)

        # Get results
        results = task.results
        return {"task_id": task_id, "images": process_images(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_images(results):
    """Convert generated images to base64"""
    processed = []
    for img_path in results:
        with open(img_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            processed.append(f"data:image/png;base64,{encoded}")
    return processed


# Initialize Gradio components (minimal)

with gr.Blocks():
    # Minimal UI for testing
    gr.Markdown("## Fooocus API Server")
    gr.Button(value="API Docs").click(
        None,
        _js="() => window.open('http://localhost:7860/docs')"
    )

if __name__ == "__main__":
    # Mount FastAPI app on Gradio server
    app = gr.mount_gradio_app(app, gr.Blocks(), path="/ui")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)