import json
import os
import openai
from asgiref.sync import sync_to_async


def get_config_path() -> str:
    config_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(config_dir, 'config.json')

def get_config() -> dict:
    try:
        config_path = get_config_path()
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from config.json.")
        return {}

# Update an aspect of JSON file (str) to a new value (value)
def update_config(key: str, value) -> None:
    try:
        config_path = get_config_path()

        # Load the current config data
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Update the specified key with the new value
        config[key] = value

        # Save the updated config back to the JSON file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"Updated '{key}' in config.json.")

    except FileNotFoundError:
        print("Error: config.json file not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from config.json.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Async wrapper for update_config
@sync_to_async
def async_update_config(key: str, value) -> None:
    update_config(key, value)

config = get_config()
openai.api_key = config['openAI-key']

async def handle_response(message) -> str:
    response = await sync_to_async(openai.Completion.create)(
        model="text-davinci-003",
        prompt=message,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    responseMessage = response.choices[0].text

    return responseMessage