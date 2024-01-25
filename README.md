# Azure App Config Function

## Description

A simple Azure Function that reads a value from Azure App Config and returns it as a JSON object.

## Design

The function uses Redis as a distributed cache to store the configuration values. The first time the function is called, it will read the configuration values from Azure App Config and store them in Redis for a defined period of time. Subsequent calls to the function will read the configuration values from Redis instead of Azure App Config.

## Prerequisites

Before you begin, you need to have the following:

- An Azure account. If you don't have one, you can create a free account [here](https://azure.microsoft.com/en-us/free/).
- An Azure Function App setup. You can follow the instructions [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-azure-function) to create your first Azure Function.

## Configuration

You need to set the following environment variables in your Azure Function App settings:

1. `APPCONFIGURATION_CONNECTION_STRING`: Your Azure App Configuration connection string.
2. `REDIS_HOST`: The host of your Redis server. Default is `localhost`.
3. `REDIS_PORT`: The port of your Redis server. Default is `6379`.
4. `REDIS_PASSWORD`: The password of your Redis server. Default is `password`.
5. `REDIS_DB`: The database number of your Redis server. Default is `0`.
6. `REDIS_KEY_EXPIRATION`: The expiration time for Redis keys in seconds. Default is `300` (5 minutes).

Here's how you can set these variables:

1. Navigate to your Function App in the [Azure portal](https://portal.azure.com/).
2. Click on `Configuration` under the `Settings` section.
3. Click on `New application setting`.
4. Add the name and value for each setting and click `OK`.
5. Click `Save` on the top of the `Configuration` page to save your changes.

## Deployment

1. Install Azure CLI. You can download it from [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).

2. Login to your Azure account using Azure CLI:
    ```bash
    az login
    ```
3. Install Azure Functions Core Tools. You can download it from [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#v2).

4. Login to your Azure account using Azure Functions Core Tools:
    ```bash
    func azure login
    ```
5. Ensure that your `local.settings.json` file or your Azure Function App settings have the `FUNCTIONS_WORKER_RUNTIME` set to `python`.

6. Publish your function app:
    ```bash
    func azure functionapp publish <YourFunctionAppName>
    ```
## Accessing the Function API

Once your function app is deployed, you can access the `get_config` function API using the following URL:

```bash
https://<YourFunctionAppName>.azurewebsites.net/api/get_config?label_filter=<YourLabelFilter>
```

