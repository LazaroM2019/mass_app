

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