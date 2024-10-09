from nicegui import ui
from datetime import datetime
import zipfile
from loguru import logger
from pathlib import Path


class FileHandler:
    @staticmethod
    def create_zip_file(last_generated_images, output_folder):
        logger.debug("Creating zip file of generated images")
        if not last_generated_images:
            ui.notify("No images to download", type="warning")
            logger.warning("No images to zip")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"generated_images_{timestamp}.zip"
        zip_path = Path(output_folder) / zip_filename

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for image_path in last_generated_images:
                zipf.write(image_path, Path(image_path).name)
        logger.info(f"Zip file created: {zip_path}")
        return str(zip_path)

    @staticmethod
    def download_zip(last_generated_images, output_folder):
        logger.debug("Downloading zip file")
        zip_path = FileHandler.create_zip_file(last_generated_images, output_folder)
        if zip_path:
            ui.download(zip_path)
            ui.notify("Downloading zip file of generated images", type="positive")
