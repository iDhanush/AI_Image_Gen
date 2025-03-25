# webui.py

import gradio as gr
import random
import os
import time
import shared
import modules.config
import fooocus_version
import modules.html
import modules.async_worker as worker
import modules.constants as constants
import modules.flags as flags
import modules.gradio_hijack as grh
import modules.style_sorter as style_sorter
import args_manager
import copy
from modules.sdxl_styles import legal_style_names
from modules.private_logger import get_current_html_path
from modules.ui_gradio_extensions import reload_javascript


def get_task(*args):
    args = list(args)
    args.pop(0)
    return worker.AsyncTask(args=args)


def generate_clicked(task: worker.AsyncTask):
    import ldm_patched.modules.model_management as model_management
    with model_management.interrupt_processing_mutex:
        model_management.interrupt_processing = False

    execution_start_time = time.perf_counter()
    finished = False

    yield gr.update(visible=True, value=modules.html.make_progress_html(1, 'Starting...')), \
        gr.update(visible=True, value=None), \
        gr.update(visible=False, value=None), \
        gr.update(visible=False)

    worker.async_tasks.append(task)

    while not finished:
        time.sleep(0.01)
        if len(task.yields) > 0:
            flag, product = task.yields.pop(0)
            if flag == 'preview':
                percentage, title, image = product
                yield gr.update(visible=True, value=modules.html.make_progress_html(percentage, title)), \
                    gr.update(visible=True, value=image) if image is not None else gr.update(), \
                    gr.update(), \
                    gr.update(visible=False)
            if flag == 'finish':
                yield gr.update(visible=False), \
                    gr.update(visible=False), \
                    gr.update(visible=False), \
                    gr.update(visible=True, value=product)
                finished = True

    execution_time = time.perf_counter() - execution_start_time
    print(f'Total time: {execution_time:.2f} seconds')
    return


reload_javascript()

title = f'Fooocus {fooocus_version.version}'
if isinstance(args_manager.args.preset, str):
    title += ' ' + args_manager.args.preset

shared.gradio_root = gr.Blocks(title=title).queue()

with shared.gradio_root:
    currentTask = gr.State(worker.AsyncTask(args=[]))
    with gr.Row():
        with gr.Column(scale=2):
            gallery = gr.Gallery(label='Output', show_label=False, object_fit='contain', visible=True,
                                 height=768,
                                 elem_classes=['resizable_area', 'main_view', 'final_gallery', 'image_gallery'],
                                 elem_id='final_gallery')

            with gr.Row():
                with gr.Column(scale=6):
                    prompt = gr.Textbox(show_label=False, placeholder="Enter prompt here...",
                                        elem_id='positive_prompt', lines=3)
                with gr.Column(scale=1):
                    generate_button = gr.Button("Generate", variant='primary')

        with gr.Column(scale=1):
            with gr.Tab(label='Settings'):
                performance_selection = gr.Radio(label='Performance',
                                                 choices=flags.Performance.values(),
                                                 value=modules.config.default_performance)

                aspect_ratios = gr.Radio(label='Aspect Ratio',
                                         choices=modules.config.available_aspect_ratios_labels,
                                         value=modules.config.default_aspect_ratio)

                image_number = gr.Slider(label='Images', minimum=1, maximum=4,
                                         step=1, value=modules.config.default_image_number)

                seed = gr.Number(label='Seed', value=0, precision=0)
                seed_random = gr.Checkbox(label='Random Seed', value=True)

            with gr.Tab(label='Models'):
                base_model = gr.Dropdown(label='Base Model', choices=modules.config.model_filenames,
                                         value=modules.config.default_base_model_name)
                refiner_model = gr.Dropdown(label='Refiner', choices=['None'] + modules.config.model_filenames,
                                            value=modules.config.default_refiner_model_name)

                lora_ctrls = []
                for i in range(modules.config.default_max_lora_number):
                    with gr.Row():
                        lora_enabled = gr.Checkbox(label='Enable', value=False, scale=1)
                        lora_model = gr.Dropdown(label=f'LoRA {i + 1}',
                                                 choices=['None'] + modules.config.lora_filenames,
                                                 value='None', scale=5)
                        lora_weight = gr.Slider(label='Weight', minimum=-2, maximum=2, step=0.1, value=1.0, scale=5)
                        lora_ctrls += [lora_enabled, lora_model, lora_weight]

            with gr.Tab(label='Styles'):
                style_selections = gr.CheckboxGroup(choices=copy.deepcopy(style_sorter.all_styles),
                                                    value=copy.deepcopy(modules.config.default_styles),
                                                    label='Selected Styles')

                style_search = gr.Textbox(label="Search Styles", placeholder="Type to search...")
                style_search.change(style_sorter.search_styles, [style_selections, style_search], style_selections)

    # Event handlers
    generate_button.click(
        lambda: (gr.update(interactive=False), [], [generate_button]
                 ).then(
            fn=refresh_seed, inputs=[seed_random, seed], outputs=seed
        ).then(
            fn=get_task, inputs=[currentTask] + [prompt, negative_prompt, style_selections, performance_selection,
                                                 aspect_ratios, image_number, 'png', seed, False, 2.0, 7.0,
                                                 base_model, refiner_model, 0.5] + lora_ctrls,
            outputs=currentTask
        ).then(
            fn=generate_clicked, inputs=currentTask,
            outputs=[progress_html, progress_window, progress_gallery, gallery]
        ).then(
            lambda: gr.update(interactive=True), outputs=[generate_button]
        )

    shared.gradio_root.launch(
        in_browser=args_manager.args.in_browser,
        server_name=args_manager.args.listen,
        server_port=args_manager.args.port,
        share=args_manager.args.share,
        allowed_paths=[modules.config.path_outputs]
    )