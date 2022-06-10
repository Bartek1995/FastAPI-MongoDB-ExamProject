from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os


class DatabaseManager:
    client = MongoClient('mongodb+srv://Bartek1995:{}@libary-app.1jnj8ab.mongodb.net/?retryWrites=true&w=majority'.format(os.environ.get('DBPASSWORD')))
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
        
    def modify_data_fields_in_collection(self, existing_collection):
        """
        Transform format from datetime to date in all datatime fields in passed collection.\n 
        You have to pass existing object of database collection as argument.
        """
        
        
        if existing_collection != None:
            existing_collection = list(existing_collection)
        
        for element in existing_collection:
            for key, value in element.items():
                if isinstance(value, datetime):
                    element[key] = element[key].date()
                                
        return existing_collection
    
    
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
            
            case "borrowing_books":
                return self.borrowing_books_collection.find(collection_of_arguments_to_search_in_db)
                
        
    def generate_card_number(self):   
        
        card_number = 1
        
        reader_list = self.readers_collection.find()
        
        for element in reader_list:
            if element["card_number"] > card_number:
                card_number = element["card_number"]
                
        return card_number + 1     
    
    def get_values_and_days_to_statistics_chart(self, start_date, end_date):
           
        values = []
        days = []
        
        
        date_format = "%Y-%m-%d"
        substract_date = datetime.strptime(str(start_date), date_format)
        end_date = datetime.strptime(str(end_date), date_format)
        delta = end_date - substract_date

        
        for i in range(delta.days + 1):
            
            day = substract_date + timedelta(days=i)
            from main import change_date_format
            day = change_date_format(day)
            amount_of_borrowed_books = self.borrowing_books_collection.find({"borrowing_date_start" : day}).count()
            values.append(amount_of_borrowed_books)
            days.append(str(day.date()))
            
        return {'values' : values,
                'days' : days}