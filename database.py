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
            print(f"{error} {transaction}")
        progress += 1

    connection.commit()
    cursor.close()

def get_max_date():
    global connection
    cursor = connection.cursor()
    cursor.execute(f"SELECT iban, buchungsdatum, referenz, valuta, betrag, waehrung, datum FROM banking WHERE (iban, datum) IN (SELECT iban, MAX(datum) FROM banking GROUP BY iban);")
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()

    transactions = []
    for row in result:
        row_dict = dict(zip(columns, row))
        row_dict["betrag"] = float(row_dict["betrag"])
        transactions.append(row_dict)
        logger.log(row_dict)
    return transactions

connect()

