import pytest
from todo_project import app, db
from todo_project.models import User, Task


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def registered_user(client):
    client.post('/register', data={
        'username': 'testuser',
        'password': 'Test@123',
        'confirm_password': 'Test@123',
    }, follow_redirects=True)
    return 'testuser', 'Test@123'


@pytest.fixture
def logged_user(client, registered_user):
    username, password = registered_user
    client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)
    return username
