from typing import Union

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI

import os
import json

app = FastAPI()
api_key=os.getenv("OPENAI_API_KEY")
base_url="https://ark.cn-beijing.volces.com/api/v3"
model="doubao-seed-1-6-250615"
instructions="你是一个幽默的小助手，善于用幽默的方式回答问题"

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.get("/chat/response")
def openai_response(content: str):
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=content
    )
    return {"content":response.output_text}

@app.get("/chat/completion")
def openai_completion(content: str):
    client = OpenAI(api_key=api_key, base_url=base_url)
    completion = client.chat.completions.create(model=model, messages=[
        {'role': 'system', 'content': instructions},
        {'role': 'user', 'content': content}
    ])
    content = completion.choices[0].message.content
    return {"content": content}

@app.post("/chat/stream")
async def openai_stream(request: ChatRequest):
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    async def event_generator():
        try:
            stream = await client.chat.completions.create(model=model, messages=[
                {'role': 'system', 'content': instructions},
                {'role': 'user', 'content': request.message}
            ], stream=True)
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    data = json.dumps({"content": chunk.choices[0].delta.content})
                    yield f"data: {data}\n\n"
            yield f"data: [DONE]\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")