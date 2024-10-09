from nicegui import ui
from loguru import logger


class Lightbox:
    def __init__(self):
        logger.debug("Initializing Lightbox")
        with ui.dialog().props("maximized").classes("bg-black") as self.dialog:
            self.dialog.on_key = self._handle_key
            self.large_image = ui.image().props("no-spinner fit=scale-down")
        self.image_list = []
        logger.debug("Lightbox initialized")

    def add_image(
        self,
        thumb_url: str,
        orig_url: str,
        thumb_classes: str = "w-32 h-32 object-cover",
    ) -> ui.button:
        logger.debug(f"Adding image to Lightbox: {orig_url}")
        self.image_list.append(orig_url)
        button = ui.button(on_click=lambda: self._open(orig_url)).props(
            "flat dense square"
        )
        with button:
            ui.image(thumb_url).classes(thumb_classes)
        logger.debug("Image added to Lightbox")
        return button

    def _handle_key(self, e) -> None:
        logger.debug(f"Handling key press in Lightbox: {e.key}")
        if not e.action.keydown:
            return
        if e.key.escape:
            logger.debug("Closing Lightbox dialog")
            self.dialog.close()
        image_index = self.image_list.index(self.large_image.source)
        if e.key.arrow_left and image_index > 0:
            logger.debug("Displaying previous image")
            self._open(self.image_list[image_index - 1])
        if e.key.arrow_right and image_index < len(self.image_list) - 1:
            logger.debug("Displaying next image")
            self._open(self.image_list[image_index + 1])

    def _open(self, url: str) -> None:
        logger.debug(f"Opening image in Lightbox: {url}")
        self.large_image.set_source(url)
        self.dialog.open()
