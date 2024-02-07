# Import necessary modules
import azure.functions as func
import logging
import os
from azure.appconfiguration import AzureAppConfigurationClient
import json
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
    logging.info("get_config function processing a request.")
    # Check if Redis is configured
    is_redis_configured = REDIS_HOST and REDIS_PORT and REDIS_PASSWORD and REDIS_DB
    label_filter = req.params.get("label_filter")
    if not label_filter:
        logging.warning("Missing label_filter parameter.")
        return func.HttpResponse("Missing label_filter parameter", status_code=400)
    
    redis_key = f"config:{label_filter}"
    if is_redis_configured:
        # If Redis is configured, check if the configuration is cached
        cached_config = get_cached_config(redis_key)
        if cached_config:
            return func.HttpResponse(cached_config, mimetype="application/json")

    config_dict = get_config_from_app_config(label_filter)
    if not config_dict:
        logging.warning("No config settings found.")
        return func.HttpResponse("No config settings found", status_code=404)

    if is_redis_configured:
        # If Redis is configured, set the configuration in the cache
        set_config_in_cache(redis_key, config_dict)

    return func.HttpResponse(
        json.dumps(config_dict), mimetype="application/json", status_code=200
    )


def get_cached_config(redis_key):
    """
    Retrieves the cached configuration from Redis based on the given key.

    Args:
        redis_key (str): The key used to retrieve the cached configuration from Redis.

    Returns:
        str: The cached configuration if found, None otherwise.
    """
    try:
        cached_config = redis_client.get(redis_key)
        logging.info(f"Redis cached config for key {redis_key}: {cached_config}")
        return cached_config
    except redis.ConnectionError:
        logging.error("Failed to connect to Redis")
        return None


def get_config_from_app_config(label_filter):
    """
    Retrieves configuration settings from Azure App Configuration based on the provided label filter.

    Args:
        label_filter (str): The label filter to apply when retrieving configuration settings.

    Returns:
        dict: A dictionary containing the configuration settings, where the key is the setting key and the value is the setting value.
    """
    config_settings = app_config_client.list_configuration_settings(label_filter=label_filter)
    config_dict = {setting.key: json.loads(setting.value).get("enabled") if ".appconfig.featureflag/" in setting.key else setting.value for setting in config_settings}
    return config_dict


def set_config_in_cache(redis_key, config_dict):
    """
    Sets the configuration dictionary in the Redis cache with the specified Redis key.

    Args:
        redis_key (str): The key to use for storing the configuration dictionary in Redis.
        config_dict (dict): The configuration dictionary to be stored in Redis.

    Raises:
        redis.ConnectionError: If there is a connection error while trying to connect to Redis.

    Returns:
        None
    """
    try:
        redis_client.set(redis_key, json.dumps(config_dict))
        redis_client.expire(redis_key, REDIS_KEY_EXPIRATION)
        logging.info(f"Set Redis key: {redis_key}")
    except redis.ConnectionError:
        logging.error("Failed to connect to Redis")
