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
            db.drop_all()


@pytest.fixture
def auth_client(client):
    resp_register = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass',
        'confirm_password': 'testpass'
    }, follow_redirects=True)
    assert b'Account Created' in resp_register.data

    resp_login = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert b'Login Successfull' in resp_login.data

    return client


@pytest.fixture
def user(app_context):
    from todo_project import bcrypt
    hashed = bcrypt.generate_password_hash('secret').decode('utf-8')
    user = User(username='alice', password=hashed)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def user_with_tasks(user):
    task = Task(content='Task 1', author=user)
    db.session.add(task)
    db.session.commit()
    return user, task


@pytest.fixture
def app_context(client):
    with client.application.app_context():
        yield
