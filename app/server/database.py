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
    
    def get_reader_by_id(self, id): 
        reader = self.readers_collection.find_one({'_id' : ObjectId(id)})
        reader['born_date'] = reader['born_date'].date()
        
        return reader
        
    def get_reader_list_with_modified_data_field(self, existing_reader_list=None):
        """
        Get reader list and modify with modified born_date format from datetime to date.\n 
        You can pass existing reader list as optional argument to modify that list.
        """
        reader_list = self.readers_collection.find()
        
        if existing_reader_list != None:
            reader_list = existing_reader_list
        
        reader_list = list(reader_list)
        
        for element in reader_list:
            element['born_date'] = element['born_date'].date()
            
        return reader_list
    
    
    def get_database_collection_by_arguments(self, name_of_collection, **kwargs):
        """
        Returns database cursor by given arguments in **kwargs \n
        name_of_collection - name of collection in MongoDB
        """
    
        collection_of_arguments_to_search_in_db = {}
        
        for element in kwargs:
            if kwargs[element] != None:
                collection_of_arguments_to_search_in_db[element] = kwargs[element]

        match name_of_collection:
            case "book":
                return self.books_collection.find(collection_of_arguments_to_search_in_db)
            
            case "reader":
                return self.readers_collection.find(collection_of_arguments_to_search_in_db)
                
                