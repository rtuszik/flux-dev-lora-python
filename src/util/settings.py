import configparser
import os
from typing import Any, Type

from loguru import logger

DOCKERIZED = os.environ.get("DOCKER_CONTAINER", "False").lower() == "true"
CONFIG_DIR = "/app/settings" if DOCKERIZED else "."
DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")
USER_CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.user.ini")

logger.info(
    f"Configuration files: DEFAULT={DEFAULT_CONFIG_FILE}, USER={USER_CONFIG_FILE}"
)

config = configparser.ConfigParser()
config.read([DEFAULT_CONFIG_FILE, USER_CONFIG_FILE])
logger.info("Configuration files loaded")


class Settings:
    def get_api_key():
        api_key = os.environ.get("REPLICATE_API_KEY") or config.get(
            "secrets", "REPLICATE_API_KEY", fallback=None
        )
        if api_key:
            logger.info("API key retrieved successfully")
        else:
            logger.warning("No API key found")
        return api_key

    def get_setting(
        section: str, key: str, fallback: Any = None, value_type: Type[Any] = str
    ) -> Any:
        logger.info(
            f"Attempting to get setting: section={section}, key={key}, fallback={fallback}, value_type={value_type}"
        )
        try:
            value = config.get(section, key)
            logger.debug(f"Raw value retrieved: {value}")
            if value_type is int:
                result = int(value)
            elif value_type is float:
                result = float(value)
            elif value_type is bool:
                result = value.lower() in ("true", "yes", "1", "on")
            else:
                result = value
            logger.info(f"Setting retrieved successfully: {result}")
            return result
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logger.warning(
                f"Setting not found: {str(e)}. Using fallback value: {fallback}"
            )
            return fallback
        except ValueError as e:
            logger.error(
                f"Error converting setting value: {str(e)}. Using fallback value: {fallback}"
            )
            return fallback

    def set_setting(section, key, value):
        logger.info(f"Setting value: section={section}, key={key}, value={value}")
        if not config.has_section(section):
            logger.info(f"Creating new section: {section}")
            config.add_section(section)
        config.set(section, key, str(value))
        logger.info("Value set successfully")

    def save_settings():
        logger.info(f"Saving settings to {USER_CONFIG_FILE}")
        try:
            with open(USER_CONFIG_FILE, "w") as configfile:
                config.write(configfile)
            logger.info("Settings saved successfully")
        except IOError as e:
            logger.error(f"Error saving settings: {str(e)}")


logger.info("Config module initialized")
