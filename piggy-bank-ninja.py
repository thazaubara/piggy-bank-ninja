from datetime import datetime
import graph

import logger
import os


class Account:
    def __init__(self, accountnumber=None, name=None, startingbalance=None):
        self.accountnumber = accountnumber
        self.name = name
        self.startingbalance = startingbalance
        self.transactions = []

    def __str__(self):
        return f"{self.accountnumber} {self.name}"

    def calc_balance(self):
        balance = self.startingbalance
        for transaction in self.transactions:
            balance += float(transaction.betrag.replace(",", "."))
        return round(balance, 2)

class Transaction:
    def __init__(self, line=None):
        self.buchungsdatum = None
        self.referenz = None
        self.valuta = None
        self.betrag = None
        self.waehrung = None
        self.datum = None

        if line is not None:
            self.buchungsdatum, self.referenz, self.valuta, self.betrag, self.waehrung, self.datum = line.split(";")
            self.datum = self.datum.strip()  # because last column has \n at the end
            # datetime object from date  string in form of "%d.%m.%Y"
            self.buchungsdatum = self.buchungsdatum.strip('\ufeff')
            self.buchungsdatum = datetime.strptime(self.buchungsdatum, "%d.%m.%Y")

            # datetime object from date string in form of 15.03.2017 15:07:03:000
            self.datum = datetime.strptime(self.datum, "%d.%m.%Y %H:%M:%S:%f")

    def __str__(self):
        return f"{self.buchungsdatum} {str(self.betrag).rjust(9)} {self.waehrung}:  {self.referenz}"

    def __eq__(self, other):
        return self.buchungsdatum == other.buchungsdatum \
               and self.referenz == other.referenz \
               and self.valuta == other.valuta \
               and self.betrag == other.betrag \
               and self.waehrung == other.waehrung \
               and self.datum == other.datum



def read_files():
    global accounts
    logger.highlight("\nReading files...")
    directory_path = "files"  # Replace with the actual directory path
    if not (os.path.exists(directory_path) and os.path.isdir(directory_path)):
        logger.error(f"Directory {directory_path} does not exist.")
        return
    for file_name in os.listdir(directory_path):
        if not os.path.isfile(os.path.join(directory_path, file_name)):
            logger.error(f"{file_name} is not a file.")
            return
        with open(os.path.join(directory_path, file_name), 'r') as file:
            logger.log("Opened file: " + file_name)
            selected_account = None
            for account in accounts:
                if account.accountnumber in file_name:
                    selected_account = account
                    logger.log("Selected account: " + str(selected_account))
            if selected_account is None:
                logger.error(f"Could not find account for file {file_name}")
                return

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
                transaction = Transaction(line)
                if transaction in selected_account.transactions:
                    duplicates += 1
                    logger.debug(f"Duplicate found. Ignoring transaction: {transaction}")
                    continue
                added += 1
                selected_account.transactions.append(transaction)

            logger.log(f"Added {added} transactions. Found {duplicates} duplicates.")

    logger.log("Done reading files.")
    logger.log("Summary:")
    for account in accounts:
        logger.log(f"{account.accountnumber}: {len(account.transactions)} transactions from {account.transactions[0].buchungsdatum} to {account.transactions[-1].buchungsdatum}")

accounts = [Account(accountnumber="AT913301000004004636", name="Gehaltskonto", startingbalance=-706.88),
            Account(accountnumber="AT383301077704004636", name="Sparkonto", startingbalance=10500)]

logger.greeting()
read_files()


for account in accounts:
    # sum all transactions
    balance = account.calc_balance()
    logger.log(f"{account.accountnumber}: {balance} EUR")





