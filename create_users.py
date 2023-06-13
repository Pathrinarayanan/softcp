from app import app
from models import User, ROLE,db1

def create_users():
    with app.app_context():
        user1 = User(
            email='admin@example.com',
            password='password',
            first_name='Admin',
            last_name='User',
            role=ROLE.ADMIN
        )
        user2 = User(
            email='user@example.com',
            password='password',
            first_name='Regular',
            last_name='User',
            role=ROLE.USER
        )
        user1.save()
        user2.save()

def create100users():
    with app.app_context():
        for i in range(15):
            user = User(
                email=f'user{i}@example.com',
                password='password',
                first_name='Regular',
                last_name='User',
                role=ROLE.USER
            )
            user.save()

def delete_all_users():
    with app.app_context():
        users = User.query.all()
        for user in users:
            user.delete()

if __name__ == '__main__':
    create_users()
    #create100users()
    # delete_all_users()
