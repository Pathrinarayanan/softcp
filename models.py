from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db1 = SQLAlchemy()


class ROLE:
    ADMIN = 'super_admin'
    USER = 'user'
    ROLES = [ADMIN, USER]


class User(db1.Model):
    id = db1.Column(db1.Integer, primary_key=True)
    email = db1.Column(db1.String(255), unique=True, nullable=False)
    password_hash = db1.Column(db1.String(255), nullable=False)
    first_name = db1.Column(db1.String(255), nullable=False)
    last_name = db1.Column(db1.String(255), nullable=False)
    role = db1.Column(db1.Enum(*ROLE.ROLES), default=ROLE.USER)

    def __init__(self, email, password, first_name, last_name, role):
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        db1.session.add(self)
        db1.session.commit()

    def update(self):
        db1.session.commit()

    def delete(self):
        db1.session.delete(self)
        db1.session.commit()

    def __repr__(self):
        return f'<User {self.email}>'
