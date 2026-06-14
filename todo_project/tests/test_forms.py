from todo_project.forms import RegistrationForm, LoginForm, TaskForm
from todo_project import db
from todo_project.models import User


class TestRegistrationForm:

    def test_valid_data(self, client):
        with client.application.app_context():
            form = RegistrationForm(
                username='validuser',
                password='secret',
                confirm_password='secret',
                submit='Register'
            )
            form.validate()
            assert form.username.data == 'validuser'
            assert len(form.username.errors) == 0

    def test_username_too_short(self, client):
        with client.application.app_context():
            form = RegistrationForm(
                username='ab',
                password='secret',
                confirm_password='secret',
                submit='Register'
            )
            assert not form.validate()
            assert len(form.username.errors) > 0

    def test_password_mismatch(self, client):
        with client.application.app_context():
            form = RegistrationForm(
                username='testuser',
                password='secret1',
                confirm_password='secret2',
                submit='Register'
            )
            assert not form.validate()
            assert len(form.confirm_password.errors) > 0

    def test_duplicate_username_validated(self, client):
        with client.application.app_context():
            from todo_project import bcrypt
            hashed = bcrypt.generate_password_hash('secret').decode('utf-8')
            user = User(username='existing', password=hashed)
            db.session.add(user)
            db.session.commit()

            form = RegistrationForm(
                username='existing',
                password='secret',
                confirm_password='secret',
                submit='Register'
            )
            assert not form.validate()
            assert any('exists' in e.lower() for e in form.username.errors)


class TestLoginForm:

    def test_valid_login_form(self, client):
        with client.application.app_context():
            form = LoginForm(
                username='myuser',
                password='mypass',
                submit='Login'
            )
            assert form.validate()

    def test_missing_password(self, client):
        with client.application.app_context():
            form = LoginForm(
                username='myuser',
                password='',
                submit='Login'
            )
            assert not form.validate()

    def test_missing_username(self, client):
        with client.application.app_context():
            form = LoginForm(
                username='',
                password='mypass',
                submit='Login'
            )
            assert not form.validate()


class TestTaskForm:

    def test_valid_task(self, client):
        with client.application.app_context():
            form = TaskForm(
                task_name='Buy groceries',
                submit='Add Task'
            )
            assert form.validate()

    def test_empty_task(self, client):
        with client.application.app_context():
            form = TaskForm(
                task_name='',
                submit='Add Task'
            )
            assert not form.validate()
