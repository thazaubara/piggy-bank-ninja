
import graph

import logger
import os
from database import *

def extract_accountnumber_from_filename(filename):
    accountnumbers = {"Gahaltskonto": "AT913301000004004636",
                      "Sparkonto": "AT383301077704004636"}
    for substr in filename.split("_"):
        if substr in accountnumbers.values():
            return substr
    return None

def transaction_dict_from_line(csv_line):
    if csv_line is not None:
        buchungsdatum, referenz, valuta, betrag, waehrung, datum = csv_line.split(";")

        # datetime object from date  string in form of "%d.%m.%Y"
        buchungsdatum = buchungsdatum.strip('\ufeff')
        buchungsdatum = datetime.strptime(buchungsdatum, "%d.%m.%Y")
        buchungsdatum = buchungsdatum.date()

        # referenz is already a string, kill quotes
        referenz = referenz.strip('"')
        referenz = referenz.strip("'")
        referenz = referenz.strip("'")

        # datetime object from date  string in form of "%d.%m.%Y"
        valuta = datetime.strptime(valuta, "%d.%m.%Y")
        valuta = valuta.date()

        betrag = float(str(betrag).replace(",", "."))

        # datetime object from date string in form of 15.03.2017 15:07:03:000
        datum = datum.strip()  # because last column has \n at the end
        datum = datetime.strptime(datum, "%d.%m.%Y %H:%M:%S:%f")

        return {"buchungsdatum": buchungsdatum,
                "referenz": referenz,
                "valuta": valuta,
                "betrag": betrag,
                "waehrung": waehrung,
                "datum": datum}

def read_all_files():
    transactions = []
    logger.highlight("\nReading files...")
    directory_path = "files"  # Replace with the actual directory path
    if not (os.path.exists(directory_path) and os.path.isdir(directory_path)):
        logger.error(f"Directory {directory_path} does not exist.")
        return
    for file_name in os.listdir(directory_path):
        if not os.path.isfile(os.path.join(directory_path, file_name)):
            logger.error(f"{file_name} is not a file.")
            continue
        with open(os.path.join(directory_path, file_name), 'r') as file:
            logger.log("Opened file: " + file_name)
            accountnumber = extract_accountnumber_from_filename(file_name)
            if not accountnumber:
                logger.error(f"Could not extract account number from file name: {file_name}")
                continue
            logger.log("Account number: " + accountnumber)

            # LIST FIRST AND LAST LINE FOR CHECK
            first_line = file.readline()
            # logger.log(first_line.strip())
            first_line_date = first_line.split(';')[0]
            last_line = file.readlines()[-1]
            last_line_date = last_line.split(';')[0]
            # logger.log(last_line.strip())
            logger.log(f"From: {first_line_date} to {last_line_date}")

            file.seek(0)
            duplicates = 0
            added = 0
            for line in file:
                transaction = transaction_dict_from_line(line)
                transaction["iban"] = accountnumber
                #print(transaction)

                if transaction in transactions:
                    duplicates += 1
                    logger.log(f"Duplicate found. Ignoring transaction: {transaction}")
                    continue

                transactions.append(transaction)
                added += 1

            logger.log(f"Added {added} transactions. Found {duplicates} duplicates.")
    logger.log(f"Done reading files. {len(transactions)} transactions registered.")
    sorted_transactions = sorted(transactions, key=lambda x: x['buchungsdatum'])

    return sorted_transactions

def print_transaction_stats(transactions):
    ibans = []
    for item in transactions:
        if item["iban"] not in ibans:
            ibans.append(item["iban"])
    logger.highlight("\nTransaction stats:")
    logger.log(f"Found {len(ibans)} different IBANs.")
    for iban in ibans:
        subset_transactions = []
        for item in transactions:
            if item["iban"] == iban:
                subset_transactions.append(item)
        logger.green(f"IBAN: {iban}")
        logger.log(f"{len(subset_transactions)} transactions")
        subset_transactions.sort(key=lambda x: x['buchungsdatum'])
        logger.log(f"First transaction: {subset_transactions[0]['buchungsdatum']}")
        logger.log(f"Last transaction: {subset_transactions[-1]['buchungsdatum']}")

def print_transactions(transactions):
    logger.highlight("\nTransactions:")
    if len(transactions) == 0:
        logger.log("empty list.")
    for transactions in transactions:
        logger.log(transactions)

def strip_up_to_max_date(transactions, max_date_transactions):
    logger.highlight("\nStripping transactions, that only new ones are left")
    # check for each iban
    ibans = []
    stripped_transactions = []
    for item in transactions:
        if item["iban"] not in ibans:
            ibans.append(item["iban"])
    logger.log(f"Found {len(ibans)} different IBANs.")

    for iban in ibans:
        logger.log(f"Checking iban {iban}")

        # find max date for iban on server item
        max_date = None
        for max_date_transaction in max_date_transactions:
            if max_date_transaction["iban"] == iban:
                max_date = max_date_transaction["buchungsdatum"]
        if max_date is None:
            logger.error(f"Could not find max date for iban {iban}")
            continue
        logger.log(f"Max date for iban {iban} is {max_date}")

        # compare max date with max date for iban on local item
        for transaction in transactions:
            if transaction["iban"] == iban:
                if transaction["buchungsdatum"] < max_date:
                    pass
                    #logger.log(f"Transaction is older than {max_date}. Removing transaction: {transaction}")
                    #transactions.remove(transaction)
                elif transaction["buchungsdatum"] == max_date:
                    logger.log(f"Transaction is same date as {max_date}. Comparing referenz.")
                    same_name = False
                    for max_date_transaction in max_date_transactions:
                        if transaction["referenz"] == max_date_transaction["referenz"]:
                            logger.log(f"Referenz is same. Removing transaction: {transaction}")
                            same_name = True
                    if not same_name:
                        stripped_transactions.append(transaction)
                elif transaction["buchungsdatum"] > max_date:
                    logger.log(f"Transaction is newer than {max_date}. Keeping transaction: {transaction}")
                    stripped_transactions.append(transaction)
                else:
                    logger.error(f"Something went wrong with transaction: {transaction}")
        logger.log(f"Done with iban {iban}")

        for max_date_transaction in max_date_transactions:
            if max_date_transaction in stripped_transactions:
                stripped_transactions.remove(max_date_transaction)
    # if max date is same, compare referenz. if referenz is same, remove transaction
    return stripped_transactions



logger.greeting()
transactions = read_all_files()
print_transaction_stats(transactions)
# upload_transactions(transactions)
max_date = get_max_date()
stripped = strip_up_to_max_date(transactions, max_date)
print_transactions(stripped)

# upload_transactions(accounts[0])
# upload_transactions(accounts[1])






