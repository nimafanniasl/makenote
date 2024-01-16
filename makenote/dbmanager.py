import sys
import os
import sqlite3
import datetime
import argparse
import shutil
import jdatetime
import json

# read config file
# TODO: try to read config from another local dir first. then go to default file


def get_date_string(date_and_time:datetime.datetime = None, show_jalali:bool = True):

    if date_and_time is None:
        date_and_time = jdatetime.datetime.now()

    if show_jalali == True:
        date_and_time = jdatetime.datetime.fromtimestamp(date_and_time.timestamp())
        jd = date_and_time.strftime("%a, %d %b %Y %H:%M:%S")
        return f"{jd}"
    else:
        return date_and_time.ctime()

def print_message(message_type:str, message:list, show_style:int=2):
    if message_type == "add note":
        table_name = message[0]
        note_id = message[1]
        note_text = message[2]
        if show_style == 1:
            print(f'{get_date_string()} - {table_name} - note saved!')
        elif show_style == 2:
            print(f'\u001b[36m{note_id} - {get_date_string()}\u001b[0m - {table_name} - note saved!')


def add_note(sqlite_cursor, table_name, note_text, note_number:int = 0, note_category:int = 0, note_metadata:dict={}):
    
    date_and_time = datetime.datetime.now()
    note_metadata_encoded = json.dumps(note_metadata)
    sqlite_cursor.execute(
        f"INSERT INTO {table_name} VALUES (?, ?, ?, ?)", (date_and_time, note_text, note_number, note_category, note_metadata))
    note_id = sqlite_cursor.execute(f"select max(rowid) from {table_name}").fetchall()[0][0]

    # let user know it works
    print_message("add note", [table_name, note_id, note_text])


def update_entry(sqlite_cursor, table_name, note_id: int, note_text: str) -> None:
    try:
        if note_id == -1:
            sqlite_cursor.execute(f"SELECT rowid FROM {table_name} order by rowid DESC LIMIT 1;")
            note_id = sqlite_cursor.fetchone()[0]

        # get the record from sqlite
        sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {note_id - 1}, 1;")
        record = sqlite_cursor.fetchone()
        
        print(f"entry {note_id} with text \"{record[1]}\" updated")
        sqlite_cursor.execute(f"""UPDATE {table_name} SET note = "{note_text}" LIMIT {note_id-1},{1};""")

    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)

def get_note(sqlite_cursor, table_name, note_id: int):
    try:
        if note_id is None:
            return ('', '')
        elif note_id == -1:
            # get the record from sqlite
            sqlite_cursor.execute(f"SELECT * FROM {table_name} order by rowid DESC LIMIT 1;")
        else:
            sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {note_id - 1}, 1;")
        record = sqlite_cursor.fetchone()
        if record[1] is None:
            print('**there is an Error in database. text is None.**')
            return (record[0], '')
        return record
    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)

def tail_show_table(sqlite_cursor, table_name, limit, show_style:int = 2):
    try:
        # get records from sqlite
        sqlite_cursor.execute(f"SELECT count(*) FROM {table_name}")
        N = sqlite_cursor.fetchone()[0]
        records = sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {N - limit}, {limit};")
        # print them all
        i = N - limit 
        for r in records:
            i += 1
            print(i, end="  ")

            # if style number 1 is selected
            if show_style == 1:
                # replace that utf representation of نیم‌فاصله with itself
                r[1].replace('\u200c', ' ')
                # remove miliseconds from date and time and print a in a stylized format
                print(f'{get_date_string_from_string(r[0])}    {r[1]}')
            
            elif show_style == 2:
                print(f'\u001b[36m{get_date_string_from_string(r[0])}\u001b[0m  {r[1]}')

            # if no show style is specified
            else:
                # print in python default style of printing
                print(r)
    # if there was an error, print error text and exit
    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)

def get_date_string_from_string(date_and_time:str):
    date_and_time = datetime.datetime.fromisoformat(date_and_time)
    return get_date_string(date_and_time)

def show_table(sqlite_cursor, table_name, show_style:int = 2):
    try:
        # get records from sqlite
        records = sqlite_cursor.execute(f"SELECT * FROM {table_name};")
        # print them all
        i = 0
        for r in records:
            i += 1
            print(i, end="  ")

            # if style number 1 is selected
            if show_style == 1:
                # replace that utf representation of نیم‌فاصله with itself
                r[1].replace('\u200c', ' ')
                # remove miliseconds from date and time and print a in a stylized format
                print(f'{r[0][:10]}   {r[0][10:18]}    {r[1]}')
            
            elif show_style == 2:
                print(f'\u001b[36m{r[0][:10]} {r[0][10:18]}\u001b[0m  {r[1]}')

            # if no show style is specified
            else:
                # print in python default style of printing
                print(r)
    # if there was an error, print error text and exit
    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)

