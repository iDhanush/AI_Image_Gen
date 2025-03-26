from fastapi import FastAPI

import args_manager
import modules.async_worker as worker
from modules import constants
from modules.auth import check_auth
from modules.config import path_outputs

app = FastAPI

import base64
import gradio as gr

# auth_token = "2up3ov6yLf17M6gkjrK91ZoqlZO_6MjbVjwYQJfbqHFS1XZQJ"
# import ngrok
# import nest_asyncio
# # Set the authtoken
# ngrok.set_auth_token(auth_token)
#
# # Connect to ngrok
# ngrok_tunnel = ngrok.connect(7860, hostname='seriously-distinct-bear.ngrok-free.app')


# print('Public URL:', ngrok_tunnel.public_url)

# Apply nest_asyncio
# nest_asyncio.apply()

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def generate_image(prompt):
    path = worker.generate_image(prompt)
    return path, image_to_base64(path)


def api_generate(prompt: str):
    _, img_b64 = generate_image(prompt)
    return {"img": img_b64}


# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# Image Generator")
    with gr.Row():
        prompt_input = gr.Textbox(label="Enter Prompt")
        btn = gr.Button("Generate")
    image_output = gr.Image(label="Generated Image")

    btn.click(generate_image, inputs=[prompt_input], outputs=[image_output])

# API support
demo.launch(share=True)

print("Gradio public link:", demo.share_url)

