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
        # logger.log(row_dict)

    logger.log(f"Found {len(transactions)} transactions.")
    return transactions

def get_max_date():
    global connection
    logger.highlight("\nGetting latest (MAX(buchungsdatum)) transactions from server for each iban")
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
    if verbose:
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

    if verbose:
        logger.log(f"Found {len(categories)} categories.")
    categories.sort(key=lambda x: x['id'])

    for category in categories:
        indent = 0
        if category["id"] % 100 == 0:
            indent = 0
            if verbose:
                logger.log("")
        elif category["id"] % 10 == 0:
            indent = 2
        elif category["id"] % 1 == 0:
            indent = 4
        if verbose:
            logger.log(f"{category['id']} {(' ' * indent + category['name']).ljust(24)} {category['beschreibung']}")

    if verbose:
        logger.log("")

    return categories

def get_categories_with_tags(verbose=False):
    global connection
    logger.highlight("\nGetting transaction categories with tags from server")
    cursor = connection.cursor()
    cursor.execute("SELECT c.id, c.name, c.beschreibung, COALESCE(bm.searchstring, '') AS matching_searchstring, COALESCE(bm.active, '') AS matching_active, COALESCE(bm.name, '') AS matching_name, COALESCE(bm.info, '') AS matching_info FROM banking_categories c LEFT JOIN banking_matching bm ON c.id = bm.category ORDER BY `c`.`id` ASC")
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    categories = []
    for row in result:
        row_dict = dict(zip(columns, row))
        categories.append(row_dict)
        # logger.log(row_dict)

    logger.log(f"Found {len(categories)} categories.")
    categories.sort(key=lambda x: x['id'])

    for category in categories:
        indent = 0
        if category["id"] % 100 == 0:
            indent = 0
        elif category["id"] % 10 == 0:
            indent = 2
        elif category["id"] % 1 == 0:
            indent = 4
        logger.log(f"{category['id']} {(' ' * indent + category['name']).ljust(24)} {category['matching_searchstring'].ljust(24)} {category['matching_name'].ljust(24)}")

    logger.log("")

    return categories

def print_transaction(transaction):
    #print(transaction)
    if transaction["betrag"] > 0:
        betrag_string = "\033[32m" + "{: >8.2f}".format(transaction["betrag"]) + "\033[0m"
    else:
        betrag_string = "\033[31m" + "{: >8.2f}".format(transaction["betrag"]) + "\033[0m"
    datum_string = str(transaction["buchungsdatum"])
    referenz_string = str(transaction["referenz"])
    category = str(transaction["banking_category"])
    if category == "0" or category == "None":
        category = "   "
    logger.log(f"[{category}] {betrag_string}    {datum_string}    {referenz_string}")
    # return f"{transaction['iban'][:4]}  {transaction['buchungsdatum']}  {str(transaction['banking_category']).rjust(3)}  {str(transaction['betrag']).rjust(8)}  {transaction['referenz']} "

"""
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
    """

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
    user_input = input("Are you sure? Type 'yes' to confirm. \n> ")
    if user_input != 'yes':
        return

    cursor = connection.cursor()
    cursor.execute(f"UPDATE banking SET banking_category = 0")

    connection.commit()
    cursor.close()
    logger.log("Done resetting categories")
    return

def get_all_without_category(loop=False, searchstring=""):
    results = send_query(f"SELECT * from banking WHERE banking_category = 0")
    if not loop:
        for row in results:
            print_transaction(row)

    if loop:
        while True:
            for row in results:
                print_transaction(row)
            searchstring = input("Apply Filter for referenz! Type 'exit' to exit \nlwc > ")
            if searchstring == 'exit':
                break
            found_entries = 0
            for row in results:
                if searchstring.lower() in row["referenz"].lower():
                    found_entries += 1
                    logger.green(print_transaction(row))
            logger.log(f"Found {found_entries} entries for '{searchstring}'")

def cat_to_path(category):
    # logger.log(f"cat_to_path({category})")
    try:
        category = int(category)
    except:
        logger.warn(f"Category {category} is not an integer. Aborting.")
        return

    categories = get_categories()
    cat_found = False
    for cat in categories:
        if cat["id"] == category:
            logger.debug(f"Found category {cat['name']}")
            cat_found = True
    if not cat_found:
        logger.warn(f"Category {category} not found. Aborting.")
        return

    path = []
    path.append((category // 100) * 100)
    if category % 100 != 0:
        path.append((category // 10) * 10)
    if category % 10 != 0:
        path.append(category)

    path_string = ""
    for item in path:
        for cat in categories:
            if cat["id"] == item:
                path_string += f"/{cat['name']}"
    path_string = path_string[1:]
    logger.debug(path_string)
    return path_string

def add_tag(category="", tag_string=""):

    # sanity check: does category exist on server?
    path = cat_to_path(category)
    if path is None:
        return
    logger.log(f"Adding tag '{tag_string}'")
    logger.log(f"Category: {category} -> {path}")
    search_transactions(searchstring=tag_string)
    logger.log("Create new Tag? Type 'y' to confirm.")
    if input() == 'y':
        cursor = connection.cursor()
        insert_query = f"INSERT INTO banking_matching (searchstring, category) " \
                       f"VALUES ('{tag_string}', '{category}')"
        cursor.execute(insert_query)
        result = cursor.fetchall()
        connection.commit()
        cursor.close()
        logger.log(f"Done uploading tag with result: {result}")



def search_transactions(searchstring="", category=None):
    base_sql = f"SELECT * from banking"
    if searchstring != "":
        base_sql += f" WHERE referenz LIKE '%{searchstring}%'"
    if category is not None:
        base_sql += f" AND banking_category = {category}"
    else:
        pass

    logger.log(base_sql)
    results = send_query(base_sql)
    for row in results:
        print_transaction(row)

connect()

