import os
import sqlite3
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
from time import sleep

from helpers import login_required, sql_insert, sql_select, sql_select_all, sql_search
from gen_pass import credit_pass, card_number, cc_code
from encrypt import encrypt_pass, decrypt_pass

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded.
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Load Database
db = sqlite3.connect("ito.db")

@app.route("/")
def index():
    return render_template('home.html')


@app.route("/account", methods=['GET','POST'])
@login_required
def account():
    # POST method
    if request.method == "POST":
        # Pay the credit invoice
        if request.form.get("submit") == "pay":
            # Get the user_cash
            query = """SELECT cash FROM user_cash WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            user_cash = sql_select(db, query, (session["user_id"], ))[0]

            # Get the credit
            query = """SELECT credit_usage FROM user_acc WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            user_credit = sql_select(db, query, (session["user_id"], ))[0]

            # Check if the user has any invoice
            if int(user_credit) == 0:
                return redirect("/account")

            # Check if has enough cash in account
            if int(user_cash) < int(user_credit):
                return redirect("/error")

            # UPDATE the table credit
            query =  """UPDATE user_acc SET credit_usage = ? WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, (0 , session["user_id"]))

            print(user_credit)
            # UPDATE THE cash
            query =  """UPDATE user_cash SET cash = ? WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, (int(user_cash) - int(user_credit), session["user_id"]))

            # ADD Operation
            query = """INSERT INTO operations(user_id, cash_amount, date_op, type_operation) VALUES((SELECT id FROM users WHERE login = ?), ?, ?, ?)"""
            sql_insert(db, query, (session["user_id"], int(user_credit), datetime.now().strftime("%m/%d/%Y"), "Credit"))

            return redirect("/account")
        else:
            return redirect("/"+request.form.get("submit"))
    # GET method
    else:
        # Get the user cash in account
        query = """SELECT cash FROM user_cash WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
        user = [sql_select(db, query, (session["user_id"], ))[0]]

        # Get the user credit limit in account
        query = """SELECT credit_limit, credit_usage FROM user_acc WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
        user.append(sql_select(db, query, (session["user_id"], )))

        return render_template("account.html", user=user)


@app.route("/statement", methods=["GET", "POST"])
@login_required
def statement():
    """Return the account statements"""
    if request.method == "POST":
        if request.form.get("submit") == "back":
            return redirect("/account")
    else:
        # Select the operations
        query = """SELECT type_operation, date_op, cash_amount FROM operations WHERE user_id = (SELECT id FROM users WHERE login = ?) ORDER BY date_op DESC"""
        operations = sql_select_all(db, query, (session["user_id"], ))
        sum_op = 0
        for op in range(0, len(operations)):
            sum_op += operations[op][2]
        return render_template("statement.html", operations=operations, sum_op=sum_op)


@app.route("/transfer", methods=['GET','POST'])
@login_required
def transfer():
    # POST method
    if request.method == "POST":
        if request.form.get("submit") == "next":
            # Check the ID input
            ID = request.form.get("ID")
            if not ID:
                return redirect("/error")
            if len(ID) != 11:
                return redirect('/error')

            # Get the ID to transfer
            query = """SELECT id FROM users WHERE login = ?"""

            # Check login in database
            try:
                transfer_id = sql_select(db, query, (ID, ))[0]
            except TypeError:
                return redirect("/error")

            # Get the user_id
            query = """SELECT id FROM users WHERE login = ?"""
            user_id = sql_select(db, query, (session["user_id"], ))[0]

            if user_id == transfer_id:
                print("Same ID")
                return redirect("/error")

            session["transferid"] = transfer_id
            session["transferlogin"] = ID
            query = """SELECT first_name, last_name FROM user_inf WHERE id_user = (SELECT id FROM users WHERE login = ?)"""
            names = sql_select(db, query, (ID, ))
            session["transferfirst"] = names[0]
            session["transferlast"] = names[1]
            return redirect("/transfer-next")
        else:
            return redirect("/account")
    # GET method
    else:
        return render_template("transfer.html")


