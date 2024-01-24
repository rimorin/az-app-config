import azure.functions as func
import logging
import os
from azure.appconfiguration import AzureAppConfigurationClient
import json
from redis import Redis

CONNECTION_STRING = os.environ.get("APPCONFIGURATION_CONNECTION_STRING")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "password")
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_KEY_EXPIRATION = int(os.environ.get("REDIS_KEY_EXPIRATION", 60))
client = AzureAppConfigurationClient.from_connection_string(CONNECTION_STRING)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

redis = Redis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB, ssl=True
)


@app.route(route="get_config")
def get_config(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_config function started.")
    try:
        label_filter = req.params.get("label_filter")
        if not label_filter:
            return func.HttpResponse("Missing label_filter parameter", status_code=400)

        redis_key = f"config:{label_filter}"
        cached_config = None
        if redis.connection:
            cached_config = redis.get(redis_key)
        if cached_config:
            logging.info("get_config function completed successfully.")
            return func.HttpResponse(cached_config, mimetype="application/json")

        config_settings = client.list_configuration_settings(label_filter=label_filter)

        config_dict = {setting.key: setting.value for setting in config_settings}

        if not config_dict:
            return func.HttpResponse("No config settings found", status_code=404)

        logging.info("get_config function completed successfully.")
        if redis.connection:
            redis.set(redis_key, json.dumps(config_dict))
            redis.expire(redis_key, REDIS_KEY_EXPIRATION)
        return func.HttpResponse(
            json.dumps(config_dict), mimetype="application/json", status_code=200
        )

    except ValueError as ve:
        logging.error(f"Value{str(ve)}")
        return func.HttpResponse("An error occurred", status_code=500)

    except Exception as e:
        logging.error(f"Unexpected {str(e)}")
        return func.HttpResponse("An error occurred", status_code=500)
