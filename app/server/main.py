from datetime import date
from datetime import datetime as datetime_func
from typing import Optional
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from auth import AuthHandler
from database import *
from models import Book, Reader
from schemas import AuthDetails

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
    temp_time = datetime_func.min.time()

    return datetime_func.combine(temp_date, temp_time)


@app.post('/register', status_code=201)
def register(auth_details: AuthDetails):
    if database_manager.administrators_collection.find_one({'username': auth_details.username}) is not None:
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
    context = {
        "request": request
    }
    # SEARCH USER IN DATABASE
    user = database_manager.administrators_collection.find_one(
        {'username': username})

    if (user is None) or (not auth_handler.verify_password(password, user['password'])):
        context['login_error'] = "Nieprawidłowe dane do logowania"
        # raise HTTPException(
        # status_code=404, detail="Nieprawidłowe dane do logowania")
        return templates.TemplateResponse("index.html", context)
    else:
        response = RedirectResponse(url="/dashboard")
        response.status_code = 302
        auth_handler.encode_token(user['username'])
        return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    context = {
        "request": request,
        "books_in_database": database_manager.books_collection.count_documents({}),
        "readers_in_database": database_manager.readers_collection.count_documents({}),
        "borrowing_books_in_database": database_manager.borrowing_books_collection.count_documents({}),
    }

    return templates.TemplateResponse("dashboard.html", context)


@app.get("/dashboard/new_reader", response_class=HTMLResponse)
def new_reader(request: Request):
    return templates.TemplateResponse("new_reader.html", {"request": request})


@app.get("/dashboard/reader_list", response_class=HTMLResponse)
def reader_list(request: Request):
    reader_list = database_manager.readers_collection.find()
    # print(reader_list.__collname)
    print(reader_list.collection['name'])

    reader_list = database_manager.modify_data_fields_in_collection(reader_list)

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

    reader_list = database_manager.modify_data_fields_in_collection(
        reader_list)
    context = {
        "request": request,
        "reader_list": reader_list,
    }

    return templates.TemplateResponse("reader_list.html", context)


@app.post('/dashboard/new_reader', response_class=HTMLResponse)
def new_reader(
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
            'card_number': database_manager.generate_card_number(),
        }
    )
    context['new_reader_confirmation'] = "Utworzono nowego czytelnika"

    return templates.TemplateResponse("new_reader.html", context)


@app.get("/dashboard/edit_reader/{id}", response_class=HTMLResponse)
def edit_reader(id: str, request: Request):
    reader = database_manager.get_reader_by_id(id)
    return templates.TemplateResponse("edit_reader.html", {"request": request, "reader": reader})


@app.post("/dashboard/edit_reader/{id}", response_class=HTMLResponse)
def edit_reader(id: str,
                request: Request,
                reader_first_name: str = Form(...),
                reader_second_name: str = Form(...),
                born_date: date = Form(...)):
    reader = Reader(
        reader_first_name=reader_first_name,
        reader_second_name=reader_second_name,
        born_date=change_date_format(born_date))

    update_reader_data(reader, id)
    reader.born_date = reader.born_date.date()

    context = {"request": request, "reader": reader,
               'edit_reader_confirmation': "Dane czytelnika zostały zmodyfikowane"}

    return templates.TemplateResponse("edit_reader.html", context)


@app.get("/dashboard/new_book", response_class=HTMLResponse)
def new_book(request: Request):
    return templates.TemplateResponse("new_book.html", {"request": request})


@app.post('/dashboard/new_book', response_class=HTMLResponse)
def new_book(request: Request,
             title: str = Form(...),
             publish_year: int = Form(..., min=0, max=2023),
             author_first_name: str = Form(...),
             author_second_name: str = Form(...),
             publishing_house: str = Form(...)):
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
def delete_fish(id: str, object_type: str):
    match object_type:
        case "book":
            database_manager.books_collection.delete_one(
                {'_id': ObjectId(id)})
            response = RedirectResponse(url="/dashboard/book_list")

        case "reader":
            database_manager.readers_collection.delete_one(
                {'_id': ObjectId(id)})
            response = RedirectResponse(url="/dashboard/reader_list")

    response.status_code = 302
    return response


