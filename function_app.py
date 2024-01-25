# Import necessary modules
import azure.functions as func
import logging
import os
from azure.appconfiguration import AzureAppConfigurationClient
import json
import traceback
import redis
# Get environment variables for Azure App Configuration and Redis
CONNECTION_STRING = os.environ.get("APPCONFIGURATION_CONNECTION_STRING")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "password")
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
# Default expiration time for Redis key is 300 seconds (5 minutes)
REDIS_KEY_EXPIRATION = int(os.environ.get("REDIS_KEY_EXPIRATION", 300))

# Create Azure App Configuration client
app_config_client = AzureAppConfigurationClient.from_connection_string(CONNECTION_STRING)

# Create Azure Function App with anonymous authentication
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)


# Define Azure Function
@app.route(route="get_config")
def get_config(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_config function started.")
    try:
        # Get label_filter parameter from request
        label_filter = req.params.get("label_filter")
        if not label_filter:
            logging.warning("Missing label_filter parameter")
            return func.HttpResponse("Missing label_filter parameter", status_code=400)

        # Define Redis key
        redis_key = f"config:{label_filter}"
        cached_config = None
        try:
            # Get the cached configuration from Redis
            cached_config = redis_client.get(redis_key)
            logging.info(f"Redis cached config for key {redis_key}: {cached_config}")
        except redis.ConnectionError:
            logging.error("Failed to connect to Redis")
        if cached_config:
            logging.info("get_config function completed successfully.")
            return func.HttpResponse(cached_config, mimetype="application/json")

        # Get configuration settings from Azure App Configuration
        config_settings = app_config_client.list_configuration_settings(label_filter=label_filter)

        # Convert configuration settings to dictionary
        config_dict = {setting.key: setting.value for setting in config_settings}

        if not config_dict:
            logging.warning("No config settings found")
            return func.HttpResponse("No config settings found", status_code=404)

        logging.info("get_config function completed successfully.")
        try:
            # set configuration in Redis and set expiration time
            redis_client.set(redis_key, json.dumps(config_dict))
            redis_client.expire(redis_key, REDIS_KEY_EXPIRATION)
            logging.info(f"Set Redis key: {redis_key}")
        except redis.ConnectionError:
            logging.error("Failed to connect to Redis")
            
        return func.HttpResponse(
            json.dumps(config_dict), mimetype="application/json", status_code=200
        )

    # Handle general exception
    except Exception as error:
        logging.error(f"Unexpected error: {str(error)}, {traceback.format_exc()}")
        return func.HttpResponse("An error occurred", status_code=500)
