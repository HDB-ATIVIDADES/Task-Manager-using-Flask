from todo_project import db, bcrypt
from todo_project.models import User, Task


def test_create_user(app_context, user):
    saved = User.query.filter_by(username='alice').first()
    assert saved is not None
    assert saved.username == 'alice'
    assert len(saved.password) == 60


def test_password_hashing(app_context, user):
    assert bcrypt.check_password_hash(user.password, 'secret')
    assert not bcrypt.check_password_hash(user.password, 'wrong')


def test_password_with_special_chars(app_context):
    special = 'P@ssw0rd!#$%&*()'
    hashed = bcrypt.generate_password_hash(special).decode('utf-8')
    user = User(username='special', password=hashed)
    db.session.add(user)
    db.session.commit()

    saved = User.query.filter_by(username='special').first()
    assert bcrypt.check_password_hash(saved.password, special)


def test_create_task(app_context, user):
    task = Task(content='Buy milk', author=user)
    db.session.add(task)
    db.session.commit()

    saved = Task.query.filter_by(content='Buy milk').first()
    assert saved is not None
    assert saved.content == 'Buy milk'
    assert saved.author == user
    assert saved.user_id == user.id
    assert saved.date_posted is not None


def test_user_tasks_relationship(app_context, user):
    task1 = Task(content='Task 1', author=user)
    task2 = Task(content='Task 2', author=user)
    db.session.add_all([task1, task2])
    db.session.commit()

    assert len(user.tasks) == 2
    assert task1 in user.tasks
    assert task2 in user.tasks


def test_task_content_edge_cases(app_context, user):
    long_content = 'A' * 100
    task = Task(content=long_content, author=user)
    db.session.add(task)
    db.session.commit()
    assert len(task.content) == 100

    task_empty = Task(content='', author=user)
    db.session.add(task_empty)
    db.session.commit()
    assert task_empty.content == ''


def test_task_default_date(app_context, user):
    from datetime import datetime
    task = Task(content='Check date', author=user)
    db.session.add(task)
    db.session.commit()
    assert task.date_posted is not None
    assert isinstance(task.date_posted, datetime)


def test_user_repr(app_context, user):
    assert 'alice' in repr(user)


def test_task_repr(app_context, user_with_tasks):
    user, task = user_with_tasks
    assert task.content in repr(task)
    assert str(task.date_posted) in repr(task)
