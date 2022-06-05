
import uvicorn
from pathlib import Path
from datetime import date
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from auth import AuthHandler
from schemas import AuthDetails
from database import *
from models import Book
from starlette.responses import RedirectResponse


app = FastAPI()
auth_handler = AuthHandler()
database_manager = DatabaseManager()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, debug=True)

current_file = Path(__file__)
current_file_dir = current_file.parent
project_root = current_file_dir.parent
project_root_absolute = project_root.resolve()
static_root_absolute = project_root_absolute / "static"
templates_root_absolute = project_root_absolute / "templates"

# static files settings
app.mount("/static", StaticFiles(directory=static_root_absolute), name='static')
templates = Jinja2Templates(directory=templates_root_absolute)


def change_date_format(date_to_modify):
    temp_date = date_to_modify
    temp_time = datetime.min.time()
    
    return datetime.combine(temp_date, temp_time)
    
    
    

@app.post('/register', status_code=201)
def register(auth_details: AuthDetails):
    if database_manager.administrators_collection.find_one({'username': auth_details.username}) != None:
        raise HTTPException(
            status_code=400, detail='Nazwa użytkownika jest już używana')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    database_manager.administrators_collection.insert_one(
        {
            'username': auth_details.username,
            'password': hashed_password
        })
    return


