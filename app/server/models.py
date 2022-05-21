from datetime import  datetime
from fastapi import Depends
from pydantic import BaseModel, EmailStr, Field
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse, Response

class Admin(BaseModel):
    username: str


class Reader(BaseModel):
    first_name: str = Field(...)
    second_name: str = Field(...)
    born: datetime = None
    card_number = int = Field(default=1)

    class Config:
        schema_extra = {
            "example": {
                "first_name": "Jan",
                "second_name": "Kowalski",
                "born": "1990-04-23T10:20:30.400+02:30",
                "card_number": 1,
            }
        }



