import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from bson.json_util import dumps
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

current_file = Path(__file__)
current_file_dir = current_file.parent
project_root = current_file_dir.parent
project_root_absolute = project_root.resolve()
db_import_export_root_absolute = project_root_absolute / "db_import_export"


class DatabaseManager:
    client = MongoClient(
        'mongodb+srv://Bartek1995:{}@libary-app.1jnj8ab.mongodb.net/?retryWrites=true&w=majority'.format(
            os.environ.get('DBPASSWORD')))
    libary_db = client['libary']

    books_collection = libary_db['books']
    readers_collection = libary_db['readers']
    borrowing_books_collection = libary_db['borrowing_books']
    administrators_collection = libary_db['administrators']

    def is_book_duplicate(self, title, author_first_name, author_second_name, publish_year):

        if self.books_collection.count_documents({
            'title': title,
            'author_first_name': author_first_name,
            'author_second_name': author_second_name,
            'publish_year': publish_year}, limit=1):
            return True

        else:
            return False

    def get_book_by_id(self, id):
        book = self.books_collection.find_one({'_id': ObjectId(id)})

        return book

    def get_reader_by_id(self, id):
        reader = self.readers_collection.find_one({'_id': ObjectId(id)})
        reader['born_date'] = reader['born_date'].date()

        return reader

    def modify_data_fields_in_collection(self, existing_collection):
        """
        Transform format from datetime to date in all datatime fields in passed collection.\n 
        You have to pass existing object of database collection as argument.
        """

        if existing_collection is not None:
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
            if kwargs[element] is not None:
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
            amount_of_borrowed_books = self.borrowing_books_collection.count_documents({"borrowing_date_start": day})
            values.append(amount_of_borrowed_books)
            days.append(str(day.date()))

        return {'values': values,
                'days': days}

    def export_collection_as_json(self, collection_name):

        print(collection_name)

        match collection_name:
            case 'borrowing_book_collection':
                collection = self.borrowing_books_collection

            case 'readers_collection':
                collection = self.readers_collection

            case 'books_collection':
                collection = self.books_collection

            case 'all':
                all_collections = {
                    'borrowing_book_collection': self.borrowing_books_collection,
                    'readers_collection': self.readers_collection,
                    'books_collection': self.books_collection
                }

        if collection_name != 'all':

            cursor = collection.find({})
            data = list(cursor)

            json_data = dumps(data)

            with open('{}/{}.json'.format(db_import_export_root_absolute, collection_name), 'w', ) as file:
                file.write(json_data)
        else:

            for collection_name in all_collections:
                cursor = all_collections[collection_name].find({})

                data = list(cursor)
                json_data = dumps(data)
                with open('{}/{}.json'.format(db_import_export_root_absolute, collection_name), 'w', ) as file:
                    file.write(json_data)

    def import_collection(self, file, collection_name):

        json_data = json.load(file.file)

        for jsonObj in json_data:
            temp_id = jsonObj['_id']['$oid']
            jsonObj['_id'] = ObjectId(temp_id)

            match collection_name:

                case "borrowing_books":
                    subtract_hours = timedelta(hours=2)
                    borrowing_date_start_ts = jsonObj['borrowing_date_start']['$date']
                    borrowing_date_start_dt_object = datetime.fromtimestamp(borrowing_date_start_ts / 1000)
                    jsonObj['borrowing_date_start'] = borrowing_date_start_dt_object - subtract_hours

                    if jsonObj['borrowing_date_end'] is not None:
                        borrowing_date_end_ts = jsonObj['borrowing_date_end']['$date']
                        borrowing_date_end_dt_object = datetime.fromtimestamp(borrowing_date_end_ts / 1000)
                        jsonObj['borrowing_date_end'] = borrowing_date_end_dt_object - subtract_hours

                    collection = self.borrowing_books_collection

                case "readers":
                    subtract_hours = timedelta(hours=2)
                    born_date_start_ts = jsonObj['born_date']['$date']
                    born_date_start_dt_object = datetime.fromtimestamp(born_date_start_ts / 1000)
                    jsonObj['born_date'] = born_date_start_dt_object - subtract_hours
                    collection = self.readers_collection

                case "books":
                    collection = self.books_collection

            try:
                collection.insert_many(json_data, ordered=False)
            except BulkWriteError:
                print("Uzupełniono bazę danych pomijając duplikaty")
