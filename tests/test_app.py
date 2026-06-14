from todo_project import db
from todo_project.models import User, Task


def text(response):
    return response.get_data(as_text=True)


class TestRoutes:
    def test_homepage(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_login_page(self, client):
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page(self, client):
        response = client.get('/register')
        assert response.status_code == 200

    def test_about_page(self, client):
        response = client.get('/about')
        assert response.status_code == 200

    def test_all_tasks_redirects_when_anon(self, client):
        response = client.get('/all_tasks', follow_redirects=True)
        assert response.status_code == 200
        assert 'Login' in text(response) or 'login' in text(response).lower()


class TestAuthentication:
    def test_successful_registration(self, client):
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'Secret@123',
            'confirm_password': 'Secret@123',
        }, follow_redirects=True)
        assert response.status_code == 200
        with client.application.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None

    def test_duplicate_username(self, client, registered_user):
        response = client.post('/register', data={
            'username': 'testuser',
            'password': 'Other@123',
            'confirm_password': 'Other@123',
        }, follow_redirects=True)
        assert response.status_code == 200
        html = text(response)
        assert 'Username Exists' in html or 'existe' in html.lower()

    def test_successful_login(self, client, registered_user):
        username, password = registered_user
        response = client.post('/login', data={
            'username': username,
            'password': password,
        }, follow_redirects=True)
        assert response.status_code == 200
        html = text(response)
        assert 'logout' in html.lower() or 'all tasks' in html.lower()

    def test_failed_login(self, client):
        response = client.post('/login', data={
            'username': 'noone',
            'password': 'wrong',
        }, follow_redirects=True)
        assert response.status_code == 200
        html = text(response)
        assert 'Unsuccessful' in text(response) or 'incorreta' in html.lower()

    def test_logout(self, client, logged_user):
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        html = text(response)
        assert 'login' in html.lower()


class TestTaskCRUD:
    def test_add_task(self, client, logged_user):
        response = client.post('/add_task', data={
            'task_name': 'Comprar pão',
        }, follow_redirects=True)
        assert response.status_code == 200
        with client.application.app_context():
            user = User.query.filter_by(username=logged_user).first()
            task = Task.query.filter_by(author=user).first()
            assert task is not None
            assert task.content == 'Comprar pão'

    def test_view_all_tasks(self, client, logged_user):
        client.post('/add_task', data={'task_name': 'Tarefa 1'})
        response = client.get('/all_tasks')
        assert response.status_code == 200
        assert 'Tarefa 1' in text(response)

    def test_delete_task(self, client, logged_user):
        client.post('/add_task', data={'task_name': 'Para deletar'})
        with client.application.app_context():
            task = Task.query.first()
            task_id = task.id

        response = client.get(f'/all_tasks/{task_id}/delete_task', follow_redirects=True)
        assert response.status_code == 200
        with client.application.app_context():
            deleted = Task.query.get(task_id)
            assert deleted is None

    def test_update_task(self, client, logged_user):
        client.post('/add_task', data={'task_name': 'Original'})
        with client.application.app_context():
            task = Task.query.first()
            task_id = task.id

        response = client.post(f'/all_tasks/{task_id}/update_task', data={
            'task_name': 'Atualizada',
        }, follow_redirects=True)
        assert response.status_code == 200
        with client.application.app_context():
            updated = Task.query.get(task_id)
            assert updated.content == 'Atualizada'


class TestModels:
    def test_create_user(self, client):
        with client.application.app_context():
            user = User(username='modeluser', password='hash')
            db.session.add(user)
            db.session.commit()
            fetched = User.query.filter_by(username='modeluser').first()
            assert fetched is not None
            assert fetched.password == 'hash'

    def test_create_task(self, client, logged_user):
        with client.application.app_context():
            user = User.query.filter_by(username=logged_user).first()
            task = Task(content='Task de teste', author=user)
            db.session.add(task)
            db.session.commit()
            fetched = Task.query.filter_by(content='Task de teste').first()
            assert fetched is not None
            assert fetched.author == user
