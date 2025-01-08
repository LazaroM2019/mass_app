from pymongo import MongoClient
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
    
    def close_connection(self):
        self.client.close()


def add_chat_message(user_id, number, text, date, is_client, status, message_id):
    mongo_service = MongoDBService()

    query = {"userId": user_id, "number": number}
        
    update = {
        "$set": {"userId": user_id, "number": number},
        "$push": {"messages": {
            "text": text,
            "date": date,
            "is_client": is_client,
            "status": status,
            "id": message_id
        }}
    }
    
    mongo_service.upsert_to_collection("chats_history", query, update)

def update_message_status(user_id, number, status):
    mongo_service = MongoDBService()

    query = {"userId": user_id, "number": number}
        
    update = {
        "$set": {"userId": user_id, "number": number},
        "$push": {"messages": {
            "status": status
        }}
    }
    
    mongo_service.upsert_to_collection("chats_history", query, update)
    

def get_whatsapp_credentials(user_id):
    mongo_service = MongoDBService()

    filter = {"_id": user_id} 

    user = mongo_service.get_document_by_filter("users", filter)

    if user is not None and user.whatsapp_id is not None:
        return user.whatsapp_id
    
    WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
    return WHATSAPP_ACCOUNT_SID

def get_whatsapp_credentials_from_phonenumber(phone_number):
    mongo_service = MongoDBService()

    filter = {"phone": phone_number} 

    user = mongo_service.get_document_by_filter("users", filter)

    if user is not None and user.whatsapp_id is not None:
        return user.whatsapp_id
    
    WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
    return WHATSAPP_ACCOUNT_SID

def save_to_mongodb(database, collection_name, data):
    """
    Save data to MongoDB.

    :param collection: The MongoDB collection object
    :param data: The data to save (as a dictionary)
    :return: The ID of the inserted document
    """
    try:
        # Insert the data
        collection = database[collection_name]
        result = collection.insert_one(data)
        print(f"Data inserted with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"An error occurred: {e}")
        return None