import sys

from loguru import logger
from nicegui import ui
import util
from gui import ImageGeneratorGUI

logger.add(
    sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO"
)
logger.add(
    "app.log",
    format="{time} {level} {module}:{line} {message}",
    level="INFO",
    rotation="500 MB",
    compression="zip",
)


logger.info("Initializing ImageGenerator")
generator = util.Replicate_API()

api_key = util.Settings.get_api_key()
if api_key:
    generator.set_api_key(api_key)
else:
    logger.warning("No Replicate API Key found. Please set it in the settings.")

logger.info("Creating and setting up GUI")


@ui.page("/")
async def main_page():
    logger.debug("Creating GUI")
    gui = ImageGeneratorGUI(generator)
    gui.setup_ui()
    logger.debug("GUI created")


logger.info("Starting NiceGUI server")

ui.run(title="Replicate Flux LoRA", port=8080, favicon="🚀")
