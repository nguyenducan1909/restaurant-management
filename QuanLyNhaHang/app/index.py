# --- YÊU CẦU 2: ROUTES XEM THỰC ĐƠN + THÊM GIỎ HÀNG ---
from urllib import response

from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from QuanLyNhaHang.app import app, dao

@app.route('/')
def index():
    return "hello world"

@app.route("/restaurants")
def restaurant_list():
    q = request.args.get("q", "")
    is_open = request.args.get("is_open")
    restaurants = dao.get_restaurants(q=q, is_open=is_open)
    return render_template("restaurants_index.html", restaurants=restaurants, q=q, is_open=is_open)

@app.route("/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    r = dao.get_restaurant_by_id(restaurant_id)
    if not r:
        flash("Không tìm thấy nhà hàng", "danger")
        return redirect(url_for("restaurant_list"))
    items = dao.get_items_for_restaurant(restaurant_id)
    added_ok = request.args.get("added") == "1"
    return render_template("restaurant_show.html", r=r, items=items, added_ok=added_ok)

@app.post("/cart/add")
def add_to_cart():
    try:
        restaurant_id = int(request.form.get("restaurant_id", "0"))
        item_id = int(request.form.get("item_id", "0"))
        qty = max(1, int(request.form.get("quantity", "1")))
    except ValueError:
        flash("Dữ liệu không hợp lệ", "danger")
        return redirect(url_for("restaurant_detail", restaurant_id=request.form.get("restaurant_id", 0)))

    # Lấy user hiện tại theo login/session (giống pattern của bạn)
    user_id = (current_user.id if getattr(current_user, "is_authenticated", False)
               else session.get("user_id") or 1)  # demo: 1

    ok, msg = dao.add_item_to_cart(user_id, restaurant_id, item_id, qty)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id, added=int(ok)))

if __name__ == "__main__":
    app.run(debug=True)
