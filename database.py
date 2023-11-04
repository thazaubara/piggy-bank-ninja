from datetime import datetime
from datetime import date
import mysql.connector as mariadb
from mysql.connector import Error
import credentials
import logger

connection = None

def datetime2sql(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def date2sql(dt):
    return dt.strftime('%Y-%m-%d')

def connect():
    global connection
    try:
        connection = mariadb.connect(host=credentials.DB_HOST, user=credentials.DB_USER, port=credentials.DB_PORT, password=credentials.DB_PASS)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f"use {credentials.DB_NAME};")
            print(f"DB connected: {credentials.DB_USER}@{credentials.DB_HOST}:{credentials.DB_PORT} DB:{credentials.DB_NAME}")
        else:
            print("No connection MySQL")
            exit()
    except Error as e:
        print("Error while connecting to MySQL", e)

def upload_transactions(transactions):
    global connection
    logger.highlight(f"\nUploading {len(transactions)} transactions...")
    cursor = connection.cursor()
    progress = 1
    for transaction in transactions:
        logger.log(f"[{progress}/{len(transactions)}] Uploading transaction: {transaction}")
        try:
            iban = transaction["iban"]
            buchungsdatum = date2sql(transaction["buchungsdatum"])
            referenz = transaction["referenz"]
            valuta = date2sql(transaction["valuta"])
            betrag = transaction["betrag"]
            waehrung = transaction["waehrung"]
            datum = datetime2sql(transaction["datum"])
            insert_query = f"INSERT INTO banking (iban, buchungsdatum, referenz, valuta, betrag, waehrung, datum) " \
                           f"VALUES ('{iban}', '{buchungsdatum}', '{referenz}', '{valuta}', {betrag}, '{waehrung}', '{datum}')"
            cursor.execute(insert_query)
        except mariadb.Error as error:
            logger.error(f"{error} {transaction}")
        progress += 1

    connection.commit()
    cursor.close()

def send_query(sqlquery):
    cursor = connection.cursor()
    cursor.execute(sqlquery)
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    transactions = []
    for row in result:
        row_dict = dict(zip(columns, row))
        row_dict["betrag"] = float(row_dict["betrag"])
        transactions.append(row_dict)
        logger.log(row_dict)

    logger.log(f"Found {len(transactions)} transactions.")
    return transactions

def get_max_date():
    global connection
    logger.highlight("\nGetting MAX(buchungsdatum) transactions from server for each iban")
    cursor = connection.cursor()
    cursor.execute(f"SELECT iban, buchungsdatum, referenz, valuta, betrag, waehrung, datum FROM banking WHERE (iban, buchungsdatum) IN (SELECT iban, MAX(buchungsdatum) FROM banking GROUP BY iban);")
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    transactions = []
    for row in result:
        row_dict = dict(zip(columns, row))
        row_dict["betrag"] = float(row_dict["betrag"])
        transactions.append(row_dict)
        logger.log(row_dict)

    logger.log(f"Found {len(transactions)} transactions.")
    return transactions

def get_categories(verbose=False):
    global connection
    logger.highlight("\nGetting transaction categories from server")
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM `banking_categories`")
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    categories = []
    for row in result:
        row_dict = dict(zip(columns, row))
        categories.append(row_dict)
        #logger.log(row_dict)

    categories.sort(key=lambda x: x['id'])

    for category in categories:
        indent = 0
        if category["id"] % 100 == 0:
            indent = 0
            logger.log("")
        elif category["id"] % 10 == 0:
            indent = 2
        elif category["id"] % 1 == 0:
            indent = 4
        logger.log(f"{category['id']} {(' ' * indent + category['name']).ljust(24)} {category['beschreibung']}")

    logger.log(f"\nFound {len(categories)} categories.")
    return categories

def print_transaction(transaction):
    #print(transaction)
    return f"{transaction['iban'][:4]}  {transaction['buchungsdatum']}  {str(transaction['banking_category']).rjust(3)}  {str(transaction['betrag']).rjust(8)}  {transaction['referenz']} "

def search_transactions(keyword):
    start_id = 0
    end_id = 5000

    # get transactions to match
    global connection
    logger.highlight("\nGetting transactions from server")
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM `banking` WHERE id >= {start_id} AND id < {end_id} AND referenz like '%{keyword}%'ORDER BY `banking`.`id` DESC")
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    transactions = []
    for row in result:
        row_dict = dict(zip(columns, row))
        row_dict["betrag"] = float(row_dict["betrag"])
        transactions.append(row_dict)
        #logger.log(print_transaction(row_dict))

    logger.log(f"Found {len(transactions)} transactions.")
    return transactions

def apply_searchstrings(overwrite=False, force=False):
    global connection
    logger.highlight("\nApplying searchstrings to transactions")
    cursor = connection.cursor()
    cursor.execute(f"SELECT banking_matching.*, banking_categories.name as cat_name FROM banking_matching JOIN banking_categories ON banking_matching.category = banking_categories.id")
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    searchstrings = []
    for row in result:
        row_dict = dict(zip(columns, row))
        searchstrings.append(row_dict)
        logger.log(row)

    cursor = connection.cursor()

    for searchstring in searchstrings:
        # logger.log(searchstring)
        logger.highlight(f"Applying searchstring: '{searchstring['searchstring']}', category: {searchstring['category']}, cat_name: {searchstring['cat_name']}")
        cursor.execute(f"SELECT * from banking WHERE referenz LIKE '%{searchstring['searchstring']}%'")

        result = cursor.fetchall()
        columns = [i[0] for i in cursor.description]
        affected_rows = []
        unaffected_rows = []
        for row in result:
            row_dict = dict(zip(columns, row))
            row_dict["betrag"] = float(row_dict["betrag"])
            category = row_dict['banking_category']
            if category == 0 or overwrite:
                affected_rows.append(row_dict)
            else:
                unaffected_rows.append(row_dict)

        if len(affected_rows) > 0:
            for item in affected_rows:
                logger.green(print_transaction(item))
            for item in unaffected_rows:
                logger.log(print_transaction(item))


            if not force:
                logger.log(f"Applying category to [{len(affected_rows)}] selected transactions? Type 'y' to confirm.")
                if input() != 'y':
                    continue

            if overwrite:
                update_string = f"UPDATE banking SET banking_category = {searchstring['category']} WHERE referenz LIKE '%{searchstring['searchstring']}%'"
            else:
                update_string = f"UPDATE banking SET banking_category = {searchstring['category']} WHERE referenz LIKE '%{searchstring['searchstring']}%' AND banking_category = 0"
            cursor.execute(update_string)
            result = cursor.fetchall()
            connection.commit()

    cursor.close()
    return

def reset_categories():
    global connection
    logger.highlight("\nResetting categories")
    cursor = connection.cursor()
    cursor.execute(f"UPDATE banking SET banking_category = 0")

    connection.commit()
    cursor.close()
    logger.log("Done resetting categories")
    return

def get_all_without_category(filtertest=False):
    results = send_query(f"SELECT * from banking WHERE banking_category = 0")
    if not filtertest:
        for row in results:
            print_transaction(row)

    if filtertest:
        while True:
            for row in results:
                print_transaction(row)
            searchstring = input("Apply Filter for referenz! CTRL-C to exit! \n > ")
            found_entries = 0
            for row in results:
                if searchstring.lower() in row["referenz"].lower():
                    found_entries += 1
                    logger.green(print_transaction(row))
            logger.log(f"Found {found_entries} entries for '{searchstring}'")


connect()

