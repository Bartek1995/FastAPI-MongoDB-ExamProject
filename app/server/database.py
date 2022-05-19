from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')

#select DB
libary_db = client['libary']

#select collections
books_collection = libary_db['books']
readers_collection = libary_db['readers']
administrators_collection = libary_db['administrators']
borrowing_books_collection = libary_db['borrowing_books']

