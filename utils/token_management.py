import requests
import os
from dotenv import set_key


class TokenManager:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret

    def get_long_lived_token(self, short_lived_token):
        url = "https://graph.facebook.com/v21.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            raise Exception(f"Error refreshing token: {response.text}")

    def save_token_to_env(self, token, env_var_name="WHATSAPP_AUTH_TOKEN", env_file=".env"):
        os.environ[env_var_name] = token
        set_key(env_file, env_var_name, token)
        print(f"Token saved to environment variable: {env_var_name} and .env file.")

def refresh_token_task():
    """Task to refresh the token."""
    try:
        # Fetch credentials from environment
        app_id = os.getenv("APP_ID")
        app_secret = os.getenv("APP_SECRET")
        short_lived_token = os.getenv("WHATSAPP_AUTH_TOKEN")

        # Initialize TokenManager
        token_manager = TokenManager(app_id, app_secret)
        long_lived_token = token_manager.get_long_lived_token(short_lived_token)

        # Save the new token
        token_manager.save_token_to_env(long_lived_token)
        print("Token refreshed successfully.")
    except Exception as e:
        print(f"Error refreshing token: {e}")




