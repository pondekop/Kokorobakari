from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import uuid # 一意なIDを生成するためのライブラリ
from sqlalchemy import ForeignKey

db = SQLAlchemy()
bcrypt = ()
friendships = db.Table(
    'friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Integer, default=0)
    friends = db.relationship('User', secondary='friendships', backref='friend_of')
    is_active_field = db.Column(db.Boolean, default=True)
    unique_id = db.Column(db.String(20), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8])  # 8文字の一意なIDを生成

    # 多対多のリレーションを定義
    friends = db.relationship(
        'User',
        secondary='friendships',
        primaryjoin=(id == friendships.c.user_id),
        secondaryjoin=(id == friendships.c.friend_id),
        backref='friend_of'
    )

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)  # UserのIDを返す

    # Flask-Login用にis_activeプロパティを定義
    @property
    def is_active(self):
        return self.is_active_field  # is_active_fieldで定義したフィールドを返す

    @property
    def is_authenticated(self):
        return True  # 常に認証されていると仮定（ログイン時に適切にチェックする）

    @property
    def is_anonymous(self):
        return False  # 匿名ユーザーではない

class Friendship(db.Model):
    __tablename__ = 'friendship'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 外部キーを使ってリレーションを明示的に定義
    user = db.relationship("User", foreign_keys=[user_id], backref="friendships_as_user")
    friend = db.relationship("User", foreign_keys=[friend_id], backref="friendships_as_friend")

    def __repr__(self):
        return f"<Friendship user_id={self.user_id}, friend_id={self.friend_id}>"
    
class Saving(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='savings')

class Gift(db.Model):
    __tablename__ = "gift"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # ギフトを送ったユーザー
    gift_name = db.Column(db.String(100), nullable=False)
    sent_at = db.Column(db.DateTime, default=None)
    current_owner_id = db.Column(db.Integer, nullable=True)  # 現在の所有者

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())