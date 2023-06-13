from flask import redirect, url_for, session
from models import ROLE,User
from functools import wraps
from datetime import datetime

def login_decorator(func):
    def wrapper(*args, **kwargs):
        if 'email' in session:
           return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    wrapper.__name__ = func.__name__
    return wrapper


def admin_decorator(func):
    def wrapper(*args, **kwargs):
        if session.get('role') == ROLE.ADMIN:
            return func(*args, **kwargs)
        else:
             return redirect(url_for('login'))
    wrapper.__name__ = func.__name__
    return wrapper


'''def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'email' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrapper
'''
# def create_log(email, lgout=None):
#     with open('logs.txt', 'a') as f:
#         if lgout:
#             f.write(f"{email} logged out at {datetime.now()}\n")
#         else:
#             f.write(f"{email} logged in at {datetime.now()}\n")


# RECORD_CREATED = "NCRP {} created by {} at {}"
# def basic_log(text):
#     with open('logs.txt', 'a') as f:
#         f.write(f"{text} at {datetime.now()}\n")