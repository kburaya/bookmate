from pymongo import MongoClient
import xml.etree.ElementTree as ET
import re


BOOKMATE_DB = 'bookmate_1'


def connect_to_database_books_collection(db):
    client = MongoClient('localhost', 27017)
    return client[db]


def get_tag(item):
    # Some magic with xml tags
    return re.sub('{[^>]+}', '', item)


def define_sections(book_id, book_file):
    db = connect_to_database_books_collection(BOOKMATE_DB)
    root = ET.ElementTree(book_file).getroot()
    _id = 1
    symbol_from = 0

    for item in root.iter():
        if get_tag(item.tag) == 'section':
            section = dict()
            section['_id'] = _id
            section['text'] = ''
            section['symbol_from'] = symbol_from
            for section_item in item.iter():
                if type(section_item.text) is str and len(section_item.text.strip(' \t\n\r')) > 0 :
                    section['text'] += section_item.text.strip(' \t\n\r') + '\n'
                    # section['text'] += section_item.text + '\n'
            section['symbol_to'] = symbol_from + len(section['text'])
            section['size'] = len(section['text'])
            db['%s_sections' % book_id].insert(section)
            _id += 1
            symbol_from = symbol_from + section['size'] + 1

    book_size = get_book_size(book_id)
    sections = db['%s_sections' % book_id].find().sort('symbol_from')
    for section in sections:
        percent_from = section['symbol_from'] / book_size * 100
        percent_to = section['symbol_to'] / book_size * 100
        db['%s_sections' % book_id].update({'_id': section['_id']},
                                           {'$set': {
                                               'percent_from': percent_from,
                                               'percent_to': percent_to
                                           }})


def get_book_size(book_id):
    db = connect_to_database_books_collection(BOOKMATE_DB)
    sections = db['%s_sections' % book_id].find()
    size = 0
    for section in sections:
        size += section['size']
    print (size)
    return size


def process_documents(book_id):
    db = connect_to_database_books_collection(BOOKMATE_DB)
    documents = db['%s_items' % book_id].find().distinct('document_id')

    for document_id in documents:
        document_items = db['%s_items' % book_id].find({'document_id': document_id}).sort('position')
        document_json = {}
        document_json['_id'] = str(document_id)
        document_file_size = 0
        for item in document_items:
            document_file_size += item['media_file_size']
            del item['_id']
            document_json[str(item['position'])] = item

        document_items = db['%s_items' % book_id].find({'document_id': document_id}).sort('position')
        summary_size = 0
        for item in document_items:
            document_json[str(item['position'])]['percent_from'] = summary_size / document_file_size * 100
            summary_size += item['media_file_size']
            document_json[str(item['position'])]['percent_to'] = summary_size / document_file_size * 100

        db['%s_documents' % book_id].insert(document_json)


def find_popular_documents(book_id):
    db = connect_to_database_books_collection(BOOKMATE_DB)
    documents = db[book_id].find().distinct('document_id')

    docs_num = {}
    for document_id in documents:
        docs_num[str(document_id)] = db[book_id].find({'document_id': document_id}).count()

    sorted_dict = [(k, docs_num[k]) for k in sorted(docs_num, key=docs_num.get, reverse=True)]
    print (sorted_dict[:10])


def find_active_readers(book_id):
    db = connect_to_database_books_collection(BOOKMATE_DB)
    users = db[book_id].find().distinct('user_id')

    readings_num = {}
    for user_id in readings_num:
        readings_num[user_id] = db[book_id].find({'user_id': user_id}).count()

    sorted_dict = [(k, readings_num[k]) for k in sorted(readings_num, key=readings_num, reverse=True)]
    readers = []
    for reader in sorted_dict:
        readers.append(reader[0])
    if len(readers) > 100:
        return readers[:100]
    else:
        return readers

def process_book(book_id):
    books_folder = '/Users/kseniya/Documents/WORK/bookmate/code/resources/in'
    book_file = '%s/%s.fb2' % (books_folder, book_id)
    book_xml = ET.XML(open(book_file, 'r').read())

    # define_sections(book_id, book_xml)
    process_documents(book_id)
    # find_popular_documents(book_id)


book_id = '2289'
# process_book(book_id)
get_book_size(book_id)



