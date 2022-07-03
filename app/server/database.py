import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from operator import itemgetter

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
        """
        Function searching for highest "card_number" value in collection and returns incremented value.
        """
        card_number = 1

        reader_list = self.readers_collection.find()

        for element in reader_list:
            if element["card_number"] > card_number:
                card_number = element["card_number"]

        return card_number + 1

    def get_values_and_days_to_statistics_chart(self, start_date, end_date):
        """
        Returns days and values of book borrowing.
        You can pass start date and end date as parameter to select date range.
        """
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

    def get_readers_and_amount_of_books_to_statistics_chart(self):
        """
        Returns names of readers and amount of borrowed books as dictionary.
        """
        reader_name = []
        amount_of_borrowed_books = []

        temp_reader_list = list(self.readers_collection.find({'book_borrowing_counter': {"$gt": 0}}))
        reader_list = sorted(temp_reader_list, reverse=True, key=itemgetter('book_borrowing_counter'))

        for reader in reader_list[:5]:
            full_name = f"{reader['reader_first_name']} {reader['reader_second_name']}"
            reader_name.append(full_name)
            amount_of_borrowed_books.append(reader['book_borrowing_counter'])
        return {'reader_name': reader_name,
                'amount_of_borrowed_books': amount_of_borrowed_books}

    def get_most_frequently_borrowed_books(self):
        """
        Returns books titles and amount of books borrowing as dictionary.
        """
        book_titles = []
        amount = []

        temp_book_list = list(self.books_collection.find({'book_borrowing_counter': {"$gt": 0}}))
        book_list = sorted(temp_book_list, reverse=True, key=itemgetter('book_borrowing_counter'))

        for book in book_list[:6]:
            if len(book['title']) > 20:
                splitted_book_name = book['title'].split()
                book_titles.append(splitted_book_name)
            else:
                book_titles.append(book['title'])

            amount.append(book['book_borrowing_counter'])

        return {
                'book_titles': book_titles,
                'amount': amount,
        }

    def get_percent_of_finished_book_borrowings(self):
        """
        Returns number of finished and unfinished book borrowing.
        """
        unfinished_borrowing_book_amount = self.borrowing_books_collection.count_documents({'is_finished': False})
        finished_borrowing_book_amount = self.borrowing_books_collection.count_documents({'is_finished': True})

        return {
            'borrowing_books_amount_as_percentage': [unfinished_borrowing_book_amount, finished_borrowing_book_amount]
        }

    def export_collection_as_json(self, collection_name):
        """
        Export collection as json file.
        You have to pass collection name as parameter.

        """

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
        """
        Import given collection JSON file to database.
        The function completes the missing documents in selected collection.
        """
        json_data = json.load(file.file)

        for jsonObj in json_data:
            temp_id = jsonObj['_id']['$oid']
            jsonObj['_id'] = ObjectId(temp_id)

            match collection_name:

                case "borrowing_books":
                    borrowing_date_start_ts = jsonObj['borrowing_date_start']['$date']
                    borrowing_date_start_ts_date = datetime.strptime(borrowing_date_start_ts, "%Y-%m-%dT%H:%M:%SZ")
                    jsonObj['borrowing_date_start'] = borrowing_date_start_ts_date

                    if jsonObj['borrowing_date_end'] is not None:
                        borrowing_date_end_ts = jsonObj['borrowing_date_end']['$date']
                        borrowing_date_end_ts_date = datetime.strptime(borrowing_date_end_ts, "%Y-%m-%dT%H:%M:%SZ")
                        jsonObj['borrowing_date_end'] = borrowing_date_end_ts_date

                    collection = self.borrowing_books_collection

                case "readers":
                    born_date_start_ts = jsonObj['born_date']['$date']
                    borrowing_date_end_ts_date = datetime.strptime(born_date_start_ts, "%Y-%m-%dT%H:%M:%SZ")
                    jsonObj['born_date'] = borrowing_date_end_ts_date
                    collection = self.readers_collection

                case "books":
                    collection = self.books_collection

            try:
                collection.insert_many(json_data, ordered=False)
            except BulkWriteError:
                print("Uzupełniono bazę danych pomijając duplikaty")