@app.get("/", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post('/')
def login(request: Request, username: str = Form(...), password: str = Form(...), ):
    # SEARCH USER IN DATABASE
    user = database_manager.administrators_collection.find_one(
        {'username': username})

    if (user is None) or (not auth_handler.verify_password(password, user['password'])):
        raise HTTPException(
            status_code=404, detail="Nieprawidłowe dane do logowania")
    else:
        response = RedirectResponse(url="/main")
        response.status_code = 302
        token = auth_handler.encode_token(user['username'])
        return response

    token = auth_handler.encode_token(user['username'])
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    context = {
        "request": request,
        "books_in_database": database_manager.books_collection.find().count(),
        "readers_in_database": database_manager.readers_collection.find().count(),
        "borrowing_books_in_database": database_manager.borrowing_books_collection.find().count(),
    }

    return templates.TemplateResponse("dashboard.html", context)


@app.get("/dashboard/new_reader", response_class=HTMLResponse)
def new_book(request: Request):

    return templates.TemplateResponse("new_reader.html", {"request": request})


@app.get("/dashboard/reader_list", response_class=HTMLResponse)
def reader_list(request: Request):

    reader_list = database_manager.get_reader_list_with_modified_data_field()

    context = {
        "request": request,
        "reader_list": reader_list,
    }

    return templates.TemplateResponse("reader_list.html", context)


@app.post("/dashboard/reader_list", response_class=HTMLResponse)
def reader_list(request: Request,
              reader_first_name: Optional[str] = Form(None),
              reader_second_name: Optional[str] = Form(None),
              born_date: Optional[date] = Form(None),
              card_number: Optional[int] = Form(None)
              ):

    if born_date:
        born_date = change_date_format(born_date)
    
    reader_list = database_manager.get_database_collection_by_arguments(
        'reader',
        reader_first_name=reader_first_name,
        reader_second_name=reader_second_name,
        born_date=born_date,
        card_number=card_number)
    
    modified_reader_list = database_manager.get_reader_list_with_modified_data_field(reader_list)    
    context = {
        "request": request, 
        "reader_list": modified_reader_list,
    }

    return templates.TemplateResponse("reader_list.html", context)


@app.post('/dashboard/new_reader', response_class=HTMLResponse)
def new_book(
    request: Request,
    reader_first_name: str = Form(...),
    reader_second_name: str = Form(...),
    born_date: date = Form(...)
):

    context = {
        "request": request,
    }

    born_date = change_date_format(born_date)

    database_manager.readers_collection.insert_one(
        {
            'reader_first_name': reader_first_name,
            'reader_second_name': reader_second_name,
            'born_date': born_date,
            'card_number': database_manager.readers_collection.find().count() + 1,
        }
    )
    context['new_reader_confirmation'] = "Utworzono nowego czytelnika"

    return templates.TemplateResponse("new_reader.html", context)

@app.get("/dashboard/edit_reader/{id}", response_class=HTMLResponse)
def edit_reader(id: str, request: Request):
    reader = database_manager.get_reader_by_id(id)
    return templates.TemplateResponse("edit_reader.html", {"request": request, "reader": reader})

@app.get("/dashboard/new_book", response_class=HTMLResponse)
def new_book(request: Request):
    return templates.TemplateResponse("new_book.html", {"request": request})


@app.post('/dashboard/new_book', response_class=HTMLResponse)
def new_book(request: Request, title: str = Form(...), publish_year: int = Form(..., min=0, max=2023), author_first_name: str = Form(...), author_second_name: str = Form(...), publishing_house: str = Form(...)):

    context = {
        "request": request,
    }

    is_book_exist = database_manager.is_book_duplicate(
        title, author_first_name, author_second_name, publish_year)

    if not is_book_exist:
        database_manager.books_collection.insert_one(
            {
                'title': title,
                'author_first_name': author_first_name,
                'author_second_name': author_second_name,
                'publish_year': publish_year,
                'publishing_house': publishing_house
            }
        )
        context['new_book_confirmation'] = "Książka została dodana do bazy danych"
    else:
        context['new_book_error'] = "Książka istnieje w bazie danych"

    return templates.TemplateResponse("new_book.html", context)


@app.get("/dashboard/book_list", response_class=HTMLResponse)
def book_list(request: Request):
    book_list = database_manager.books_collection.find()

    context = {
        "request": request,
        "book_list": book_list,
    }

    return templates.TemplateResponse("book_list.html", context)


@app.post("/dashboard/book_list", response_class=HTMLResponse)
def book_list(request: Request,
              title: Optional[str] = Form(None),
              publish_year: Optional[int] = Form(None),
              author_first_name: Optional[str] = Form(None),
              author_second_name: Optional[str] = Form(None),
              publishing_house: Optional[str] = Form(None)
              ):


    book_list = database_manager.get_database_collection_by_arguments(
        'book',
        title=title,
        publish_year=publish_year,
        author_first_name=author_first_name,
        author_second_name=author_second_name,
        publishing_house=publishing_house)
    
    context = {
        "request": request, 
        "book_list": book_list,
    }

    return templates.TemplateResponse("book_list.html", context)


@app.get("/dashboard/edit_book/{id}", response_class=HTMLResponse)
def edit_book(id: str, request: Request):
    book = database_manager.get_book_by_id(id)
    return templates.TemplateResponse("edit_book.html", {"request": request, "book": book})


@app.get("/dashboard/delete_book_ask/{id}", response_class=HTMLResponse)
def delete_book(id: str, request: Request):
    book = database_manager.get_book_by_id(id)
    return templates.TemplateResponse("delete_book.html", {"request": request, "book": book})


@app.get("/dashboard/delete/{object_type}/{id}", response_class=HTMLResponse)
def delete_fish(id: str, request: Request, object_type : str):
    
    match object_type:
        case "book":
            result = database_manager.books_collection.delete_one(
        {'_id': ObjectId(id)})
            response = RedirectResponse(url="/dashboard/book_list")
            
        case "reader":
            result = database_manager.readers_collection.delete_one(
        {'_id': ObjectId(id)})
            response = RedirectResponse(url="/dashboard/reader_list")
            

    response.status_code = 302
    return response


@app.post("/dashboard/edit_book/{id}", response_class=HTMLResponse)
def update_book(id: str, request: Request, title: str = Form(...), publish_year: int = Form(..., min=0, max=2023), author_first_name: str = Form(...), author_second_name: str = Form(...), publishing_house: str = Form(...)):

    book = Book(title=title, publish_year=publish_year, author_first_name=author_first_name,
                author_second_name=author_second_name, publishing_house=publishing_house)

    context = {
        "request": request,
        "book": book,
    }

    update_book_data(book, id)

    context['edit_book_confirmation'] = "Dane książki zostały zmodyfikowane"

    return templates.TemplateResponse("edit_book.html", context)


@app.put("/update_book", status_code=202)
def update_book_data(book: Book, id: str):
    result = database_manager.books_collection.update_one(
        {'_id': ObjectId(id)},
        {"$set":
            {
                'title': book.title,
                'author_first_name': book.author_first_name,
                'author_second_name': book.author_second_name,
                'publish_year': book.publish_year,
                'publishing_house': book.publishing_house,
            }
         }
    )
