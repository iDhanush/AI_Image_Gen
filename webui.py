import gradio as gr
import modules.config
from modules.async_worker import AsyncTask
import args_manager
from modules.flags import Performance, OutputFormat


def generate_api(prompt, negative_prompt, style_selections, performance, aspect_ratio, image_number,
                 output_format, seed, base_model, refiner_model, refiner_switch, loras, sampler, scheduler):
    # Create task with parameters
    task = AsyncTask(args=[
        prompt, negative_prompt, style_selections,
        performance, aspect_ratio, image_number, output_format, seed,
        base_model, refiner_model, refiner_switch, loras,
        sampler, scheduler
    ])

    # Process task and return results
    # (Implementation would go here to actually generate images)
    return [task]  # Return generated images paths


# Create simplified interface
with gr.Blocks(title="Fooocus API") as app:
    with gr.Row():
        with gr.Column():
            # Core Parameters
            prompt = gr.Textbox(label="Prompt")
            negative_prompt = gr.Textbox(label="Negative Prompt")
            style_selections = gr.CheckboxGroup(
                choices=modules.config.legal_style_names,
                label="Styles"
            )

            # Generation Settings
            performance = gr.Radio(
                label="Performance",
                choices=Performance.values(),
                value=Performance.SPEED.value
            )
            aspect_ratio = gr.Radio(
                label="Aspect Ratio",
                choices=modules.config.available_aspect_ratios,
                value="1152×896"
            )
            image_number = gr.Slider(1, 8, value=2, step=1, label="Image Number")
            output_format = gr.Radio(
                label="Output Format",
                choices=OutputFormat.list(),
                value="png"
            )
            seed = gr.Number(label="Seed", value=-1)

            # Model Settings
            base_model = gr.Dropdown(
                label="Base Model",
                choices=modules.config.model_filenames,
                value=modules.config.default_base_model_name
            )
            refiner_model = gr.Dropdown(
                label="Refiner Model",
                choices=['None'] + modules.config.model_filenames,
                value='None'
            )
            refiner_switch = gr.Slider(0.1, 1.0, value=0.5, label="Refiner Switch At")

            # Advanced Settings
            loras = gr.CheckboxGroup(
                label="LoRAs",
                choices=modules.config.lora_filenames
            )
            sampler = gr.Dropdown(
                label="Sampler",
                choices=modules.config.sampler_list,
                value=modules.config.default_sampler
            )
            scheduler = gr.Dropdown(
                label="Scheduler",
                choices=modules.config.scheduler_list,
                value=modules.config.default_scheduler
            )

            submit_btn = gr.Button("Generate")

        # Outputs
        output_gallery = gr.Gallery(label="Generated Images")

    # API Endpoint
    submit_btn.click(
        generate_api,
        inputs=[
            prompt, negative_prompt, style_selections,
            performance, aspect_ratio, image_number,
            output_format, seed, base_model,
            refiner_model, refiner_switch, loras,
            sampler, scheduler
        ],
        outputs=output_gallery
    )

# Launch configuration
app.launch(
    inbrowser=args_manager.args.in_browser,
    server_name=args_manager.args.listen,
    server_port=args_manager.args.port,
    share=args_manager.args.share,
    allowed_paths=[modules.config.path_outputs]
)