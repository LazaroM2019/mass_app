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


def add_chat_message(user_id, number, text, date, is_client, status, message_id, client_name=""):
    mongo_service = MongoDBService()

    query = {"userId": user_id, "number": number}

    obj_client_name = {"userId": user_id, "number": number}
    if client_name is not None and client_name != "":
        obj_client_name["client_name"] = client_name
        
    update = {
        "$set": obj_client_name,
        "$push": {"messages": {
            "text": text,
            "date": date,
            "is_client": is_client,
            "status": status,
            "id": message_id
            }
        }
    }
    
    mongo_service.upsert_to_collection("chats_history", query, update)

@staticmethod
def update_message_status(user_id, number, status_tag, message_waid):
    mongo_service = MongoDBService()

    # Filter to select the document
    filter_criteria = {"userId": user_id, "number": number}

    # Update operation
    update_operation = {
        "$set": {
            "messages.$[elem].status": status_tag
        }
    }

    # Define array filters
    array_filters = [{"elem.id": message_waid}]

    # Include the array filters in the update
    update_with_filters = {
        update_operation,
        array_filters
    }

    # Perform the upsert
    result = mongo_service.upsert_to_collection(
        collection_name="chats_history",
        query=filter_criteria,
        update=update_with_filters
    )
    
    # mongo_service.upsert_to_collection("chats_history", filter_criteria, update_operation)
    
@staticmethod
def get_whatsapp_credentials(user_id, phone_number):
    mongo_service = MongoDBService()

    filter_id = {"_id": user_id} 
    filter_phone = {"phone": phone_number}


    user_by_id = mongo_service.get_document_by_filter("users", filter_id)
    user_by_phone = mongo_service.get_document_by_filter("users", filter_phone)

    if user_by_id is not None and user_by_id["wappPhoneNumberId"] is not None:
        return user_by_id["wappPhoneNumberId"]
    elif user_by_phone is not None and user_by_phone["wappPhoneNumberId"] is not None:
        return user_by_phone["wappPhoneNumberId"]
    
    WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
    return WHATSAPP_ACCOUNT_SID

@staticmethod
def get_user_id_from_phonenumber(phone_number):
    mongo_service = MongoDBService()

    filter = {"phone": phone_number} 

    user = mongo_service.get_document_by_filter("users", filter)

    if user is not None and user["_id"] is not None:
        return str(user["_id"])
    
    return None

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