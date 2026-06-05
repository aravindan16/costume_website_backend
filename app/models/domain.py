from pydantic import BaseModel, Field
from typing import List

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: int = Field(gt=0)
    color: str
    stock: int = Field(ge=0)
    image: str = "/nilla-sarres-hero.png"
    images: List[str] = []
    description: str

class Customer(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    address: str = Field(min_length=5)

class OrderItem(BaseModel):
    id: str
    name: str
    price: int = Field(gt=0)
    quantity: int = Field(gt=0)

class Order(BaseModel):
    customer: Customer
    items: List[OrderItem]
    total: int = Field(gt=0)
