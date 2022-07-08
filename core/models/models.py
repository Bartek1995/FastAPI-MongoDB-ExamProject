from datetime import datetime

from pydantic import BaseModel, Field


class Admin(BaseModel):
    username: str


class Reader(BaseModel):
    reader_first_name: str = Field(...)
    reader_second_name: str = Field(...)
    born_date: datetime = None
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


class Book(BaseModel):
    title: str = Field(...)
    publish_year: int = Field(...)
    author_first_name: str = Field(...)
    author_second_name: str = Field(...)
    publishing_house: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "name": "Jan",
                "publish_year": "Kowalski",
                "description": "Świetna powieść fantastyczna",
                "book_genre": "Fantasy",
            }
        }
