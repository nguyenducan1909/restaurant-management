from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = '@#$%^*&A^D&A(D*D*^A&%^D$^%&DAY*UAD*AD^&'
app.config[
    "SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/foodhub?charset=utf8mb4" % quote(
    'admin123')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