@app.post("/dashboard/edit_book/{id}", response_class=HTMLResponse)
def update_book(id: str,
                request: Request,
                title: str = Form(...),
                publish_year: int = Form(..., min=0, max=2023),
                author_first_name: str = Form(...),
                author_second_name: str = Form(...),
                publishing_house: str = Form(...)):
    book = Book(title=title,
                publish_year=publish_year,
                author_first_name=author_first_name,
                author_second_name=author_second_name,
                publishing_house=publishing_house)

    context = {
        "request": request,
        "book": book,
    }

    update_book_data(book, id)
    context['edit_book_confirmation'] = "Dane książki zostały zmodyfikowane"

    return templates.TemplateResponse("edit_book.html", context)


@app.get("/dashboard/new_book_borrowing", response_class=HTMLResponse)
def new_book_borrowing(request: Request):
    reader_list = database_manager.readers_collection.find()
    book_list = database_manager.books_collection.find()

    context = {
        "request": request,
        "reader_list": reader_list,
        "book_list": book_list,
    }

    return templates.TemplateResponse("new_book_borrowing.html", context)


@app.get("/dashboard/borrowing_book_list", response_class=HTMLResponse)
def borrowing_book_list(request: Request):
    borrowing_book_list = database_manager.borrowing_books_collection.find()

    borrowing_book_list = database_manager.modify_data_fields_in_collection(borrowing_book_list)

    context = {
        "request": request,
        "borrowing_book_list": borrowing_book_list,
    }

    return templates.TemplateResponse("borrowing_book_list.html", context)


@app.post("/dashboard/borrowing_book_list", response_class=HTMLResponse)
def borrowing_book_list(request: Request,
                        reader_full_name: Optional[str] = Form(None),
                        card_number: Optional[int] = Form(None),
                        book_title: Optional[str] = Form(None),
                        borrowing_date_start: Optional[date] = Form(None),
                        borrowing_date_end: Optional[date] = Form(None),
                        is_finished: Optional[bool] = Form(None),
                        modified_borrowing_date_end: Optional[date] = Form(None),
                        borrowing_book_id: Optional[str] = Form(None)):
    if modified_borrowing_date_end:
        modified_borrowing_date_end = change_date_format(modified_borrowing_date_end)

        database_manager.borrowing_books_collection.update_one(
            {'_id': ObjectId(borrowing_book_id)},
            {"$set":
                {
                    'borrowing_date_end': modified_borrowing_date_end,
                    'is_finished': True,
                }})

    if borrowing_date_start is not None:
        borrowing_date_start = change_date_format(borrowing_date_start)
    elif borrowing_date_end is not None:
        borrowing_date_end = change_date_format(borrowing_date_end)

    borrowing_book_list = database_manager.get_database_collection_by_arguments(
        "borrowing_books",
        reader_full_name=reader_full_name,
        card_number=card_number,
        book_title=book_title,
        borrowing_date_start=borrowing_date_start,
        borrowing_date_end=borrowing_date_end,
        is_finished=is_finished
    )

    borrowing_book_list = database_manager.modify_data_fields_in_collection(borrowing_book_list)

    context = {
        "request": request,
        "borrowing_book_list": borrowing_book_list,
    }

    return templates.TemplateResponse("borrowing_book_list.html", context)


@app.post('/dashboard/new_book_borrowing', response_class=HTMLResponse)
def new_book_borrowing(request: Request,
                       reader_id: str = Form(...),
                       book_id: str = Form(...),
                       borrowing_date_start: date = Form(...),
                       borrowing_date_end: Optional[date] = Form(None),
                       ):
    reader_list = database_manager.readers_collection.find()
    book_list = database_manager.books_collection.find()

    context = {
        "request": request,
        "reader_list": reader_list,
        "book_list": book_list,
    }

    is_finished = False

    if borrowing_date_end is not None:
        if borrowing_date_end < borrowing_date_start:
            context['new_borrowing_error'] = "Błędnie wprowadzona data, data oddania powinna być po dacie wypożyczenia"

            return templates.TemplateResponse("new_book_borrowing.html", context)
        else:
            is_finished = True
            borrowing_date_end = change_date_format(borrowing_date_end)

    book = database_manager.get_book_by_id(book_id)
    reader = database_manager.readers_collection.find_one(
        {'_id': ObjectId(reader_id)})
    borrowing_date_start = change_date_format(borrowing_date_start)
    database_manager.borrowing_books_collection.insert_one(
        {'reader_id': reader_id,
         'card_number': reader["card_number"],
         'book_id': book_id,
         'book_title': book['title'],
         'reader_full_name': "{} {}".format(reader['reader_first_name'], reader['reader_second_name']),
         'borrowing_date_start': borrowing_date_start,
         'borrowing_date_end': borrowing_date_end,
         'is_finished': is_finished
         }
    )
    context['new_borrowing_confirmation'] = "Dodano wpis o wypożyczeniu"

    return templates.TemplateResponse("new_book_borrowing.html", context)


