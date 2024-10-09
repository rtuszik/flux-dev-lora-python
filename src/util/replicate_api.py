import json
import os

import replicate
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class Replicate_API:
    def __init__(self):
        self.replicate_model = None
        self.api_key = None
        self.client = None
        logger.info("ImageGenerator initialized")

    def set_api_key(self, api_key):
        self.api_key = api_key
        os.environ["REPLICATE_API_KEY"] = api_key
        self.client = replicate.Client(api_token=self.api_key)
        logger.info("API key set and client initialized")

    def set_model(self, replicate_model):
        self.replicate_model = replicate_model
        logger.info(f"Model set to: {replicate_model}")

    def get_model_version(self, user_input):
        if not self.client:
            error_message = (
                "No API key set. Please set an API key before getting model version."
            )
            logger.error(error_message)
            raise ImageGenerationError(error_message)

        logger.info(f"Parsing model string: {user_input}")
        if ":" in user_input:
            logger.debug("Model string contains version")
            return user_input
        else:
            logger.debug("Model string does not contain version")
            owner, name = user_input.split("/")
            logger.debug(f"Retrieving latest version for {owner}/{name}")
            if not self.client:
                error_message = "No API key set. Please set an API key before getting model version."
                logger.error(error_message)
                raise ImageGenerationError(error_message)

            model = self.client.models.get(f"{owner}/{name}")
            version = model.latest_version.id
            latest_version = f"{owner}/{name}:{version}"
            logger.info(f"Latest version retrieved: {latest_version}")
            return latest_version

    def generate_images(self, params):
        if not self.replicate_model:
            error_message = (
                "No Replicate model set. Please set a model before generating images."
            )
            logger.error(error_message)
            raise ImageGenerationError(error_message)

        if not self.client:
            error_message = (
                "No API key set. Please set an API key before generating images."
            )
            logger.error(error_message)
            raise ImageGenerationError(error_message)

        try:
            flux_model = params.pop("flux_model", "dev")
            params["model"] = flux_model
            logger.info(
                f"Generating images with params: {json.dumps(params, indent=2)}"
            )
            logger.info(f"Using Replicate model: {self.replicate_model}")

            output = self.client.run(self.replicate_model, input=params)
            logger.success(f"Images generated successfully. Output: {output}")
            return output
        except Exception as e:
            error_message = f"Error generating images: {str(e)}"
            logger.exception(error_message)
            raise ImageGenerationError(error_message)


class ImageGenerationError(Exception):
    pass
