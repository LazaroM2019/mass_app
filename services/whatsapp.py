import base64
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import requests
import os
from utils.logger import logger
from datetime import datetime, timezone
from services.mongo_database import add_chat_message, get_company_info, get_whatsapp_credentials, update_message_whats_app_status
from templates.template_management import load_dynamic_template
from utils.image_procesor import save_base64_to_jpeg
import uuid
import re
from services.telegram import TelegramService

# Initialize the scheduler (ensure it's started only once)
executors = {
    'default': ThreadPoolExecutor(2)  # Increase from default (10) to 20
}
scheduler = BackgroundScheduler(executors=executors)
scheduler.start()

# WHATSAPP credentials saved
WHATSAPP_AUTH_TOKEN = os.getenv('WHATSAPP_AUTH_TOKEN')

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

telegram_service = TelegramService()

# Function to send a WhatsApp message
def send_whatsapp_message(message_id, user_id, number, title_front, text_front, image_base64, doc_base64):
    title = title_front + "\r"
    logger.info(repr(text_front))    
    text_front = re.sub(r'(\r\n){4,}', '\r\n' * 3, text_front)
    message = text_front.replace("\r\n", "\r")

    company_id = get_company_info(user_id, "user", "id")
    logger.info(f"Company: {company_id}")
    account_id = get_whatsapp_credentials(company_id)

    try:
        if title_front == "chat_only":
            logger.info(f"Sending chat message to: {number}")
            response = send_chat_message(company_id, account_id, number, message, image_base64, doc_base64)
        else:
            logger.info(f"Sending initial message to: {number}")
            response = send_initial_message(account_id, number, title, message, image_base64, doc_base64)

        if response.status_code == 200:
            json_response = response.json()
            logger.info(f"WHATSAPP: Message sent successfully {json_response}")
            update_message_whats_app_status(message_id, number, "delivered")            
            return {"status": "success", "message_sid": response.json()}
        else:
            logger.info(f"Message faild: {response.text}")
            telegram_service.send_message(f"WHATSAPP API FALIED for {number}: {response.text}")
            return {"status": "failed", "error": response.text}
    except Exception as e:
        logger.error(str(e))
        telegram_service.send_message("WhatsApp exception")
        return {"status": "failed", "error": str(e)}


# Function to schedule a WhatsApp message
def schedule_whatsapp_message(message_id, user_id, title, message, numbers, send_time, image, doc_file):
    for number in numbers:
        scheduler.add_job(
            send_whatsapp_message,
            'date',
            run_date=send_time,
            args=[message_id, user_id, number, title, message, image, doc_file],
            misfire_grace_time=30 
        )

def upload_media(phone_number_id: str, file_name: str, type_of_file: str):
    if type_of_file == "image":
        file_type = "image/jpeg" 
    if type_of_file == "document":
        file_type = "application/pdf"
    
    name = file_name.split("/")[-1]
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/media"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_AUTH_TOKEN}"
    }
    
    with open(file_name, 'rb') as file:
        files = {
            'file': (name, file, file_type),
        }
        payload_data = {
            'messaging_product': 'whatsapp',
        }
    
        response = requests.post(url, headers=headers, data=payload_data, files=files)
        if response.status_code == 200:
            media_id = response.json()["id"]
            logger.info("Upload file successfully!!!")
        else:
            logger.error(response.text)
    
    os.remove(file_name)
    return media_id


def initiate_upload(file_length, file_name, access_token):
    url = f'https://graph.facebook.com/v21.0/app/uploads/?file_length={file_length}&file_type=image/jpeg&file_name={file_name}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        raise Exception('Failed to initiate upload')
    
    data = response.json()
    logger.info(data)
    return data['id'] 


def upload_image_chunk(upload_id, file, access_token):

    headers = {
        'Authorization': f'OAuth {access_token}',
        'Content-Type': 'image/jpeg',
        'file_offset': '0'
    }

    response = requests.post(
            f'https://graph.facebook.com/v21.0/{upload_id}',
            headers=headers,
            data=file
        )

    data = response.json()
    logger.info(data)

    return data["h"]  # Return the file handle to be used in the next step


