from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_user, logout_user, login_required
from QuanLyNhaHang.app import app, dao

# ======================
# HOME
# ======================
@app.route("/")
def index():
    return redirect(url_for("restaurant_list"))

# ======================
# RESTAURANTS & MENU
# ======================
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

# ======================
# CART
# ======================
@app.post("/cart/add")
def add_to_cart():
    try:
        restaurant_id = int(request.form.get("restaurant_id", "0"))
        item_id = int(request.form.get("item_id", "0"))
        qty = max(1, int(request.form.get("quantity", "1")))
    except (TypeError, ValueError):
        flash("Dữ liệu không hợp lệ", "danger")
        rid = request.form.get("restaurant_id") or 0
        return redirect(url_for("restaurant_detail", restaurant_id=rid))

    # demo fallback user_id=1 nếu chưa login
    user_id = (current_user.id if getattr(current_user, "is_authenticated", False)
               else session.get("user_id") or 1)

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
    except (TypeError, ValueError):
        flash("Dữ liệu không hợp lệ", "danger")
        rid = request.form.get("restaurant_id") or 0
        return redirect(url_for("show_cart", restaurant_id=rid))

    ok, msg = dao.update_cart_item_quantity(cart_id, item_id, qty)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("show_cart", restaurant_id=restaurant_id))

@app.post("/cart/remove")
def remove_from_cart():
    try:
        restaurant_id = int(request.form.get("restaurant_id", "0"))
        item_id = int(request.form.get("item_id", "0"))
        cart_id = int(request.form.get("cart_id", "0"))
    except (TypeError, ValueError):
        flash("Dữ liệu không hợp lệ", "danger")
        rid = request.form.get("restaurant_id") or 0
        return redirect(url_for("show_cart", restaurant_id=rid))

    ok, msg = dao.remove_item_from_cart(cart_id, item_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("show_cart", restaurant_id=restaurant_id))

# ======================
# AUTH
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("restaurant_list"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        if not username or not password:
            flash("Vui lòng nhập đầy đủ thông tin", "danger")
            return render_template("auth/login.html")

        success, result = dao.authenticate_user(username, password)
        if success:
            login_user(result, remember=remember)
            flash(f"Chào mừng {result.full_name or result.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("restaurant_list"))
        else:
            flash(result, "danger")

    return render_template("auth/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("restaurant_list"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        full_name = (request.form.get("full_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        # Validation cơ bản
        if not all([username, email, password, confirm_password]):
            flash("Vui lòng nhập đầy đủ thông tin bắt buộc", "danger")
            return render_template("auth/register.html")
        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp", "danger")
            return render_template("auth/register.html")
        if len(password) < 6:
            flash("Mật khẩu phải có ít nhất 6 ký tự", "danger")
            return render_template("auth/register.html")

        success, result = dao.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name or None,
            phone=phone or None
        )
        if success:
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("login"))
        else:
            flash(result, "danger")

    return render_template("auth/register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Đã đăng xuất thành công", "success")
    return redirect(url_for("restaurant_list"))

# ======================
# CHECKOUT
# ======================
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

    # Chuẩn hóa payment_method về 1 trong 4 enum: COD, CARD, EWALLET, BANK
    raw_method = (request.form.get("payment_method") or "COD").strip().upper()
    payment_method = raw_method if raw_method in {"COD", "CARD", "EWALLET", "BANK"} else "CARD"

    if not ship_name or not ship_phone or not ship_address:
        flash("Vui lòng nhập đầy đủ thông tin giao hàng", "danger")
        return redirect(url_for("checkout_form", restaurant_id=restaurant_id))

    ok, msg, order = dao.create_order_from_cart(
        user_id, restaurant_id, ship_name, ship_phone, ship_address, payment_method
    )
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("checkout_form", restaurant_id=restaurant_id))

    # Điều hướng theo phương thức thanh toán
    if payment_method == "BANK":
        return redirect(url_for("bank_transfer", order_id=order.id))
    elif payment_method != "COD":
        return redirect(url_for("mock_payment", order_id=order.id, method=payment_method))
    else:
        return redirect(url_for("order_result", order_id=order.id, status="success"))

# ======================
# PAYMENT MOCK GATEWAY
# ======================
@app.get("/mockpay")
def mock_payment():
    order_id = request.args.get("order_id", type=int)
    method = request.args.get("method", default="CARD")
    if not order_id:
        flash("Thiếu mã đơn hàng", "danger")
        return redirect(url_for("restaurant_list"))
    # trang giả lập cổng thanh toán
    return render_template("payment_gateway.html", order_id=order_id, method=method)

@app.get("/payment/callback")
def payment_callback():
    order_id = request.args.get("order_id", type=int)
    result = request.args.get("result", default="success")  # "success" | "fail"
    ok, _ = dao.update_payment_result(order_id, result)
    status = "success" if ok and result == "success" else "fail"
    return redirect(url_for("order_result", order_id=order_id, status=status))

# ======================
# ORDER RESULT
# ======================
@app.get("/orders/<int:order_id>/result")
def order_result(order_id):
    status = request.args.get("status", "success")
    return render_template("order_result.html", order_id=order_id, status=status)

# ======================
# BANK TRANSFER (mock)
# ======================
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

    # Ở models: Payment.method là Enum string -> so sánh trực tiếp với "BANK"
    if payment.method != "BANK":
        # nếu không phải chuyển khoản ngân hàng thì đẩy về mockpay chung
        return redirect(url_for("mock_payment", order_id=order_id, method=payment.method))

    return render_template("bank_transfer.html", order=order, payment=payment)

# ======================
# DEV ENTRY
# ======================
if __name__ == "__main__":
    app.run(debug=True)
