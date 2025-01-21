import base64
import os

def save_base64_to_jpeg(base64_code, filename):
    """
    Convert a Base64 encoded string to a JPEG file and save it to a specified folder.

    Args:
        base64_code (str): The Base64 encoded string of the image.
        output_folder (str): The folder where the image will be saved.
        filename (str): The name of the output JPEG file.

    Returns:
        str: The path to the saved image.
    """
    output_folder = "temp_files"
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Decode the Base64 string
    image_data = base64.b64decode(base64_code)

    # Define the file path
    file_path = os.path.join(output_folder, filename)

    # Write the decoded image to a file
    with open(file_path, "wb") as image_file:
        image_file.write(image_data)
        
    return file_path
