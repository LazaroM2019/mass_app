from pymongo import MongoClient
from bson import ObjectId
import os

class MongoDBService:
    def __init__(self):
        self.client = MongoClient("mongodb+srv://inland:9sFRBksRbIgC4htj@cluster0.tha5gev.mongodb.net/inland_data_uy?retryWrites=true&w=majority")
        self.database = self.client["inland_data_uy"]

    def get_document_by_filter(self, collection_name: str, filter: dict):
        collection = self.database[collection_name]
        document = collection.find_one(filter)
        return document

    def write_to_collection(self, collection_name: str, data: dict):
        collection = self.database[collection_name]
        result = collection.insert_one(data)
        return result.inserted_id

    def upsert_to_collection(self, collection_name: str, query, update):
        collection = self.database[collection_name]
        
        result = collection.update_one(query, update, upsert=True)
        
        return result.upserted_id if result.upserted_id else result.modified_count
    
    def update_one(self, collection_name: str, query, update):
        collection = self.database[collection_name]  
        result = collection.update_one(query, update)
        return result.modified_count
    
    def close_connection(self):
        self.client.close()

@staticmethod
def add_chat_message(company_id, number, text, date, is_client, status, message_id, client_name=""):
    mongo_service = MongoDBService()

    query = {"companyId": company_id, "number": number}

    obj_client_name = {"companyId": company_id, "number": number}
    if client_name is not None and client_name != "":
        obj_client_name["client_name"] = client_name
        
    update = {
        "$set": obj_client_name,
        "$push": {"messages": {
            "text": text,
            "date": date,
            "is_client": is_client,
            "new": is_client,
            "status": status,
            "id": message_id
            }
        }
    }
    
    mongo_service.upsert_to_collection("chats_history", query, update)

@staticmethod
def update_message_whats_app_status(message_id, number, status):
    mongo_service = MongoDBService()

    mongo_service.update_one(
        "messages", 
        { 
            "_id": ObjectId(message_id), 
            "numbers.number": number 
        },
        { 
            "$set": { "numbers.$.status": status }
        })

    
@staticmethod
def get_whatsapp_credentials(company_id):
    mongo_service = MongoDBService()

    obj_company_id = ObjectId(company_id)
    filter_id = {"_id": obj_company_id} 
    company_by_id = mongo_service.get_document_by_filter("companies", filter_id)

    if company_by_id is not None and company_by_id["whatsappAccountId"] is not None:
        return company_by_id["whatsappAccountId"]    
    
    WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
    return WHATSAPP_ACCOUNT_SID

@staticmethod
def get_company_id_from_phonenumber(phone_number):
    mongo_service = MongoDBService()

    filter = {"phone": phone_number} 

    company = mongo_service.get_document_by_filter("companies", filter)

    if company is not None and company["_id"] is not None:
        return str(company["_id"])
    
    return None

@staticmethod
def get_company_from_user(user_id):
    mongo_service = MongoDBService()

    filter = {"users":  ObjectId(user_id) }

    company = mongo_service.get_document_by_filter("companies", filter)

    if company is not None and company["_id"] is not None:
        return str(company["_id"])
    
    return None