def table_exists(sqlite_cursor: sqlite3.Cursor, table_name) -> bool:
    query = 'SELECT name from sqlite_master where type= "table"'
    # query = f"SELECT tableName FROM sqlite_master WHERE type='table' AND tableName='{table_name}';"
    records = sqlite_cursor.execute(query)
    # print([t for t in tables])
    tables = [record[0] for record in records]
    return table_name in tables


def make_table(sqlite_cursor: sqlite3.Cursor, table_name):
    try:
        # create the table!
        sqlite_cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                    (date datetime, note text)''')
        # tell the user it was successful
        print(f'table {table_name} created!')
    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)

def list_tables(sqlite_cursor: sqlite3.Cursor):
    try:
        # get list of tables
        records = sqlite_cursor.execute(
            'SELECT name from sqlite_master where type= "table"')
        # print them
        for r in records:
            print(r[0])
    # if there was an error, print error text and exit
    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)

def export_database_json(sqlite_cursor: sqlite3.Cursor, output_filename:str):
    try:
        # get list of tables
        records = sqlite_cursor.execute(
            'SELECT name from sqlite_master where type= "table"')
        # print them
        tables = [r[0] for r in records]
        import json
        all_data = {}
        for table in tables:
            table_data = sqlite_cursor.execute(f"select * from {table};").fetchall()
            all_data[table] = table_data
        
        print(json.dumps(all_data, ensure_ascii=False))



    # if there was an error, print error text and exit
    except sqlite3.OperationalError as error_text:
        print(error_text)
        exit(1)


def merge_databases(cursor1:sqlite3.Cursor, cursor2:sqlite3.Cursor, cursor_out:sqlite3.Cursor):

    def add_table(cursor_in, cursor_out, table_name):
        cursor_out.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (date datetime, note text)''')
        table_data = cursor_in.execute(f"select * from {table_name};").fetchall()

        for entry in table_data:
            cursor_out.execute(f"INSERT INTO {table_name} VALUES (?, ?)", (entry[0], entry[1]))
  

    def merge_tables(cursor1:sqlite3.Cursor, cursor2:sqlite3.Cursor, cursor_out:sqlite3.Cursor, table_name):


        table_1 = cursor1.execute(f"select * from {table_name};").fetchall()
        table_2 = cursor2.execute(f"select * from {table_name};").fetchall()

        table_out = []
        last_index_table2 = 0
        for entry_1 in table_1:
            for entry_2 in table_2[last_index_table2:]:
                # print(x[0], y[0], x[0] > y[0])
                if entry_1[0] > entry_2[0]:
                    table_out.append(entry_2)
                    # print(i)
                    last_index_table2 += 1
                else:
                    break
            table_out.append(entry_1)
        for entry_2 in table_2[last_index_table2:]:
            table_out.append(entry_2)


        cursor_out.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (date datetime, note text)''')
        for entry in table_out:
            cursor_out.execute(f"INSERT INTO {table_name} VALUES (?, ?)", (entry[0], entry[1]))
    

    tables_1 = cursor1.execute('SELECT name from sqlite_master where type= "table"').fetchall()
    tables_2 = cursor2.execute('SELECT name from sqlite_master where type= "table"').fetchall()
    for table_name in tables_1:
        if table_name in tables_2:
            merge_tables(cursor1, cursor2, cursor_out, table_name[0])
        else:
            add_table(cursor1, cursor_out, table_name[0])
    
    for table_name in tables_2:
        if table_name not in tables_1:
            add_table(cursor2, cursor_out, table_name[0])

def sql_to_csv(sqlite_cursor: sqlite3.Cursor):
    records = sqlite_cursor.execute(
        'SELECT name from sqlite_master where type= "table"')
    # print them
    tables = [r[0] for r in records]
    

def merge_databases_by_name(firstdb_filename:str, seconddb_filename:str, outdb_filename:str):

    con1 = sqlite3.connect(firstdb_filename)
    cur1 = con1.cursor()

    con2 = sqlite3.connect(seconddb_filename)
    cur2 = con2.cursor()

    con3 = sqlite3.connect(outdb_filename)
    curo = con3.cursor()

    merge_databases(cur1, cur2, curo)

    # con1.commit()
    # con1.close()

    # con2.commit()
    # con2.close()
    
    con3.commit()
    con3.close()

    print('done merging databases')


def import_database(db_filename: str, outdb_filename:str):

    merge_databases_by_name(outdb_filename, db_filename, outdb_filename)
    print('done importing your database')

