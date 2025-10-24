from fastapi import FastAPI
from enum import Enum
from typing import Union
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/item/{item_id}")
async def read_item(item_id: int): #aca definimos que el parametro que recibe es int
    return {"item_id": item_id}

#Usando Enum
class ModelName(str, Enum): #Creo una clase Enum 
    juanes = "Juanes"
    camila = "Camila"
    carlos = "Carlos"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.juanes:
        return {"model_name": model_name, "message": "Llamaste a Juanes"}

    if model_name.value == "Camila": #Otra forma de comparar
        return {"model_name": model_name, "message": "Camila está disponible"}

    return {"model_name": model_name, "message": "Seguro eres carlos"}

#query parameters

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]

@app.get("/items/{item_id}")
async def read_user_item(
    item_id: str, needy: str, skip: int = 0, limit: int | None = None
):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item

#Body
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    discount: float | None = None
    
@app.post("/items/")
async def create_item(item: Item):
    return item