@app.route("/transfer-next", methods=["GET", 'POST'])
@login_required
def transfer_next():
    # POST method
    if request.method == "POST":
        if request.form.get("submit") == "transfer":

            # Check the amount input
            amount = request.form.get("amount")
            if not amount:
                return redirect("/error")
            if not amount.isnumeric():
                return redirect("/error")

            # Check the password input
            password = request.form.get("pass")
            if not password:
                return redirect("/error")
            if len(password) != 4:
                return redirect("/error")

            # Get user id
            query = """SELECT id FROM users WHERE login = ?"""
            user_id = sql_select(db, query, (session["user_id"], ))[0]

            # Check Password
            query = """SELECT pass FROM user_acc WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            user_password = decrypt_pass(sql_select(db, query, (session["user_id"], ))[0], len(password))
            if user_password != password:
                print("invalid password")
                return redirect("/error")

            # Check if the user has the amount necessary
            query = """SELECT cash FROM user_cash WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            cash = int(sql_select(db, query, (session["user_id"], ))[0])
            if int(amount) > int(cash):
                return redirect("/error")

            # UPDATE THE USERS CASH AMOUNT
            query = """UPDATE user_cash SET cash = ? WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, ((cash - int(amount)), session["user_id"]))

            # UPDATE the receiver of the amount
            query = """UPDATE user_cash SET cash = ? WHERE id_cash = ?)"""
            sql_insert(db, query, (int(amount), session["transferid"]))

            # Register the operation in transfer table
            query = """INSERT INTO transfers(id_cashout, id_cashin, cash_amount, transf_date) VALUES(?, ?, ?, ?)"""
            sql_insert(db, query, (user_id, session["transferid"], int(amount), datetime.now().strftime("%m/%d/%Y")))

            # Register the operations in operation table
            query = """INSERT INTO operations(user_id, cash_amount, date_op, type_operation) VALUES(?, ?, ?, ?)"""
            sql_insert(db, query, (user_id, -int(amount), datetime.now().strftime("%m/%d/%Y"), "Transfer"))

            query = """INSERT INTO operations(user_id, cash_amount, date_op, type_operation VALUES(?, ?, ?, ?)"""
            sql_insert(db, query, (session["transferid"], int(amount), datetime.now().strftime("%m/%d/%Y"), "Transfer"))

            # Free the session
            session.pop("transferid")
            session.pop("transferlogin")
            session.pop("transferfirst")
            session.pop("transferlast")

            return redirect("/account")
        else:
            # Free the session
            # If the back button is pressed
            session.pop("transferid")
            session.pop("transferlogin")
            session.pop("transferfirst")
            session.pop("transferlast")

            return redirect("/transfer")
    # GET method
    else:
        # Allows the transfer-next only from the transfer
        try:
            session["transferid"]
        except KeyError:
            return redirect("/error")

        return render_template("transfer-next.html")


@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    """Deposit Cash"""

    # POST method
    if request.method == "POST":
        if request.form.get("submit") == "next":

            # Validate the bill number
            bill = request.form.get("bill")
            if not bill:
                return redirect("/account")

            if len(bill) != 48:
                return redirect("/account")

            # Check bill in database
            query = """SELECT bill_numbers FROM bill_inf WHERE bill_numbers = ?"""
            try:
                bills = sql_select(db, query, (bill, ))
                len(bills)
            except TypeError:
                return redirect("/error")

            # Store the bill numbers to load in the next page
            session["bill"] = bill
            return redirect("/next")
        else:
            return redirect("/account")

    # GET method
    else:
        return render_template("payment.html")


@app.route("/next", methods=["GET", "POST"])
@login_required
def payment_next():
    """Load bill informations"""
    # POST method
    if request.method == "POST":
        if request.form.get("submit") == "pay":

            # Check the account password
            password = request.form.get('pass')
            if len(password) != 4:
                return redirect("/error")

            query = """SELECT pass FROM user_acc WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            user_password = decrypt_pass(sql_select(db, query, (session["user_id"], ))[0], len(password))
            if user_password != password:
                print("invalid password")
                return redirect("/error")

            # Get the bill value
            query = """SELECT bill_numbers, bank, bill_value FROM bill_inf WHERE bill_numbers = ?"""
            bill = sql_select(db, query, (session["bill"], ))

            # Check if the user as the cash amount in account
            query = """SELECT cash FROM user_cash WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            cash = sql_select(db, query, (session["user_id"], ))[0]
            if cash < bill[2]:
                print("Invalid cash amount")
                return redirect("/error")

            # Add the operation in the payments table
            query = """INSERT INTO payment_operations(id_user, value, payment_date) VALUES((SELECT id FROM users WHERE login = ?), ?, ?)"""
            sql_insert(db, query, (session["user_id"], bill[2], datetime.now().strftime("%m/%d/%Y")))

            # UPDATE user cash amount in account
            query = """UPDATE user_cash SET cash = ? WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, (cash - bill[2], session['user_id']))

            # INSERT operation in operations table
            query = """INSERT INTO operations(user_id, cash_amount, date_op, type_operation) VALUES((SELECT id FROM users WHERE login = ?), ?, ?, ?)"""
            sql_insert(db, query, (session["user_id"], -bill[2], datetime.now().strftime("%m/%d/%Y"), "Payment"))

            # Free the session bill
            session.pop("bill")
            return redirect("/account")
        else:
            # Free the session
            session.pop("bill")
            return redirect("/payment")

    # GET method
    else:
        # Grant access only after the payment input
        try:
            session["bill"]
        except KeyError:
            return redirect("/error")

        query = """SELECT bill_numbers, bank, bill_value FROM bill_inf WHERE bill_numbers = ?"""
        bills = sql_select(db, query, (session["bill"], ))
        return render_template("next.html" , bill=bills)


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    # POST method
    if request.method == "POST":
        if request.form.get("submit") == "cash":
            cash = request.form.get("cash")
            # Check blank values
            if not cash:
                return redirect("/error")
            # Check if is digits
            if not cash.isdigit():
                return redirect("/error")
            # Check if is positive and different of zero and limit of 10000 deposit
            if int(cash) <= 0 or int(cash) > 10000:
                return redirect("/error")

            # Return the current amount in user account
            query = """SELECT cash FROM user_cash WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            user_cash = sql_select(db, query, (session["user_id"], ))[0]

            # Add the cash amount in the database
            query = """UPDATE user_cash SET cash = ? WHERE id_cash = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, (int(cash) + int(user_cash), session["user_id"]))

            return redirect("/account")
        # Back button pressed
        else:
            return redirect("/account")
    # GET method
    else:
        return render_template("cash.html")


