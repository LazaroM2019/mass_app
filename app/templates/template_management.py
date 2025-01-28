import json

def load_dynamic_template(name: str, title=None, message=None, media_id=None):
    if "general_text_dynamic" == name:
        template_path = "app/templates/schema/general_text_dynamic.json"
    if "general_image_dynamic" == name:
        template_path = "app/templates/schema/general_image_dynamic.json"
    if "general_doc_dynamic" == name:
        template_path = "app/templates/schema/general_doc_dynamic.json"    
    with open(template_path, "r") as file:
        template_schema = json.load(file)
    
    if "general_text_dynamic" == name:
        template_schema["components"][0]["parameters"][0]["text"] = title
        template_schema["components"][1]["parameters"][0]["text"] = message


    if "general_image_dynamic" == name:
        template_schema["components"][0]["parameters"][0]["image"]["id"] = media_id
        template_schema["components"][1]["parameters"][0]["text"] = title
        template_schema["components"][1]["parameters"][1]["text"] = message    
    
    if "general_doc_dynamic" == name:
        template_schema["components"][0]["parameters"][0]["document"]["id"] = media_id
        template_schema["components"][1]["parameters"][0]["text"] = title
        template_schema["components"][1]["parameters"][1]["text"] = message

    return template_schema

def load_prompt_template(name:str):
   if "message_suggestion" == name:
       template_path = "app/templates/schema_prompts/message_suggestion.json"   
   with open(template_path, "r") as file:
       template_schema = json.load(file)
   return template_schema