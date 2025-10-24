from fastapi import FastAPI, Path, Query, Body
from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field, HttpUrl
import os
import django
from fastapi import HTTPException
from pydantic import AfterValidator
from typing import Annotated, Literal
import random

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

"""
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip + limit]


@app.get("/items/{item_id}")
async def read_user_item(item_id: str, needy: str, skip: int = 0, limit: Optional[int] = None):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item
"""

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

# ----- Validator -----

data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}


def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
    return id

"""
@app.get("/items/")
async def read_items(
    id: Annotated[str | None, AfterValidator(check_valid_id)] = None,
):
    if id:
        item = data.get(id)
    else:
        id, item = random.choice(list(data.items()))
    return {"id": id, "name": item}
"""

@app.get("/items/{item_id}")
async def read_items(
    *,
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    q: str, #obligatorio porque no tiene valor por defecto
    size: Annotated[float, Query(gt=0, lt=10.5)],##obligatorio porque no tiene valor por defecto
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if size:
        results.update({"size": size})
    return results

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

#multiple Body 

class Item1(BaseModel): # un Body
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class User(BaseModel): #otro body
    username: str
    full_name: str | None = None


@app.put("/body/items/{item_id}")
async def update_item(
    item_id: int, item: Item1, user: User, importance: Annotated[int, Body()] #llamo a body para que no sea un parametro
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    return results

#Field 

class Item2(BaseModel):
    name: str
    description: str | None = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None


@app.put("/field/items/{item_id}")
async def update_item1(item_id: int, item: Annotated[Item2, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results

# Nested Models

class Image(BaseModel):
    url: HttpUrl
    name: str

class ItemNested(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None
    tags: set[str] = set()
    images: list[Image] | None = None


@app.put("/Nested/items/{item_id}")
async def update_item_nested(item_id: int, item: ItemNested):
    results = {"item_id": item_id, "item": item}
    return results