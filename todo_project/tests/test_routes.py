import logging

from todo_project import db
from todo_project.models import Task


def _add_task_and_get_id(client, task_name='Default task'):
    client.post('/add_task', data={'task_name': task_name}, follow_redirects=True)
    with client.application.app_context():
        task = Task.query.filter_by(content=task_name).first()
        return task.id if task else None


class TestAuthentication:

    def test_login_page(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_register_page(self, client):
        resp = client.get('/register')
        assert resp.status_code == 200

    def test_register_user(self, client):
        resp = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass',
            'confirm_password': 'newpass'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Account Created' in resp.data

    def test_login_success(self, client):
        client.post('/register', data={
            'username': 'user1',
            'password': 'pass1',
            'confirm_password': 'pass1'
        })
        resp = client.post('/login', data={
            'username': 'user1',
            'password': 'pass1'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login Successfull' in resp.data

    def test_login_failure(self, client):
        resp = client.post('/login', data={
            'username': 'noexist',
            'password': 'wrong'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login Unsuccessful' in resp.data

    def test_logout_redirects_to_login(self, client):
        client.post('/register', data={
            'username': 'user2',
            'password': 'pass2',
            'confirm_password': 'pass2'
        })
        client.post('/login', data={
            'username': 'user2',
            'password': 'pass2'
        })
        resp = client.get('/logout', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Sign In' in resp.data or b'Login' in resp.data

    def test_register_duplicate_username(self, client):
        client.post('/register', data={
            'username': 'dup',
            'password': 'pass',
            'confirm_password': 'pass'
        })
        resp = client.post('/register', data={
            'username': 'dup',
            'password': 'pass2',
            'confirm_password': 'pass2'
        }, follow_redirects=True)
        assert b'Username Exists' in resp.data


class TestAuthorization:

    def test_all_tasks_requires_auth(self, client):
        resp = client.get('/all_tasks', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data or b'login' in resp.data.lower()

    def test_add_task_requires_auth(self, client):
        resp = client.post('/add_task', data={'task_name': 'hack'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data or b'login' in resp.data.lower()

    def test_account_requires_auth(self, client):
        resp = client.get('/account', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data or b'login' in resp.data.lower()

    def test_about_requires_auth(self, client):
        resp = client.get('/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data or b'login' in resp.data.lower()

    def test_about_page_requires_auth(self, client):
        resp = client.get('/about', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data or b'login' in resp.data.lower()


class TestTaskCRUD:

    def test_add_task(self, auth_client):
        resp = auth_client.post('/add_task', data={
            'task_name': 'My test task'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Task Created' in resp.data

    def test_all_tasks_shows_tasks(self, auth_client):
        auth_client.post('/add_task', data={'task_name': 'Task A'}, follow_redirects=True)
        auth_client.post('/add_task', data={'task_name': 'Task B'}, follow_redirects=True)
        resp = auth_client.get('/all_tasks', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Task A' in resp.data
        assert b'Task B' in resp.data

    def test_update_task(self, auth_client):
        task_id = _add_task_and_get_id(auth_client, 'Task to update')
        assert task_id is not None

        resp = auth_client.post(f'/all_tasks/{task_id}/update_task', data={
            'task_name': 'Updated name'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Task Updated' in resp.data

    def test_delete_task(self, auth_client):
        task_id = _add_task_and_get_id(auth_client, 'Task to delete')
        assert task_id is not None

        resp = auth_client.get(f'/all_tasks/{task_id}/delete_task', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Task Deleted' in resp.data


class TestTaskIsolation:

    def test_update_other_users_task_returns_403(self, client):
        client.post('/register', data={
            'username': 'alice', 'password': 'alicepass', 'confirm_password': 'alicepass'
        }, follow_redirects=True)
        client.post('/login', data={
            'username': 'alice', 'password': 'alicepass'
        }, follow_redirects=True)
        task_id = _add_task_and_get_id(client, 'Alice task')
        assert task_id is not None

        client.get('/logout', follow_redirects=True)
        client.post('/register', data={
            'username': 'bob', 'password': 'bobpass', 'confirm_password': 'bobpass'
        }, follow_redirects=True)
        client.post('/login', data={
            'username': 'bob', 'password': 'bobpass'
        }, follow_redirects=True)
        resp = client.post(
            f'/all_tasks/{task_id}/update_task',
            data={'task_name': 'Hacked'},
            follow_redirects=True
        )
        assert resp.status_code == 403

    def test_delete_other_users_task_returns_403(self, client):
        client.post('/register', data={
            'username': 'alice', 'password': 'alicepass', 'confirm_password': 'alicepass'
        }, follow_redirects=True)
        client.post('/login', data={
            'username': 'alice', 'password': 'alicepass'
        }, follow_redirects=True)
        task_id = _add_task_and_get_id(client, 'Alice task')
        assert task_id is not None

        client.get('/logout', follow_redirects=True)
        client.post('/register', data={
            'username': 'bob', 'password': 'bobpass', 'confirm_password': 'bobpass'
        }, follow_redirects=True)
        client.post('/login', data={
            'username': 'bob', 'password': 'bobpass'
        }, follow_redirects=True)
        resp = client.get(
            f'/all_tasks/{task_id}/delete_task',
            follow_redirects=True
        )
        assert resp.status_code == 403


class TestAccount:

    def test_account_page(self, auth_client):
        resp = auth_client.get('/account')
        assert resp.status_code == 200

    def test_change_password(self, auth_client):
        resp = auth_client.post('/account/change_password', data={
            'old_password': 'testpass',
            'new_password': 'newpass'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Password Changed' in resp.data

    def test_change_password_wrong_old(self, auth_client):
        resp = auth_client.post('/account/change_password', data={
            'old_password': 'wrong',
            'new_password': 'newpass'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Please Enter Correct Password' in resp.data


class TestSyslog:

    def test_login_success_logs(self, caplog, client):
        caplog.set_level(logging.INFO)
        client.post('/register', data={
            'username': 'logsuser',
            'password': 'logspass',
            'confirm_password': 'logspass'
        }, follow_redirects=True)
        caplog.clear()
        client.post('/login', data={
            'username': 'logsuser',
            'password': 'logspass'
        }, follow_redirects=True)
        assert any('LOGIN_SUCCESS' in msg for msg in caplog.messages)

    def test_login_failure_logs(self, caplog, client):
        caplog.set_level(logging.INFO)
        client.post('/login', data={
            'username': 'nobody',
            'password': 'wrong'
        }, follow_redirects=True)
        assert any('LOGIN_FAILURE' in msg for msg in caplog.messages)

    def test_register_success_logs(self, caplog, client):
        caplog.set_level(logging.INFO)
        client.post('/register', data={
            'username': 'reguser',
            'password': 'regpass',
            'confirm_password': 'regpass'
        }, follow_redirects=True)
        assert any('REGISTER_SUCCESS' in msg for msg in caplog.messages)

    def test_add_task_logs(self, caplog, auth_client):
        caplog.set_level(logging.INFO)
        auth_client.post('/add_task', data={
            'task_name': 'Log task'
        }, follow_redirects=True)
        assert any('OPERATION_SUCCESS' in msg for msg in caplog.messages)
