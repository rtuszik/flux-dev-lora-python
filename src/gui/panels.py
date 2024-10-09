import asyncio
from nicegui import ui
from loguru import logger
from util.settings import Settings
from gui.lightbox import Lightbox
from gui.usermodels import UserModels
from gui.filehandler import FileHandler
from gui.styles import Styles


class GUIPanels:
    def setup_top_panel(self):
        logger.debug("Setting up top panel")
        with ui.row().classes("w-full items-center"):
            ui.label("Lumberjack - Replicate API Interface").classes(
                "text-2xl/loose font-bold"
            )
            # dark_mode = ui.dark_mode(True)
            # ui.switch().bind_value(dark_mode).classes().props(
            #     "dense checked-icon=dark_mode unchecked-icon=light_mode color=blue-4"
            # )
            ui.button(
                icon="settings_suggest",
                on_click=self.open_settings_popup,
                color="blue-4",
            ).classes("absolute-right mr-6 mt-3 mb-3")

    def setup_left_panel(self):
        logger.debug("Setting up left panel")
        with ui.row().classes("w-full flex-row flex-nowrap"):
            self.replicate_model_select = (
                ui.select(
                    options=self.model_options,
                    label="Replicate Model",
                    value=self.replicate_model,
                    on_change=lambda e: asyncio.create_task(
                        self.update_replicate_model(e.value)
                    ),
                )
                .classes("width-5/6 overflow-auto custom-select bg-[#1e1e2e]")
                .tooltip("Select or manage Replicate models")
                .props("filled bg-color=dark")
            )
            ui.button(icon="token", color="blue-4").classes("ml-2 mt-1.2").on(
                "click", UserModels.open_user_model_popup(self)
            ).props("size=1.3rem")

        self.flux_model_select = (
            ui.select(
                ["dev", "schnell"],
                label="Flux Model",
                value=Settings.get_setting("default", "flux_model", "dev"),
            )
            .classes("w-full text-gray-200")
            .tooltip(
                "Which model to run inferences with. The dev model needs around 28 steps but the schnell model only needs around 4 steps."
            )
            .bind_value(self, "flux_model")
            .props("filled bg-color=dark")
        )

        with ui.row().classes("w-full flex-nowrap md:flex-wrap"):
            self.aspect_ratio_select = (
                ui.select(
                    [
                        "1:1",
                        "16:9",
                        "21:9",
                        "3:2",
                        "2:3",
                        "4:5",
                        "5:4",
                        "3:4",
                        "4:3",
                        "9:16",
                        "9:21",
                        "custom",
                    ],
                    label="Aspect Ratio",
                    value=Settings.get_setting("default", "aspect_ratio", "1:1"),
                )
                .classes("w-1/2 md:w-full text-gray-200")
                .bind_value(self, "aspect_ratio")
                .tooltip(
                    "Width of the generated image. Optional, only used when aspect_ratio=custom. Must be a multiple of 16 (if it's not, it will be rounded to nearest multiple of 16)"
                )
                .props("filled bg-color=dark")
            )
            self.aspect_ratio_select.on("change", self.toggle_custom_dimensions)

            with ui.column().classes("w-full").bind_visibility_from(
                self.aspect_ratio_select, "value", value="custom"
            ):
                self.width_input = (
                    ui.number(
                        "Width",
                        value=Settings.get_setting("default", "width", 1024, int),
                        min=256,
                        max=1440,
                    )
                    .classes("w-full")
                    .bind_value(self, "width")
                    .tooltip(
                        "Width of the generated image. Optional, only used when aspect_ratio=custom. Must be a multiple of 16 (if it's not, it will be rounded to nearest multiple of 16)"
                    )
                    .props("filled bg-color=dark")
                )
                self.height_input = (
                    ui.number(
                        "Height",
                        value=Settings.get_setting("default", "height", 1024, int),
                        min=256,
                        max=1440,
                    )
                    .classes("w-full")
                    .bind_value(self, "height")
                    .tooltip(
                        "Height of the generated image. Optional, only used when aspect_ratio=custom. Must be a multiple of 16 (if it's not, it will be rounded to nearest multiple of 16)"
                    )
                    .props("filled bg-color=dark")
                )

            self.num_outputs_input = (
                ui.number(
                    "Num Outputs",
                    value=Settings.get_setting("default", "num_outputs", 1, int),
                    min=1,
                    max=4,
                )
                .classes("w-1/2 md:w-full")
                .bind_value(self, "num_outputs")
                .tooltip("Number of images to output.")
                .props("filled bg-color=dark")
            )

        with ui.row().classes("w-full flex-nowrap md:flex-wrap"):
            self.lora_scale_input = (
                ui.number(
                    "LoRA Scale",
                    value=float(Settings.get_setting("default", "lora_scale", 1)),
                    min=-1,
                    max=2,
                    step=0.1,
                )
                .classes("w-1/2 md:w-full")
                .tooltip(
                    "Determines how strongly the LoRA should be applied. Sane results between 0 and 1."
                )
                .props("filled bg-color=dark color=primary")
                .bind_value(self, "lora_scale")
            )
            self.num_inference_steps_input = (
                ui.number(
                    "Num Inference Steps",
                    value=Settings.get_setting(
                        "default", "num_inference_steps", 28, int
                    ),
                    min=1,
                    max=50,
                    precision=0,
                )
                .classes("w-1/2 md:w-full")
                .tooltip("Number of Inference Steps")
                .bind_value(self, "num_inference_steps")
                .props("filled bg-color=dark")
            )

        with ui.row().classes("w-full flex-nowrap md:flex-wrap"):
            self.guidance_scale_input = (
                ui.number(
                    "Guidance Scale",
                    value=float(Settings.get_setting("default", "guidance_scale", 3.5)),
                    min=0,
                    max=10,
                    step=0.1,
                    precision=2,
                )
                .classes("w-1/2 md:w-full")
                .tooltip("Guidance Scale for the diffusion process")
                .bind_value(self, "guidance_scale")
                .props("filled bg-color=dark")
            )
            self.seed_input = (
                ui.number(
                    "Seed",
                    value=Settings.get_setting("default", "seed", -1, int),
                    min=-2147483648,
                    max=2147483647,
                )
                .classes("w-1/2 md:w-full")
                .bind_value(self, "seed")
                .props("filled bg-color=dark")
            )

        with ui.row().classes("w-full flex-nowrap"):
            self.output_format_select = (
                ui.select(
                    ["webp", "jpg", "png"],
                    label="Output Format",
                    value=Settings.get_setting("default", "output_format", "webp"),
                )
                .classes("w-full")
                .tooltip("Format of the output images")
                .bind_value(self, "output_format")
                .props("filled bg-color=dark")
            )

            self.output_quality_input = (
                ui.number(
                    "Output Quality",
                    value=Settings.get_setting("default", "output_quality", 80, int),
                    min=0,
                    max=100,
                )
                .classes("w-full")
                .tooltip(
                    "Quality when saving the output images, from 0 to 100. 100 is best quality, 0 is lowest quality. Not relevant for .png outputs"
                )
                .bind_value(self, "output_quality")
                .props("filled bg-color=dark")
            )

        with ui.row().classes("w-full flex-nowrap"):
            self.disable_safety_checker_switch = (
                ui.switch(
                    "Disable Safety Checker",
                    value=Settings.get_setting(
                        "default", "disable_safety_checker", fallback="False"
                    ).lower()
                    == "true",
                )
                .classes("w-1/2")
                .tooltip("Disable safety checker for generated images.")
                .bind_value(self, "disable_safety_checker")
                .props("filled bg-color=dark color=blue-4")
            )
            self.reset_button = ui.button(
                "Reset Parameters", on_click=self.reset_to_default, color="#e78284"
            ).classes("w-1/2 text-white font-bold py-2 px-4 rounded")

    def setup_right_panel(self):
        logger.debug("Setting up right panel")
        with ui.row().classes("w-full flex-nowrap"):
            ui.label("Output").classes("text-center ml-4 mt-3 w-full").style(
                "font-size: 230%; font-weight: bold; text-align: left;"
            )
            ui.button(
                "Download Images",
                on_click=lambda: FileHandler.download_zip(
                    self.last_generated_images, self.output_folder
                ),
                color="blue-4",
            ).classes("modern-button text-white font-bold py-2 px-4 rounded")
        ui.separator()
        with ui.row().classes("w-full flex-nowrap"):
            self.gallery_container = ui.column().classes(
                "w-full mt-4 grid grid-cols-2 gap-4"
            )
            self.lightbox = Lightbox()

    def setup_prompt_panel(self):
        logger.debug("Setting up prompt panel")
        with ui.row().classes("w-full flex-row flex-nowrap"):
            self.prompt_input = (
                ui.textarea("Prompt", value=self.prompt)
                .classes("w-full shadow-lg")
                .bind_value(self, "prompt")
                .props("clearable filled bg-color=dark autofocus color=blue-4")
            )
            self.generate_button = (
                ui.button(icon="bolt", on_click=self.start_generation, color="blue-4")
                .classes("ml-2 font-bold rounded modern-button h-full")
                .props("size=1.5rem")
                .style("animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;")
            )
        self.progress = (
            ui.linear_progress(show_value=False, size="20px")
            .classes("w-full")
            .props("indeterminate")
        )
        self.progress.visible = False