@app.get("/dashboard/statistics", response_class=HTMLResponse)
def statistics(request: Request):
    today = date.today()
    modified_days = timedelta(10)

    start_date = today - modified_days

    context = {
        "request": request,
    }

    context.update(database_manager.get_values_and_days_to_statistics_chart(start_date, today))

    return templates.TemplateResponse("statistics.html", context)


@app.post("/dashboard/statistics", response_class=HTMLResponse)
def statistics(request: Request,
               borrowing_date_start: Optional[date] = Form(None),
               borrowing_date_end: Optional[date] = Form(None)):
    context = {
        "request": request,
    }

    if borrowing_date_end < borrowing_date_start:
        context['date_error'] = "Nieprawidłowo wprowadzona data, popraw datę aby wyświetlić wykres głowny"

    context.update(database_manager.get_values_and_days_to_statistics_chart(borrowing_date_start, borrowing_date_end))

    return templates.TemplateResponse("statistics.html", context)


@app.get("/dashboard/db_import_export", response_class=HTMLResponse)
def db_import_export(request: Request):
    context = {
        "request": request,
    }

    return templates.TemplateResponse("db_import_export.html", context)


@app.post("/dashboard/db_import_export", response_class=HTMLResponse)
def db_import_export(request: Request,
                     collection_select: Optional[str] = Form(None),
                     borrowing_book_collection: Optional[UploadFile] = Form(None),
                     book_collection: Optional[UploadFile] = Form(None),
                     readers_collection: Optional[UploadFile] = Form(None),
                     type_of_action: Optional[str] = Form(None),
                     db_password_input: Optional[str] = Form(None)):
    context = {
        "request": request,
    }

    borrowing_book_collection_json_file_is_valid = None
    books_collection_json_file_is_valid = None
    readers_collection_json_file_is_valid = None
    password_valid = False

    match type_of_action:

        case "export":
            database_manager.export_collection_as_json(collection_select)
            context['export_success'] = "Pomyślnie eksportowano wybrane kolekcje"

        case "import":

            if str(db_password_input) == str(os.environ.get('DBPASSWORD')):
                password_valid = True

            if borrowing_book_collection.filename != "":
                if borrowing_book_collection.filename == "borrowing_book_collection.json":
                    borrowing_book_collection_json_file_is_valid = True
                    database_manager.import_collection(borrowing_book_collection, "borrowing_books")
                else:
                    borrowing_book_collection_json_file_is_valid = False

            elif readers_collection.filename != "":
                if readers_collection.filename == "readers_collection.json":
                    readers_collection_json_file_is_valid = True
                    database_manager.import_collection(readers_collection, "readers")
                else:
                    readers_collection_json_file_is_valid = False

            elif book_collection.filename != "":
                if book_collection.filename == "books_collection.json":
                    books_collection_json_file_is_valid = True
                    database_manager.import_collection(book_collection, "books")
                else:
                    books_collection_json_file_is_valid = False

            if (borrowing_book_collection_json_file_is_valid is not True or None) and (
                    books_collection_json_file_is_valid is not True or None) and (
                    readers_collection_json_file_is_valid is not True or None) and password_valid:
                context['import_error'] = "Błąd ładowania plików, sprawdź poprawność załadowanych plików."
            else:
                if password_valid:
                    context[
                        'import_success'] = "Pliki JSON zostały wczytane do bazy danych. Baza została uzupełniona o różnice."
                else:
                    context['password_error'] = "Nieprawidłowe hasło do bazy danych"

    return templates.TemplateResponse("db_import_export.html", context)


@app.put("/update_book", status_code=202)
def update_book_data(book: Book, id: str):
    database_manager.books_collection.update_one(
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


@app.put("/update_reader", status_code=202)
def update_reader_data(reader: Reader, id: str):
    database_manager.readers_collection.update_one(
        {'_id': ObjectId(id)},
        {"$set":
            {
                'reader_first_name': reader.reader_first_name,
                'reader_second_name': reader.reader_second_name,
                'born_date': reader.born_date,
            }
        }
    )
