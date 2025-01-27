from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
import os

MODELS = {
    "GPT_4O_mini": "gpt-4o-mini-2024-07-18"
}

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
