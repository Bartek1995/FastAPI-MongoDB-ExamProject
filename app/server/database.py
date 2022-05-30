from pymongo import MongoClient
from bson.objectid import ObjectId


class DatabaseManager:
    client = MongoClient('mongodb://localhost:27017/')
    libary_db = client['libary']
    
    books_collection = libary_db['books']
    readers_collection = libary_db['readers']
    administrators_collection = libary_db['administrators']
    borrowing_books_collection = libary_db['borrowing_books']

    def is_book_duplicate(self, title, author_first_name, author_second_name, publish_year):
 
        if self.books_collection.count_documents({
            'title': title,
            'author_first_name': author_first_name,
            'author_second_name': author_second_name,
            'publish_year': publish_year}, limit= 1):

            return True

        else:
            return False
        
    
    def get_book_by_id(self, id): 
        book = self.books_collection.find_one({'_id' : ObjectId(id)})
        
        return book
        