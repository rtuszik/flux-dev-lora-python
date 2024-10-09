from nicegui import ui
from loguru import logger
import asyncio
import json
from util import Settings


class UserModels:
    @ui.refreshable
    def model_list(self):
        logger.debug("Refreshing model list")
        for model in self.user_added_models:
            with ui.row().classes("w-full justify-between items-center"):
                ui.label(model)
                ui.button(
                    icon="delete",
                    on_click=lambda m=model: self.confirm_delete_model(m),
                    color="#818b981f",
                ).props("flat round color=red")

    async def open_user_model_popup(self):
        logger.debug("Opening user model popup")

        async def add_model():
            await self.add_user_model(new_model_input.value)

        with ui.dialog() as dialog, ui.card():
            ui.label("Manage Replicate Models").classes("text-xl font-bold mb-4")
            new_model_input = ui.input(label="Add New Model").classes("w-full mb-4")
            ui.button("Add Model", on_click=add_model, color="#818b981f")

            ui.label("Current Models:").classes("mt-4 mb-2")
            self.model_list()

            ui.button("Close", on_click=dialog.close, color="#818b981f").classes("mt-4")
        dialog.open()

    async def add_user_model(self, new_model):
        logger.debug(f"Adding user model: {new_model}")
        if new_model and new_model not in self.user_added_models:
            try:
                latest_v = await asyncio.to_thread(
                    self.image_generator.get_model_version, new_model
                )
                self.user_added_models[new_model] = latest_v
                self.model_options = list(self.user_added_models.values())
                self.replicate_model_select.options = self.model_options
                self.replicate_model_select.value = latest_v
                await self.update_replicate_model(latest_v)
                models_json = json.dumps(
                    {"user_added": list(self.user_added_models.values())}
                )
                Settings.set_setting("default", "models", models_json)
                save_settings()
                ui.notify(f"Model '{latest_v}' added successfully", type="positive")
                self.model_list.refresh()
                logger.info(f"User model added: {latest_v}")
            except Exception as e:
                logger.error(f"Error adding model: {str(e)}")
                ui.notify(f"Error adding model: {str(e)}", type="negative")
        else:
            logger.warning(f"Invalid model name or model already exists: {new_model}")
            ui.notify("Invalid model name or model already exists", type="negative")

    async def confirm_delete_model(self, model):
        logger.debug(f"Confirming deletion of model: {model}")
        with ui.dialog() as confirm_dialog, ui.card():
            ui.label(f"Are you sure you want to delete the model '{model}'?").classes(
                "mb-4"
            )
            with ui.row():
                ui.button(
                    "Yes",
                    on_click=lambda: self.delete_user_model(model, confirm_dialog),
                    color="1f883d",
                ).classes("mr-2")
                ui.button("No", on_click=confirm_dialog.close, color="cf222e")
        confirm_dialog.open()

    async def delete_user_model(self, model, confirm_dialog):
        logger.debug(f"Deleting user model: {model}")
        if model in self.user_added_models:
            del self.user_added_models[model]
            self.model_options = list(self.user_added_models.keys())
            self.replicate_model_select.options = self.model_options
            if self.replicate_model_select.value == model:
                self.replicate_model_select.value = None
                await self.update_replicate_model(None)
            models_json = json.dumps(
                {"user_added": list(self.user_added_models.keys())}
            )
            Settings.set_setting("default", "models", models_json)
            save_settings()
            ui.notify(f"Model '{model}' deleted successfully", type="positive")
            confirm_dialog.close()
            self.model_list.refresh()
            logger.info(f"User model deleted: {model}")
        else:
            logger.warning(f"Cannot delete model, not found: {model}")
            ui.notify("Cannot delete this model", type="negative")

    async def update_replicate_model(self, new_model):
        logger.debug(f"Updating Replicate model to: {new_model}")
        if new_model:
            await asyncio.to_thread(self.image_generator.set_model, new_model)
            self.replicate_model = new_model
            await self.save_settings()
            logger.info(f"Replicate model updated to: {new_model}")
            self.generate_button.enable()
        else:
            logger.warning("No Replicate model selected")
            self.generate_button.disable()
