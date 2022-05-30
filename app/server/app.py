from multiprocessing import context
from turtle import pu, title
from urllib import response
from fastapi import FastAPI, HTTPException, Form, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from h11 import Data
from .forms import LoginForm
from .auth import AuthHandler
from .schemas import AuthDetails
from .database import *
from .models import Book
from starlette.responses import RedirectResponse


app = FastAPI()
auth_handler = AuthHandler()
database_manager = DatabaseManager()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#static files settings
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.post('/token')
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    return {'access_token'}







@app.post('/register', status_code = 201)
def register(auth_details: AuthDetails):
    if database_manager.administrators_collection.find_one({'username' : auth_details.username}) != None:
        raise HTTPException(status_code = 400, detail = 'Nazwa użytkownika jest już używana')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    database_manager.administrators_collection.insert_one(
        {
            'username' : auth_details.username,
            'password' : hashed_password
        })
    return


#MAIN PAGE

@app.get("/", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard/new_book", response_class=HTMLResponse)
def new_book(request: Request):
    return templates.TemplateResponse("new_book.html", {"request": request})

@app.get("/dashboard/book_list", response_class=HTMLResponse)
def book_list(request: Request):
    book_list = database_manager.books_collection.find()

    context = {
        "request" : request,
        "book_list" : book_list,
    }
    

    return templates.TemplateResponse("book_list.html", context)

@app.post('/')
def login(request: Request, username:str = Form(...), password:str = Form(...), ):
    # SEARCH USER IN DATABASE
    user = database_manager.administrators_collection.find_one({'username' : username})
    
    
    if (user is None) or (not auth_handler.verify_password(password, user['password'])):
        raise HTTPException(status_code=404, detail="Nieprawidłowe dane do logowania")
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
        "request" : request,
    }

    return templates.TemplateResponse("dashboard.html", context)


@app.post('/dashboard/new_book', response_class=HTMLResponse)
def new_book(request: Request, title:str = Form(...), publish_year:int = Form(..., min=0, max=2023), author_first_name: str = Form(...), author_second_name: str = Form(...),publishing_house: str = Form(...)):

    context = {
        "request": request,
    }

    is_book_exist = database_manager.is_book_duplicate(title,author_first_name,author_second_name, publish_year)

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


@app.get("/dashboard/edit_book/{id}",response_class=HTMLResponse)
def edit_book(id:str, request:Request):
    book = database_manager.get_book_by_id(id)
    return templates.TemplateResponse("edit_book.html", {"request": request, "book": book})


@app.post("/dashboard/edit_book/{id}",response_class=HTMLResponse)
def update_book(id:str, request:Request, title:str = Form(...), publish_year:int = Form(..., min=0, max=2023), author_first_name: str = Form(...), author_second_name: str = Form(...),publishing_house: str = Form(...)):
    
    book = Book(title=title, publish_year=publish_year, author_first_name=author_first_name, author_second_name=author_second_name, publishing_house=publishing_house)
    
    context = {
        "request": request,
        "book": book,
    }

    
    update_api_data(book, id)
    
    context['edit_book_confirmation'] = "Dane książki zostały zmodyfikowane"
    
    return templates.TemplateResponse("edit_book.html", context)
    
    
@app.put("/updateapi", status_code=202)
def update_api_data(book:Book, id:str):
    print("Data updated")
    result = database_manager.books_collection.update_one({'_id':ObjectId(id)},
                                                            {"$set" : 
                                                                {
                                                                    'title':book.title,
                                                                    'author_first_name' : book.author_first_name,
                                                                    'author_second_name' : book.author_second_name,
                                                                    'publishin_year' : book.publish_year,
                                                                    'publishing_house' : book.publishing_house,
                                                                }
                                                            }
                                                        )