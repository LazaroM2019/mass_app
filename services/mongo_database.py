

def save_message_to_mongodb(collection, message):
    """
    Save a message to MongoDB.

    :param connection_string: MongoDB connection string
    :param database_name: Name of the database
    :param collection_name: Name of the collection
    :param message: The message to save (as a dictionary)
    :return: The ID of the inserted document
    """
    try:
        # Insert the message
        result = collection.insert_one(message)
        print(f"Message inserted with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"An error occurred: {e}")
        return None