def update_business_profile(phone_number_id, file_handle, access_token):
    url = f'https://graph.facebook.com/v21.0/{phone_number_id}/whatsapp_business_profile'
    
    headers = {
        'Authorization': f'OAuth {access_token}',
        'Content-Type': 'application/json',
    }

    data = {
        "messaging_product": "whatsapp",
        "profile_picture_handle": file_handle,
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    logger.info(result)
    return response

def update_business_profile_image(base64_data, file_name, access_token, phone_number_id):
    # Step 1: Decode base64 to binary data
    byte_data = base64.b64decode(base64_data)
    
    # Step 2: Initiate the upload
    file_length = len(byte_data)
    upload_id = initiate_upload(file_length, file_name, access_token)

    # Step 3: Upload the image in chunks
    file_handle = upload_image_chunk(upload_id, byte_data, access_token)

    # Step 4: Update the business profile with the new image
    return update_business_profile(phone_number_id, file_handle, access_token)


def update_business_image(company_id, image_base64):
   
    account_id = get_whatsapp_credentials(company_id)
    logger.info(f"updating image for: {account_id} - {image_base64}")
    file_name = 'myprofile.jpg'

    response = update_business_profile_image(image_base64, file_name, WHATSAPP_AUTH_TOKEN, account_id)
    
    if response.status_code == 200:
        logger.info(f"Company photo updated: {company_id}")            
        return {"status": "success", "message_sid": response.json()}
    else:
        logger.info(f"Update faild: {response.text}")
        telegram_service.send_message(f"Update image error: {response.text}")
        return {"status": "failed", "error": response.text}


def send_initial_message(account_id, number, title, message, image_base64, doc_base64):
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "template",
        "template": {}
    }

    if image_base64 == "" and doc_base64 == "":        
        payload["template"] = load_dynamic_template(name="general_text_dynamic",title=title, message=message)
        
    if image_base64 != "":
        key_name = f"{str(uuid.uuid4())}.jpeg"
        path_file = save_base64_to_jpeg(image_base64, key_name)
        number_media_id = upload_media(account_id,path_file, "image")

        payload["template"] = load_dynamic_template(name="general_image_dynamic",title=title, message=message, media_id=number_media_id)
    
    if doc_base64 != "":
        pdf_name = f"{str(uuid.uuid4())}.pdf"
        path_file = save_base64_to_jpeg(doc_base64, pdf_name)
        number_media_id = upload_media(account_id, path_file, "document")
        
        payload["template"] = load_dynamic_template(name="general_doc_dynamic", title=title, message=message, media_id=number_media_id)

    URL_WHATSAPP = f"https://graph.facebook.com/v21.0/{account_id}/messages"
    return requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)

def send_chat_message(company_id, account_id, number, message, image_base64, doc_base64):
    URL_WHATSAPP = f"https://graph.facebook.com/v21.0/{account_id}/messages"
    
    number_media_id = ""

    payload = {
        "messaging_product": "whatsapp",
        "to": "59897222006",
        "recipient_type": "individual"
    }

    if image_base64 == "" and doc_base64 == "":
        payload["text"] = {
            "body": message
        }

    if image_base64 != "":
        key_name = f"{str(uuid.uuid4())}.jpeg"
        path_file = save_base64_to_jpeg(image_base64, key_name)
        number_media_id = upload_media(account_id,path_file, "image")

        payload["type"] = "image"
        payload["image"] = {
            "caption": message,
            "id": number_media_id
        }
    
    if doc_base64 != "":
        pdf_name = f"{str(uuid.uuid4())}.pdf"
        path_file = save_base64_to_jpeg(doc_base64, pdf_name)
        number_media_id = upload_media(account_id,path_file, "document")

        payload["type"] = "document"
        payload["document"] = {
            "caption": message,
            "id": number_media_id,
            "filename": "documento-pdf"
        }
    
    response = requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)
    json_response = response.json()
    logger.info(json_response)

    message_id_whatsApp = json_response['messages'][0].get("id")
    
    if response.status_code == 200:
        add_chat_message(company_id, number, message, datetime.now(timezone.utc), False, 'delivered', message_id_whatsApp, "", number_media_id)

    return response