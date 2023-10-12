import logger
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors

def graph_balance(account):
    # graph balace with matplotlib
    dates = []
    balances = []
    balance = account.startingbalance
    for transaction in account.transactions:
        balance += float(transaction.betrag.replace(",", "."))
        dates.append(transaction.buchungsdatum)
        balances.append(balance)
        # logger.debug(balance)

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    line = ax.step(dates, balances, where="mid")

    # Customize the x-axis ticks to show every month
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m %Y'))
    plt.xticks(rotation=45)

    # Add labels and a title
    plt.xlabel("Date")
    plt.ylabel("Values")
    plt.title("Larger Chart with Every Month on X-Axis")

    # Use mplcursors to display values on hover with custom formatting
    cursor = mplcursors.cursor(line, hover=True)

    @cursor.connect("add")
    def on_hover(sel):
        x, y = sel.target
        x_formatted = mdates.DateFormatter('%b %Y')(mdates.date2num(x))
        y_formatted = f"{y:.0f}€"  # Format the y value
        sel.annotation.set_text(f"{y_formatted}")


    # Display the plot
    plt.tight_layout()
    plt.show()

def graph_multiple_accounts(accounts):
    # Create a figure for the entire plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Customize the x-axis ticks to show every month and format them as "%b %Y"
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m %Y'))
    plt.xticks(rotation=45)

    # Initialize colors for different accounts
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    for i, account in enumerate(accounts):
        # Prepare data for the current account
        dates = []
        balances = []
        balance = account.startingbalance
        for transaction in account.transactions:
            balance += float(transaction.betrag.replace(",", "."))
            dates.append(transaction.datum)
            balances.append(balance)
            # logger.log(balance)

        # Create a step chart for the current account
        line = ax.step(dates, balances, where="mid", label=f'{account.name}', color=colors[i], linewidth=0.75)

        # Use mplcursors to display values on hover with custom formatting
        cursor = mplcursors.cursor(line, hover=True)

        @cursor.connect("add")
        def on_hover(sel):
            x, y = sel.target
            y_formatted = f"{y:.2f}€"  # Format the y value with 2 decimal places
            sel.annotation.set_text(f"{y_formatted}")

    # Add labels, a title, and a legend
    plt.xlabel("Date")
    plt.ylabel("Values")
    plt.title("Multiple Account Balances with Every Month on X-Axis")
    plt.legend()

    # Display the plot
    plt.tight_layout()
    plt.show()