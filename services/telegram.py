import requests
import os


class TelegramService:
    def __init__(self):
        self.bot_token = "7744367198:AAHy3N-ikdXjAUmPZLOtwhOAIVH8BFfNe-U"
        self.chat_id = "-4626335313"
        self.telegram_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message: str):
        """Send message to the specified Telegram chat."""
        if not message:
            raise ValueError("Message is required")

        try:
            # Send the message using Telegram API
            response = requests.post(
                self.telegram_url,
                json={"chat_id": self.chat_id, "text": message},
                headers={"Content-Type": "application/json"},
            )
            
            # Handle the response from Telegram
            response_data = response.json()
            if response.status_code == 200 and response_data.get("ok"):
                return {"success": True, "message": "Message sent"}
            else:
                return {"success": False, "message": response_data.get("description", "Unknown error")}
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error sending message: {e}")

