import asyncio
import json
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from gui.lightbox import Lightbox
from gui.styles import Styles
from gui.panels import GUIPanels
from gui.filehandler import FileHandler
import httpx
from loguru import logger
from nicegui import ui
from util import Settings

DOCKERIZED = os.environ.get("DOCKER_CONTAINER", False)


class ImageGeneratorGUI:
    def __init__(self, image_generator):
        logger.info("Initializing ImageGeneratorGUI")
        self.image_generator = image_generator
        self.api_key = Settings.get_api_key() or os.environ.get("REPLICATE_API_KEY", "")
        self.last_generated_images = []
        self.custom_styles = Styles.setup_custom_styles()
        self._attributes = [
            "prompt",
            "flux_model",
            "aspect_ratio",
            "num_outputs",
            "lora_scale",
            "num_inference_steps",
            "guidance_scale",
            "output_format",
            "output_quality",
            "disable_safety_checker",
            "width",
            "height",
            "seed",
            "output_folder",
            "replicate_model",
        ]

        self.user_added_models = {}
        self.prompt = Settings.get_setting("default", "prompt", "", str)

        self.flux_model = Settings.get_setting("default", "flux_model", "dev", str)
        self.aspect_ratio = Settings.get_setting("default", "aspect_ratio", "1:1", str)
        self.num_outputs = Settings.get_setting("default", "num_outputs", "1", int)
        self.lora_scale = Settings.get_setting("default", "lora_scale", "1", float)
        self.num_inference_steps = Settings.get_setting(
            "default", "num_inference_steps", "28", int
        )
        self.guidance_scale = Settings.get_setting(
            "default", "guidance_scale", "3.5", float
        )
        self.output_format = Settings.get_setting("default", "output_format", "png")
        self.output_quality = Settings.get_setting(
            "default", "output_quality", "80", int
        )
        self.disable_safety_checker = Settings.get_setting(
            "default", "disable_safety_checker", True, bool
        )

        self.width = Settings.get_setting("default", "width", "1024", int)
        self.height = Settings.get_setting("default", "height", "1024", int)
        self.seed = Settings.get_setting("default", "seed", "-1", int)

        self.output_folder = (
            "/app/output"
            if DOCKERIZED
            else Settings.get_setting("default", "output_folder", "/Downloads", str)
        )
        models_json = Settings.get_setting(
            "default", "models", '{"user_added": []}', str
        )
        models = json.loads(models_json)
        self.user_added_models = {
            model: model for model in models.get("user_added", [])
        }
        self.model_options = list(self.user_added_models.keys())
        self.replicate_model = Settings.get_setting(
            "default", "replicate_model", "", str
        )

        logger.info("ImageGeneratorGUI initialized")

    def setup_ui(self):
        logger.info("Setting up UI")
        ui.dark_mode(True)
        self.check_api_key()

        with ui.grid().classes(
            "w-full h-screen md:h-full grid-cols-1 md:grid-cols-2 gap-2 md:gap-5 p-4 md:p-6 dark:bg-[#11111b] bg-#eff1f5] md:auto-rows-min"
        ):
            with ui.card().classes("col-span-full modern-card flex-nowrap h-min"):
                GUIPanels.setup_top_panel(self)

            with ui.card().classes("col-span-full modern-card"):
                GUIPanels.setup_prompt_panel(self)

            with ui.card().classes("row-span-2 overflow-auto modern-card"):
                GUIPanels.setup_left_panel(self)

            with ui.card().classes("row-span-2 overflow-auto modern-card"):
                GUIPanels.setup_right_panel(self)
        Styles.stylefilter(self)
        logger.info("UI setup completed")

    async def open_settings_popup(self):
        logger.debug("Opening settings popup")
        with ui.dialog() as dialog, ui.card().classes(
            "w-2/3 modern-card dark:bg-[#25292e] bg-[#818b981f]"
        ):
            ui.label("Settings").classes("text-2xl font-bold")
            api_key_input = ui.input(
                label="API Key",
                placeholder="Enter Replicate API Key...",
                password=True,
                value=self.api_key,
            ).classes("w-full mb-4")

            async def save_settings():
                logger.debug("Saving settings")
                new_api_key = api_key_input.value
                if new_api_key != self.api_key:
                    self.api_key = new_api_key
                    Settings.set_setting("secrets", "REPLICATE_API_KEY", new_api_key)
                    await self.save_settings()
                    os.environ["REPLICATE_API_KEY"] = new_api_key
                    self.image_generator.set_api_key(new_api_key)
                    logger.info("API key saved")

                dialog.close()
                ui.notify("Settings saved successfully", type="positive")

            if not DOCKERIZED:
                self.folder_input = ui.input(
                    label="Output Folder", value=self.output_folder
                ).classes("w-full mb-4")
                self.folder_input.on("change", self.update_folder_path)
            ui.button("Save Settings", on_click=save_settings, color="blue-4").classes(
                "mt-4"
            )
        dialog.open()

    async def save_api_key(self):
        logger.debug("Saving API key")
        Settings.set_setting("secrets", "REPLICATE_API_KEY", self.api_key)
        Settings.save_settings()
        os.environ["REPLICATE_API_KEY"] = self.api_key
        self.image_generator.set_api_key(self.api_key)

    async def update_folder_path(self, e):
        logger.debug("Updating folder path")
        if hasattr(e, "value"):
            new_path = e.value
        elif hasattr(e, "sender") and hasattr(e.sender, "value"):
            new_path = e.sender.value
        elif hasattr(e, "args") and e.args:
            new_path = e.args[0]
        else:
            new_path = None

        if new_path is None:
            logger.error("Failed to extract new path from event object")
            ui.notify("Error updating folder path", type="negative")
            return

        if os.path.isdir(new_path):
            self.output_folder = new_path
            Settings.set_setting("default", "output_folder", new_path)
            Settings.save_settings()
            logger.info(f"Output folder set to: {self.output_folder}")
            ui.notify(
                f"Output folder updated to: {self.output_folder}", type="positive"
            )
        else:
            logger.warning(f"Invalid folder path: {new_path}")
            ui.notify(
                "Invalid folder path. Please enter a valid directory.", type="negative"
            )
            if hasattr(self, "folder_input"):
                self.folder_input.value = self.output_folder

    async def toggle_custom_dimensions(self, e):
        logger.debug(f"Toggling custom dimensions: {e.value}")
        if e.value == "custom":
            self.width_input.enable()
            self.height_input.enable()
        else:
            self.width_input.disable()
            self.height_input.disable()
        await self.save_settings()
        logger.info(f"Custom dimensions toggled: {e.value}")

    def check_api_key(self):
        logger.debug("Checking API key")
        if not self.api_key:
            logger.warning("No Replicate API Key found.")
            ui.notify(
                "No Replicate API Key found. Please set it in the settings before generating images.",
                type="warning",
                close_button="OK",
                timeout=10000,  # 10 seconds
                position="top",
            )

    async def reset_to_default(self):
        logger.debug("Resetting parameters to default values")
        for attr in self._attributes:
            if attr not in ["models", "replicate_model"]:
                value = Settings.get_setting("default", attr)
                if value is not None:
                    if attr in [
                        "num_outputs",
                        "num_inference_steps",
                        "width",
                        "height",
                        "seed",
                        "output_quality",
                    ]:
                        value = int(value)
                    elif attr in ["lora_scale", "guidance_scale"]:
                        value = float(value)
                    elif attr == "disable_safety_checker":
                        value = value.lower() == "true"

                    setattr(self, attr, value)
                    if hasattr(self, f"{attr}_input"):
                        getattr(self, f"{attr}_input").value = value
                    elif hasattr(self, f"{attr}_select"):
                        getattr(self, f"{attr}_select").value = value
                    elif hasattr(self, f"{attr}_switch"):
                        getattr(self, f"{attr}_switch").value = value

        await self.save_settings()
        ui.notify("Parameters reset to default values", type="info")
        logger.info("Parameters reset to default values")

    async def start_generation(self):
        logger.debug("Starting image generation")
        if not self.api_key:
            ui.notify(
                "Please set your Replicate API Key in the settings.", type="negative"
            )
            logger.error("Cannot start generation: No API key set.")
            return
        if not self.replicate_model_select.value:
            ui.notify(
                "Please select a Replicate model before generating images.",
                type="negative",
            )
            logger.warning(
                "Attempted to generate images without selecting a Replicate model"
            )
            return

        await asyncio.to_thread(
            self.image_generator.set_model, self.replicate_model_select.value
        )

        await self.save_settings()
        params = {
            "prompt": self.prompt_input.value,
            "flux_model": self.flux_model,
            "aspect_ratio": self.aspect_ratio,
            "num_outputs": self.num_outputs,
            "lora_scale": self.lora_scale,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            "output_format": self.output_format,
            "output_quality": self.output_quality,
            "disable_safety_checker": self.disable_safety_checker,
        }

        if self.aspect_ratio == "custom":
            params["width"] = self.width
            params["height"] = self.height

        if self.seed != -1:
            params["seed"] = self.seed

        self.generate_button.disable()
        self.progress.visible = True
        ui.notify("Generating images...", type="info")
        logger.info(f"Generating images with params: {json.dumps(params, indent=2)}")

        try:
            output = await asyncio.to_thread(
                self.image_generator.generate_images, params
            )
            await self.download_and_display_images(output)
            logger.success(f"Images generated successfully: {output}")
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            ui.notify(error_message, type="negative")
            logger.exception(error_message)
        finally:
            self.generate_button.enable()
            self.progress.visible = False

    # def create_zip_file(self):
    #     logger.debug("Creating zip file of generated images")
    #     if not self.last_generated_images:
    #         ui.notify("No images to download", type="warning")
    #         logger.warning("No images to zip")
    #         return None
    #
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     zip_filename = f"generated_images_{timestamp}.zip"
    #     zip_path = Path(self.output_folder) / zip_filename
    #
    #     with zipfile.ZipFile(zip_path, "w") as zipf:
    #         for image_path in self.last_generated_images:
    #             zipf.write(image_path, Path(image_path).name)
    #     logger.info(f"Zip file created: {zip_path}")
    #     return str(zip_path)
    #
    # def download_zip(self):
    #     logger.debug("Downloading zip file")
    #     zip_path = self.create_zip_file()
    #     if zip_path:
    #         ui.download(zip_path)
    #         ui.notify("Downloading zip file of generated images", type="positive")
    #
    async def update_gallery(self, image_paths):
        logger.debug("Updating image gallery")
        self.gallery_container.clear()
        self.last_generated_images = image_paths
        with self.gallery_container:
            with ui.row().classes("w-full"):
                with ui.grid(columns=2).classes("md:grid-cols-3 w-full gap-2"):
                    for image_path in image_paths:
                        self.lightbox.add_image(
                            image_path, image_path, "w-full h-full object-cover"
                        )
        logger.debug("Image gallery updated")

    async def download_and_display_images(self, image_urls):
        logger.debug("Downloading and displaying generated images")
        downloaded_images = []
        async with httpx.AsyncClient() as client:
            for i, url in enumerate(image_urls):
                logger.debug(f"Downloading image from {url}")
                response = await client.get(url)
                if response.status_code == 200:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    url_part = urllib.parse.urlparse(url).path.split("/")[-2][:8]
                    file_name = f"generated_image_{timestamp}_{url_part}_{i+1}.png"
                    file_path = Path(self.output_folder) / file_name
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    downloaded_images.append(str(file_path))
                    logger.info(f"Image downloaded: {file_path}")
                else:
                    logger.error(f"Failed to download image from {url}")

        await self.update_gallery(downloaded_images)
        ui.notify("Images generated and downloaded successfully!", type="positive")
        logger.success("Images downloaded and displayed")

    async def save_settings(self):
        logger.debug("Saving settings")
        for attr in self._attributes:
            value = getattr(self, attr)
            if attr == "models":
                value = json.dumps({"user_added": list(self.user_added_models.keys())})
            Settings.set_setting("default", attr, str(value))

        Settings.set_setting(
            "default", "replicate_model", self.replicate_model_select.value
        )

        Settings.save_settings()
        logger.info("Settings saved successfully")


async def create_gui(image_generator):
    logger.debug("Creating GUI")
    gui = ImageGeneratorGUI(image_generator)
    gui.setup_ui()
    logger.debug("GUI created")
    return gui
