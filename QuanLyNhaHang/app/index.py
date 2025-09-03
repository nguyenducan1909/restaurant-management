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

@app.get("/cart/<int:restaurant_id>")
def show_cart(restaurant_id):
    user_id = (current_user.id if getattr(current_user, "is_authenticated", False)
               else session.get("user_id") or 1)
    r = dao.get_restaurant_by_id(restaurant_id)
    if not r:
        flash("Không tìm thấy nhà hàng", "danger")
        return redirect(url_for("restaurant_list"))
    cart, items, total = dao.get_active_cart_detail(user_id, restaurant_id)
    return render_template("cart_show.html", r=r, cart=cart, rows=items, total=total)

@app.post("/cart/update")
def update_cart():
    try:
        restaurant_id = int(request.form.get("restaurant_id", "0"))
        item_id = int(request.form.get("item_id", "0"))
        qty = int(request.form.get("quantity", "1"))
        cart_id = int(request.form.get("cart_id", "0"))
    except ValueError:
        flash("Dữ liệu không hợp lệ", "danger")
        return redirect(url_for("show_cart", restaurant_id=request.form.get("restaurant_id", 0)))

    ok, msg = dao.update_cart_item_quantity(cart_id, item_id, qty)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("show_cart", restaurant_id=restaurant_id))

@app.post("/cart/remove")
def remove_from_cart():
    try:
        restaurant_id = int(request.form.get("restaurant_id", "0"))
        item_id = int(request.form.get("item_id", "0"))
        cart_id = int(request.form.get("cart_id", "0"))
    except ValueError:
        flash("Dữ liệu không hợp lệ", "danger")
        return redirect(url_for("show_cart", restaurant_id=request.form.get("restaurant_id", 0)))

    ok, msg = dao.remove_item_from_cart(cart_id, item_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("show_cart", restaurant_id=restaurant_id))

# ----------------
# CHECKOUT
# ----------------
@app.get("/checkout/<int:restaurant_id>")
def checkout_form(restaurant_id):
    user_id = (current_user.id if getattr(current_user, "is_authenticated", False)
               else session.get("user_id") or 1)
    r = dao.get_restaurant_by_id(restaurant_id)
    if not r:
        flash("Không tìm thấy nhà hàng", "danger")
        return redirect(url_for("restaurant_list"))
    cart, items, total = dao.get_active_cart_detail(user_id, restaurant_id)
    if not items:
        flash("Giỏ hàng đang trống", "warning")
        return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id))
    return render_template("checkout.html", r=r, cart=cart, rows=items, total=total)

@app.post("/checkout/<int:restaurant_id>")
def checkout_submit(restaurant_id):
    user_id = (current_user.id if getattr(current_user, "is_authenticated", False)
               else session.get("user_id") or 1)
    ship_name = (request.form.get("ship_name") or "").strip()
    ship_phone = (request.form.get("ship_phone") or "").strip()
    ship_address = (request.form.get("ship_address") or "").strip()
    payment_method = request.form.get("payment_method") or "COD"

    if not ship_name or not ship_phone or not ship_address:
        flash("Vui lòng nhập đầy đủ thông tin giao hàng", "danger")
        return redirect(url_for("checkout_form", restaurant_id=restaurant_id))

    ok, msg, order = dao.create_order_from_cart(
        user_id, restaurant_id, ship_name, ship_phone, ship_address, payment_method
    )
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("checkout_form", restaurant_id=restaurant_id))

    if payment_method == "BANK":
        return redirect(url_for("bank_transfer", order_id=order.id))
    elif payment_method != "COD":
        return redirect(url_for("mock_payment", order_id=order.id, method=payment_method))
    else:
        return redirect(url_for("order_result", order_id=order.id, status="success"))

# ----------------
# PAYMENT MOCK GATEWAY
# ----------------
@app.get("/mockpay")
def mock_payment():
    order_id = request.args.get("order_id", type=int)
    method = request.args.get("method", default="CARD")
    if not order_id:
        flash("Thiếu mã đơn hàng", "danger")
        return redirect(url_for("restaurant_list"))
    return render_template("payment_gateway.html", order_id=order_id, method=method)

@app.get("/payment/callback")
def payment_callback():
    order_id = request.args.get("order_id", type=int)
    result = request.args.get("result", default="success")  # success | fail
    ok, _ = dao.update_payment_result(order_id, result)
    status = "success" if ok and result == "success" else "fail"
    return redirect(url_for("order_result", order_id=order_id, status=status))

# ----------------
# ORDER RESULT
# ----------------
@app.get("/orders/<int:order_id>/result")
def order_result(order_id):
    status = request.args.get("status", "success")
    return render_template("order_result.html", order_id=order_id, status=status)
# ----------------
# BANK TRANSFER MOCK PAGE
# ----------------
@app.get("/bankpay")
def bank_transfer():
    order_id = request.args.get("order_id", type=int)
    if not order_id:
        flash("Thiếu mã đơn hàng", "danger")
        return redirect(url_for("restaurant_list"))
    order, payment = dao.get_payment_info(order_id)
    if not order or not payment:
        flash("Không tìm thấy đơn hàng hoặc thanh toán", "danger")
        return redirect(url_for("restaurant_list"))
    if str(payment.method) != "BANK":
        # Nếu không phải BANK thì đưa về mockpay chung
        return redirect(url_for("mock_payment", order_id=order_id, method=str(payment.method)))
    return render_template("bank_transfer.html", order=order, payment=payment)


if __name__ == "__main__":
    app.run(debug=True)
