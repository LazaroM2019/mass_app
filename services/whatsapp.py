from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os

# Initialize the scheduler (ensure it's started only once)
scheduler = BackgroundScheduler()
scheduler.start()

# WHATSAPP credentials saved
WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
WHATSAPP_AUTH_TOKEN = os.getenv('WHATSAPP_AUTH_TOKEN')

# WHATSAPP API ENDPOINT
URL_WHATSAPP = f"https://graph.facebook.com/v21.0/{WHATSAPP_ACCOUNT_SID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Function to send a WhatsApp message
def send_whatsapp_message(number, formatted_message):
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {"body": formatted_message}
    }
    try:
        response = requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)
        if response.status_code == 200:
            return {"status": "success", "message_sid": response.json()}
        else:
            return {"status": "failed", "error": response.text}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Function to schedule a WhatsApp message
def schedule_whatsapp_message(title, message, numbers, send_time):
    formatted_message = f"*{title}*\n\n{message}"
    for number in numbers:
        scheduler.add_job(
            send_whatsapp_message,
            'date',
            run_date=send_time,
            args=[number, formatted_message]
        )
