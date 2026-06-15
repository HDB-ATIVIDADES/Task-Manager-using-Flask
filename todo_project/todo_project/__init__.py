import logging
import logging.handlers
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt


app = Flask(__name__)
app.config['SECRET_KEY'] = '45cf93c4d41348cd9980674ade9a7356'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'danger'

bcrypt = Bcrypt(app)

formatter = logging.Formatter(
    '%(asctime)s TaskManager[%(process)d]: %(levelname)s %(message)s'
)

try:
    syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
    syslog_handler.setFormatter(formatter)
    app.logger.addHandler(syslog_handler)
except (OSError, ConnectionError):
    app.logger.warning('Syslog not available')

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)


@app.before_request
def require_auth():
    from flask import request, redirect, url_for
    from flask_login import current_user
    public_routes = ['login', 'register', 'logout', 'static']
    if request.endpoint not in public_routes and not current_user.is_authenticated:
        app.logger.warning(
            f'UNAUTHORIZED_ACCESS ip={request.remote_addr} endpoint={request.endpoint}'
        )
        return redirect(url_for('login'))


from todo_project import routes
