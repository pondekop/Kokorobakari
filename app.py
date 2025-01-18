from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Gift, Friendship, Transaction
from config import Config
from datetime import datetime
from functools import wraps
from flask_migrate import Migrate

app = Flask(__name__, static_folder='./templates/images')
app.secret_key = 'your_secret_key'  # セッションに必要な秘密鍵を設定
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/Kokorobakari'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

# ログインユーザーのローダー
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def root():
    # 既にログインしている場合はindexページにリダイレクト
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    # ログインしていない場合はlogin_pageにリダイレクト
    return redirect(url_for("login_page"))

@app.route("/index")
@login_required
def index():
    return render_template("index.html", user=current_user)

@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        if User.query.filter_by(email=email).first():
            flash("このメールアドレスは既に登録されています。")
            return redirect(url_for("create_user"))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("ユーザー登録が完了しました。ログインしてください。")
        return redirect(url_for("login_page"))
    return render_template("create_user.html")

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)  # ユーザーをログイン状態にする
            flash("ログインに成功しました。")
            print("ログイン成功:", current_user.is_authenticated)  # ログイン状態を確認
            return redirect(url_for("index"))  # ログイン成功後、indexページにリダイレクト
        else:
            flash("メールアドレスまたはパスワードが間違っています。")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    flash("ログアウトしました。")
    return redirect(url_for("login_page"))

@app.route("/add_transaction", methods=["GET", "POST"])
@login_required
def add_transaction_page():
    if request.method == "POST":
        amount = int(request.form.get("amount"))
        rounding_option = int(request.form.get("rounding_option"))  # 端数設定を取得

        # 選択された端数設定で切り上げ
        rounded_amount = (amount + (rounding_option - 1)) // rounding_option * rounding_option
        fractional_amount = rounded_amount - amount

        # 取引を保存
        transaction = Transaction(user_id=current_user.id, amount=amount, date=datetime.now())
        db.session.add(transaction)

        # ユーザーの貯金額を更新
        current_user.balance += fractional_amount
        db.session.commit()

        # Successページにリダイレクト
        return render_template("success.html", user=current_user, amount=fractional_amount)

    return render_template("add_transaction.html")

@app.route("/add_friend", methods=["GET", "POST"])
@login_required
def add_friend():
    if request.method == "POST":
        friend_registration_id = request.form.get("friend_registration_id")
        friend = User.query.filter_by(registration_id=friend_registration_id).first()

        if not friend:
            flash("指定されたIDのユーザーが見つかりません。")
            return redirect(url_for("add_friend"))

        if friend.id == current_user.id:
            flash("自分自身を友達に追加することはできません。")
            return redirect(url_for("add_friend"))

        # 既に友達かチェック
        existing_friendship = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend.id).first()
        if existing_friendship:
            flash("このユーザーは既に友達に追加されています。")
            return redirect(url_for("add_friend"))

        # 友達関係を保存
        friendship = Friendship(user_id=current_user.id, friend_id=friend.id)
        db.session.add(friendship)
        db.session.commit()

        flash(f"{friend.name} さんを友達に追加しました！")
        return redirect(url_for("add_friend"))

    return render_template("add_friend.html", user=current_user)

@app.route("/view_savings")
@login_required
def view_savings_page():
    users = User.query.all()  # If you want all users displayed
    return render_template("view_savings.html", users=users, user=current_user)

@app.route("/send_gift", methods=["GET", "POST"])
@login_required
def send_gift_page():
    if request.method == "POST":
        receiver_id = int(request.form.get("receiver"))
        gift_option = request.form.get("gift_option")  # ギフトの選択肢

        receiver = User.query.get(receiver_id)

        if not receiver:
            flash("選択された受信者が見つかりません。")
            return redirect(url_for("send_gift_page"))

        if receiver_id == current_user.id:
            flash("自分自身にギフトを送ることはできません。")
            return redirect(url_for("send_gift_page"))

        # ギフト送信処理
        gift = Gift(
            user_id=current_user.id,
            gift_name=gift_option,
            sent_at=datetime.now(),
            current_owner_id=receiver_id
        )
        db.session.add(gift)
        db.session.commit()

        flash(f"{receiver.name} さんに {gift_option} のギフトを送りました！")
        return redirect(url_for("send_gift_page"))

    # ログインユーザーの友達リストを取得
    friends = Friendship.query.filter_by(user_id=current_user.id).all()
    friend_users = [User.query.get(friend.friend_id) for friend in friends]

    return render_template("send_gift.html", user=current_user, friends=friend_users)

@app.route("/gift_history")
@login_required
def gift_history_page():
    # 全ユーザーを取得
    users = {user.id: user for user in User.query.all()}
    current_gifts = {}

    # すべてのギフト履歴を取得
    gifts = Gift.query.all()
    for gift in gifts:
        # ギフト名を取得（「chocolateのギフトを～」→「chocolate」）
        gift_name = gift.gift_name.split("の")[0]

        # ギフトの現在の所有者を取得
        owner = users.get(gift.current_owner_id)
        if owner:
            if owner.id not in current_gifts:
                current_gifts[owner.id] = []
            current_gifts[owner.id].append(gift_name)

    return render_template("gift_history.html", current_gifts=current_gifts, users=users)
