from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
import os

MODELS = {
    "GPT_4O_mini": "gpt-4o-mini-2024-07-18"
}

PROMPT = """
<Start Title Info>
__TEXT_TITLE__
</End Title Info>
<Start message Info>
__TEXT_MESSAGE__
</End message Info>
<Start Task>
Here is the title and message for a travel campaign. Please improve the message by making it 
more engaging, emphasizing the offer's benefits, and including a clear CTA. 
</End Task>

<Start Specifications>
- The lenguage of title and message are in spanish, return them in spanish too.
- Remove this type of characteres "\n"
- Add emoji to message
</End Specification>
"""

SYSTEM_INSTRUCTION = """
You are a marketing expert specializing in creating engaging and persuasive WhatsApp messages
for a travel agency. Your goal is to make the messages attractive, concise, and action-oriented
to capture customers' attention. Focus on emphasizing the unique aspects of the offer, creating
a sense of urgency, and including a clear call-to-action (CTA). The tone should be friendly and
professional.

Aditional details: The title and message provided will be in spanish, you will return title and 
message improved in spanish too.

Output structure: Please ensure your resultadheres to the following structure:
{
    "title": str
    "message": str
}


"""

class MessageImproved(BaseModel):
    title: str
    message: str


class ChatGpt:
    def __init__(self, model:str, system_instruction: Optional[str]=None, temperature=0.1):
        self.client = OpenAI(organization=os.getenv("ORGANIZATION_ID"),
                             project=os.getenv("PROJECT_ID"),
                             api_key=os.getenv("CHATGPT_KEY"))
        self.model = model
        self.tokens = 9000
        self.system_instruction = system_instruction
        self.temperature = temperature
    
    def generate(self, prompt: str, respose_format: BaseModel):
        context = []
        if self.system_instruction == None:
            context = [{"role": "system", "content": self. system_instruction}]
        context.append({"role": "user", "content": prompt})

        completion = self.client.beta.chat.completions.parse(
            model= self.model,
            temperature=self.temperature,
            messages=context,
            response_format= respose_format
        )


        event = completion.choices[0].message
        return {
            'output': event.parsed.model_dump() if not event.refusal else None,
            'refusal': event.refusal,
            'usage': completion.usage.to_dict()
        }

@staticmethod
def prepare_message_for_prompt(obj_message: dict):
    res_message = {}
    messages_list = obj_message.get("messages", [])
    for value in messages_list:
        key_date = str(value["date"]).split(".")[0]
        res_message[key_date] = value["text"]
    return res_message