@app.route("/credit", methods=["GET", "POST"])
@login_required
def credit():
    # POST method
    if request.method == "POST":
        if request.form.get("submit") == "credit":
            credit = request.form.get("credit")
            # Check blank values
            if not credit:
                return redirect("/error")
            # Check number values
            if not credit.isdigit():
                return redirect("/error")
            # Check postiive value
            if int(credit) <= 0:
                return redirect("/error")

            # Check limit value
            # Get user limit in database
            query = """SELECT credit_limit FROM user_acc WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            user_limit = sql_select(db, query, (session["user_id"], ))[0]

            # Get the current credit usage
            query = """SELECT credit_usage FROM user_acc WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            credit_usage = sql_select(db, query, (session["user_id"], ))[0]

            # Check if the operation is possible
            if int(credit) > (int(user_limit) - int(credit_usage)):
                return redirect("/error")

            # UPDATE the credit usage
            query =  """UPDATE user_acc SET credit_usage = ? WHERE id_pass = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, (int(credit) + int(credit_usage) , session["user_id"]))

            # ADD operation in operations
            query = """INSERT INTO operations(user_id, cash_amount, date_op, type_operation) VALUES((SELECT id FROM users WHERE login = ?), ?, ?, ?)"""
            sql_insert(db, query, (session["user_id"], -int(credit), datetime.now().strftime("%m/%d/%Y"), "Credit"))

            return redirect("/account")

        # Back Button
        else:
            return redirect("/account")
    # GET method
    else:
        return render_template("credit.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login User"""

    # Free cookies
    session.clear()

    # Post method
    if request.method == "POST":
        if request.form.get("submit") == "login":

            # Check blank inputs
            if not request.form.get("ID"):
                return redirect("/login")

            if not request.form.get("password"):
                return redirect("/login")

            # Return the inputed login
            query = """SELECT password FROM users WHERE login = ?"""
            try:
                search = sql_select(db, query, (request.form.get("ID"), ))[0]
                len(search)
            except TypeError:
                return redirect("/error")

            # decrypt the pass and search if it's the same
            if decrypt_pass(search, len(request.form.get("password"))) != request.form.get("password"):
                print("invalid password")
                return redirect("/error")

            # Add the ID in the cookie session
            session["user_id"] = request.form.get("ID")

            # Get the firstname and lastname of the person
            query = """SELECT first_name, last_name FROM user_inf WHERE id_user = (SELECT id FROM users WHERE login = ?)"""
            names = sql_select(db, query, (request.form.get("ID"), ))

            #Add the first name and last name in the session
            session["firstname"] = names[0]
            session["lastname"] = names[1]
            return redirect("/account")
        else:
            return redirect("/login")
    else:
        log = "TRUE"
        return render_template("login.html", log=log)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Create a banking account to the user"""
    # Post method
    if request.method == "POST":

        # Check the First Name input
        firstname = request.form.get("firstname")
        # Check blank spaces
        if not firstname:
            print("firstname")
            return redirect("/error")
        # Check if it's only alphabetic
        if not firstname.isalpha():
            print("firstname")
            return redirect("/error")

        # Check the Last Name input
        lastname = request.form.get("lastname")
        # Check blank spaces
        if not lastname:
            print("lastname")
            return redirect("/error")
        # Check if it's only alphabetic
        if not lastname.isalpha():
            print("lastname")
            return redirect("/error")

        # Check the ID input
        ID = request.form.get("ID")
        # Check black spaces
        if not ID:
            print("ID")
            return redirect("/error")
        # Check if it's only numbers
        if not ID.isnumeric():
            print("ID")
            return redirect("/error")
        # Check the len of the ID
        if len(ID) != 11:
            print("ID")
            return redirect("/error")

        # Check email input
        email = request.form.get("email")

        # Check password
        password = request.form.get("password")
        if not password:
            print("pass1")
            return redirect("/error")

        if len(password) < 8 or len(password) > 20:
            print("pass2")
            return redirect("/error")

        # Check if has digits and characters
        # Check if has only digits
        if not password.isdigit():
            # Check if has only characters
            if not password.isalpha():
                # Check if has special characters
                if password.isalnum():
                    pass
                else:
                    return redirect("/error")
            else:
                return redirect("/error")
        else:
            return redirect("/error")

        # Check confirmation password
        c_password = request.form.get("c-password")
        if password != c_password:
            print("pass4")
            return redirect("/error")

        # Check Phone
        phone = request.form.get("phone")
        # Check blank spaces
        if not phone:
            print("phone1")
            return redirect("/error")
        if not phone.isdigit():
            print("phone2")
            return redirect("/error")
        if len(phone) < 7 or len(phone) > 15:
            print('phone3')
            return redirect("/error")

        """Check if the inputs are already registered"""
        # Check if the ID is already registered
        query = """SELECT login FROM users WHERE login = ?"""
        if sql_search(db, query, (ID, ), "ID") == False:
            return redirect("/error")

        # Check if the e-mail is already registered
        query = """SELECT email FROM user_inf WHERE email = ?"""
        if sql_search(db, query, (email, ), "Email") == False:
            return redirect("/error")

        # Check if the phone number is already registered
        query = "SELECT phone_number FROM user_phone WHERE phone_number = ?"
        if sql_search(db, query, (phone, ), "Phone") == False:
            return redirect("/error")
        """"""

        # Insert login and encrypted password in table users
        query = "INSERT INTO users(login, password) VALUES(?, ?);"
        sql_insert(db, query, (ID, encrypt_pass(password)))

        # Insert user info in table user_inf
        query = "INSERT INTO user_inf(id_user, first_name, last_name, email) VALUES((SELECT id FROM users WHERE login = ?), ?, ?, ?)"
        sql_insert(db, query, (ID, firstname, lastname, email))

        # Insert user phone contact in table user_phone
        query = "INSERT INTO user_phone(id_phone, phone_number) VALUES((SELECT id FROM users WHERE login = ?), ?)"
        sql_insert(db, query, (ID, phone))

        # Insert cash and limit of the user
        query = "INSERT INTO user_cash(id_cash, cash) VALUES ((SELECT id FROM users WHERE login = ?), ?)"
        sql_insert(db, query, (ID, 0))

        # Generate credit card to the count
        credit = card_number()

        # Check if the credit number already exists.
        query = "SELECT cc_number FROM user_acc WHERE cc_number = ?"
        while True:
            try:
                # If return a len, the credit card number exist
                len(sql_select(db, query, (credit, )))
                # Return a new credit_card value
                credit = card_number()
            except TypeError:
                break

        # Insert the credit card values in the table user_acc
        # Encrypt the credit card password
        query = "INSERT INTO user_acc(id_pass, pass, cc_number, post_number, credit_limit) VALUES((SELECT id FROM users WHERE login = ?), ?, ?, ?, ?)"
        sql_insert(db, query, (ID, encrypt_pass(credit_pass()), credit, cc_code(), 50))

        return redirect("/")
    # Get method
    else:
        log = "TRUE"
        return render_template("register.html", log=log)


@app.route("/config", methods=["GET", "POST"])
@login_required
def config():
    # POST method
    if request.method == "POST":

        if request.form.get("submit") == "change":
            # Check email input
            email = request.form.get("email")
            query = """SELECT email FROM user_inf WHERE id_user = (SELECT id FROM users WHERE login = ?)"""
            if email != sql_select(db, query, (session["user_id"], ))[0]:
                print("Wrong Email")
                return redirect("/account")

            # Get new email
            new_email = request.form.get("new_email")

            if email == new_email:
                print("Invalid email")
                return redirect("/account")

            # Check if new_email is already in database
            query = """SELECT email FROM user_inf WHERE email = ?"""
            try:
                len(sql_select(db, query, (new_email, )))
                print("Email already in database")
                return redirect("/account")
            except TypeError:
                pass

            password = request.form.get("password")
            query = """SELECT password FROM users WHERE login = ?"""
            check_pass = sql_select(db, query, (session["user_id"], ))[0]

            # Check the input password
            if password != decrypt_pass(check_pass, len(password)):
                print("invalid password")
                return redirect("/account")
            # Change email
            query = """UPDATE user_inf SET email = ? WHERE id_user = (SELECT id FROM users WHERE login = ?)"""
            sql_insert(db, query, (new_email, session["user_id"]))

            print("Email changed")

            return redirect("/account")
        else:
            return redirect("/account")

    # GET method
    else:
        return render_template("config.html")


@app.route("/forget", methods=['GET', 'POST'])
def forget():
    # POST method
    if request.method == "POST":
        # Get the email
        email = request.form.get("email")
        return redirect("/login")
    else:
        log = "TRUE"
        return render_template("forget.html", log=log)


# Only Get Method
@app.route("/error")
def errors():
    return render_template("error.html")


