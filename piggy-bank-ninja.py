import json

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
        if "'" in referenz:
            logger.warn(f"Found ' in referenz: {referenz}")
            referenz = referenz.replace("'", "")
        #referenz = referenz.strip("'")
        #referenz = referenz.strip("'")


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
                    logger.debug(f"Duplicate found. Ignoring transaction: {transaction}")
                    continue

                transactions.append(transaction)
                added += 1

            logger.log(f"Added {added} transactions. Found {duplicates} duplicates.")
    logger.log(f"Done reading files. {len(transactions)} transactions registered.")
    sorted_transactions = sorted(transactions, key=lambda x: x['buchungsdatum'])

    return sorted_transactions

def print_transaction_stats(transactions):
    logger.highlight("\nTransaction stats:")
    logger.log(f"Found {len(transactions)} transactions.")
    ibans = []
    for item in transactions:
        if item["iban"] not in ibans:
            ibans.append(item["iban"])

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
    logger.log("Stripping transactions, that only new ones are left")
    # check for each iban
    ibans = []
    stripped_transactions = []
    for item in transactions:
        if item["iban"] not in ibans:
            ibans.append(item["iban"])
    logger.debug(f"Found {len(ibans)} different IBANs.")

    for iban in ibans:
        logger.debug(f"Checking iban {iban}")

        # find max date for iban on server item
        max_date = None
        for max_date_transaction in max_date_transactions:
            if max_date_transaction["iban"] == iban:
                max_date = max_date_transaction["buchungsdatum"]
        if max_date is None:
            logger.error(f"Could not find max date for iban {iban}. Appending all.")
            for transaction in transactions:
                if transaction["iban"] == iban:
                    stripped_transactions.append(transaction)
            continue
        logger.debug(f"Max date for iban {iban} is {max_date}")

        # compare max date with max date for iban on local item
        for transaction in transactions:
            if transaction["iban"] == iban:
                if transaction["buchungsdatum"] < max_date:
                    pass
                    logger.debug(f"Transaction is older than {max_date}. Removing transaction: {transaction}")
                    # transactions.remove(transaction)
                else:
                    logger.debug(f"Transaction is same or newer than {max_date}. Keeping transaction: {transaction}")
                    found_same = False
                    for max_date_transaction in max_date_transactions:
                        if max_date_transaction["referenz"] == transaction["referenz"]:
                            found_same = True
                            logger.debug(f"   Found same transaction on server: {max_date_transaction}")
                    if not found_same:
                        logger.debug(f"   Did not find same transaction on server. Keeping transaction: {transaction}")
                        stripped_transactions.append(transaction)
        logger.log(f"Done with iban {iban}")
    logger.green(f"Done stripping transactions. {len(stripped_transactions)} transactions left.")

    # if max date is same, compare referenz. if referenz is same, remove transaction
    return stripped_transactions

def generate_sql_from_old_lut():
    logger.highlight("\nReading regex")
    regex = []
    with open("lut.json", 'r') as file:
        for entry in json.load(file):
            #logger.log(entry)
            regex.append(entry)

    logger.log(f"Found {len(regex)} entries in LUT")

    regex.sort(key=lambda x: x['regex'])
    regex_clean = []
    for item in regex:
        if item['regex'] != "":
            regex_clean.append(item)
            continue

    logger.log(f"Cleaned down to {len(regex_clean)} entries.")
    for item in regex_clean:

        sqlstring = f"INSERT INTO `banking_matching` (`searchstring`, `name`, `info`) VALUES ('{item['regex'][2:-2]}', '{item['name']}', '{'alte kategorie: ' + item['kategorie']}');"
        logger.log(sqlstring)
    return regex

def upload_new_transactions():
    transactions = read_all_files()
    print_transaction_stats(transactions)

    max_date = get_max_date()
    stripped = strip_up_to_max_date(transactions, max_date)

    print_transactions(stripped)
    print_transaction_stats(stripped)

    user_input = input(f"Upload {len(stripped)} transactions? Type '{len(stripped)}' in console: ")
    if user_input == len(stripped):
        upload_transactions(stripped)
    else:
        logger.log("Aborted.")




# SET UP DATABASE FROM CSV FILES
#generate_sql_from_old_lut()
# upload_new_transactions()

#

# GET CATEGORIES AND DISPLAY FROM SERVER
#reset_categories()
#get_categories(verbose=True)
# search_transactions("hofer dankt  ")

#apply_searchstrings(overwrite=False, force=True)
# get_all_without_category(filtertest=True)



if __name__ == "__main__":
    logger.greeting()
    while True:
        user_inp = input("> ")
        if user_inp == "exit":
            logger.log("thx 4 using Piggy Bank Ninja!")
            logger.log("cya next year ;)")
            break
        elif user_inp == "list-categories" or user_inp == "lc":
            get_categories(verbose=True)
        elif user_inp == "reset-categories" or user_inp == "rc":
            reset_categories()
        elif user_inp == "upload-csv" or user_inp == "ul":
            upload_new_transactions()
        elif user_inp.startswith("list-without-category") or user_inp.startswith("lw"):
            search_transactions(searchstring=user_inp.split(" ")[1])
        elif user_inp == "help" or user_inp == "h":
            logger.log("exit: exit program")
            logger.log("help [h]: show this help")
            logger.log("list-categories [lc]: list all categories")
            logger.log("upload-csv [ul]: upload new transactions from ./files")
            logger.log("list-without-category [lwc]: list all transactions without category")
            logger.log("reset-categories [rc]: reset all categories to default")
            logger.log("")
        else:
            logger.log("Unknown command. Type 'help' for help.")



