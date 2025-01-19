import json

def load_template(name: str, title=None, message=None, media_id=None):
    if "general_image" == name:
        template_path = "templates/schema/title_text_image_dynamic.json"
    if "image" == name:
        template_path = "templates/schema/image_dynamic.json"
    if "general" == name:
        template_path = "templates/schema/general_dynamic.json"
    if "chat_only" == name:
        template_path = "templates/schema/chat_only_dinamyc.json"
    if "document_general" == name:
        template_path = "templates/schema/document_dynamic.json"
    with open(template_path, "r") as file:
        template_schema = json.load(file)
    
    if "general" == name:
        template_schema["components"][0]["parameters"][0]["text"] = title
        template_schema["components"][1]["parameters"][0]["text"] = message

    if "chat_only" == name:
        template_schema["components"][0]["parameters"][0]["text"] = message

    if "image" == name:
        template_schema["components"][0]["parameters"][0]["image"]["id"] = media_id
        template_schema["components"][1]["parameters"][0]["text"] = message

    if "general_image" == name:
        template_schema["components"][0]["parameters"][0]["image"]["id"] = media_id
        template_schema["components"][1]["parameters"][0]["text"] = title
        template_schema["components"][1]["parameters"][1]["text"] = message
    
    if "document_general" == name:
        template_schema["components"][0]["parameters"][0]["document"]["id"] = media_id
        template_schema["components"][1]["parameters"][0]["text"] = title
        template_schema["components"][1]["parameters"][1]["text"] = message

    return template_schema
