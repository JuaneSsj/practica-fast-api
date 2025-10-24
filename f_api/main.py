from fastapi import FastAPI
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
import os
import django
from fastapi import HTTPException

# --- CONFIGURACIÓN DE DJANGO ---
# Es crucial que esto se ejecute antes de importar los modelos
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

# --- IMPORTACIONES DE DJANGO (después de django.setup()) ---
from store.models import Item as DjangoItem # Usamos un alias para evitar conflictos de nombres


app = FastAPI()

# ---------- RUTAS BÁSICAS ----------
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/item/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# ---------- ENUM ----------
class ModelName(str, Enum):
    juanes = "Juanes"
    camila = "Camila"
    carlos = "Carlos"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.juanes:
        return {"model_name": model_name, "message": "Llamaste a Juanes"}

    if model_name.value == "Camila":
        return {"model_name": model_name, "message": "Camila está disponible"}

    return {"model_name": model_name, "message": "Seguro eres Carlos"}

# ---------- QUERY PARAMETERS ----------
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip + limit]

@app.get("/items/{item_id}")
async def read_user_item(item_id: str, needy: str, skip: int = 0, limit: Optional[int] = None):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item

class ItemSchemaIn(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: float 

#como se verrá en la respuesta get 
class ItemSchemaOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tax: float

    # Esto le dice a Pydantic que puede leer los datos desde un objeto de modelo ORM
    class Config:
        orm_mode = True


# ---------- RUTAS CRUD PARA INTERACTUAR CON LA BASE DE DATOS ----------

# ---- CREATE ----
@app.post("/store/", response_model=ItemSchemaOut, status_code=201)
def create_item(item: ItemSchemaIn):
    new_item = DjangoItem.objects.create(
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax
    )
    return new_item

# ---- READ (List) ----
@app.get("/store/", response_model=List[ItemSchemaOut])
def read_all_items():
    items = DjangoItem.objects.all()
    return list(items)

# ---- READ (Single Item) ----
@app.get("/store/{item_id}", response_model=ItemSchemaOut)#response model para que devuelva la estrutura que quiero
def read_single_item(item_id: int):    
    try:
        item = DjangoItem.objects.get(pk=item_id)
        return item
    except DjangoItem.DoesNotExist:
        raise HTTPException(status_code=404, detail="Item not found")
    
@app.get("/suma_store/")
def suma_store():
    total = sum(i.price for i in DjangoItem.objects.all())
    return {"total_price": total}
