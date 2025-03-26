from fastapi import FastAPI

import modules.async_worker as worker

app = FastAPI

import base64


def image_to_base64(image_path):
    """Convert an image to a base64 string."""
    with open(image_path, "rb") as image_file:
        # Read the image in binary mode
        image_data = image_file.read()
        # Encode the image data to base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
    return encoded_image

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

def start_ngrok():
    import ngrok
    # Start ngrok tunnel for port 7860
    tunnel = ngrok.connect(7860)
    print(f"Ngrok Tunnel URL: {tunnel.public_url}")
    return tunnel
start_ngrok()


@app.get('/')
async def img_ge(prompt:str):
    path = worker.generate_image(prompt)
    return {"img": image_to_base64(path)}



import uvicorn
uvicorn.run(app, host="0.0.0.0", port=7860)