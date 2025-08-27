from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Cấu hình database (chỉnh lại user/pass cho đúng)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:123456@localhost:3306/foodhub_demo?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # =================
    # Models
    # =================
    class Restaurant(db.Model):
        __tablename__ = "restaurants"
        id = db.Column(db.BigInteger, primary_key=True)
        owner_id = db.Column(db.BigInteger, nullable=False)
        name = db.Column(db.String(191), nullable=False)
        address = db.Column(db.String(255))
        phone = db.Column(db.String(30))
        is_open = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp())

    # =================
    # Routes
    # =================
    @app.route("/")
    def home():
        return restaurant_list()

    @app.route("/restaurants")
    def restaurant_list():
        q = request.args.get("q", "")
        is_open = request.args.get("is_open")

        query = Restaurant.query
        if q:
            like = f"%{q.strip()}%"
            query = query.filter(
                or_(Restaurant.name.ilike(like), Restaurant.address.ilike(like))
            )
        if is_open in ("0", "1"):
            query = query.filter(Restaurant.is_open == bool(int(is_open)))

        restaurants = query.order_by(Restaurant.created_at.desc()).all()
        return render_template("restaurants_index.html", restaurants=restaurants, q=q, is_open=is_open)

    @app.route("/restaurants/<int:restaurant_id>")
    def restaurant_detail(restaurant_id):
        r = Restaurant.query.get_or_404(restaurant_id)
        return render_template("restaurant_show.html", r=r)

    return app
