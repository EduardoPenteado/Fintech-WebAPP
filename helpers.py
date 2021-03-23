import sqlite3
from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def sql_insert(db, query, data):
    try:
        cursor = db.cursor()
        cursor.execute(query, data)
        db.commit()
        cursor.close()
    except Exception:
        return redirect("/error")


def sql_select(db, query, data):
    try:
        cursor = db.cursor()
        cursor.execute(query, data)
        search = cursor.fetchall()[0]
        cursor.close()
        return search
    except Exception:
        return redirect("/error")


def sql_select_all(db, query, data):
    try:
        cursor = db.cursor()
        cursor.execute(query, data)
        search = cursor.fetchall()
        cursor.close()
        return search
    except Exception:
        return redirect("/error")


def sql_search(db, query, data, message):
    try:
        len(sql_select(db, query, data))
        print(message + " Already Registered")
        return False
    except TypeError:
        return True

