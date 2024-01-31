from flask import Flask, render_template, request, session, redirect, url_for
from db import Database
from base64 import b64encode
import re


app = Flask(__name__)
app.secret_key = '1KMsm112KMI8Fd45v8bvr56878mnc5XXZcV8878'

@app.route("/show_cart_items", methods=["POST"])
def show_cart_items():
    if request.method == "POST":
        db = Database("shop.db")
        action = request.form.get("action")
        if request.form.get('count') != "":
            items_count = int(request.form.get("count"))
        else:
            items_count=1
        if action == "+":
            items_count += 1
        elif action == "-":
            if items_count == 1:
                items_count == 1
            else:
                items_count -= 1
        else:
            items_count=1
        isActive = int(request.form.get("isActive"))
        if items_count > isActive:
            items_count = isActive
        cart_id = request.form.get("cart_id")
        db.update_carts_count(cart_id, items_count)
        
    return redirect(url_for("show_cart")) 


@app.route("/show_cart")
def show_cart():
    surname = session.get("surname")
    email = session.get("email")
    name = session.get("name")
    params = {"is_authenticated": session.get("is_authenticated")}
    if not params["is_authenticated"]:
        return redirect(url_for("register"))
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    db = Database("shop.db")
    cart_items = db.get_cart_items(user_id)  

    total_price = 0
    if cart_items:  
        for item in cart_items:
            if item[5] is not None:
                total_price += item[4] * item[5]
    else:
        total_price = 0 

    cart_items_with_images = []
    for item in cart_items:
        image = b64encode(item[1]).decode('utf-8')
        cart_items_with_images.append({
            'id': item[0],
            'title': item[2],
            'price': item[4],
            'image': image,
            'items_count': item[5],
            'carts_id': item[6],
            'isActive': item[7]
        })

    return render_template('cart.html', cart_items=cart_items_with_images, total_price=total_price, is_active_values=[item[4] for item in cart_items], name=name, surname=surname, email=email)


@app.route("/place_order", methods=["POST"])
def place_order():
    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]
    comment = request.form.get("comment", "")
    user_id = session.get("user_id")
    db = Database("shop.db")
    items_id = db.get_all_items_id_cart(user_id)

    total_price = request.form["total_price"]
    buy = db.insert_buyer(name, phone, email, comment, total_price, user_id)
    for item_id in items_id:
        db.cursor.execute("INSERT INTO buyers_items (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
    db.conn.commit()

    db.remove_from_cart(user_id)

    return redirect(url_for("show_cart", buy=buy))


@app.route("/remove_from_cart/<int:item_id>", methods=["GET"])
def remove_from_cart(item_id):
    user_id = session.get("user_id")

    db = Database("shop.db")
    db.cursor.execute("DELETE FROM carts WHERE user_id=? AND item_id=?", (user_id, item_id))
    db.conn.commit()

    return redirect(url_for("show_cart"))  



@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    item_id = request.form.get("itemId")
    # Перевірка авторизації
    if not session.get("is_authenticated"):
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Перевірка, чи є такий товар вже в кошику
    db = Database("shop.db")
    db.cursor.execute("SELECT * FROM carts WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    items = db.cursor.fetchall()

    if items:
        # Товар уже є в кошику
        return redirect(url_for("drone", id=item_id))

    # Додавання товару в кошик
    db.cursor.execute("INSERT INTO carts (user_id, item_id, items_count) VALUES (?, ?, 1)", (user_id, item_id))
    db.conn.commit()

    return redirect(url_for("drone", id=item_id))


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        users_level = 1

        if not name or not surname or not email or not password:
            return render_template('register.html', error='Всі поля повинні бути заповнені')
        if not re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+', email):
            return render_template('register.html', error='Некоректний формат електронної пошти')
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.{8,})', password):
            return render_template('register.html', error='Пароль повинен містити принаймні 8 символів, принаймні одну велику літеру, принаймні одну малу літеру та принаймні одну цифру')
        db = Database("shop.db")

        if not db.check_email(email):
            db.insert_user(name, surname, email, password, users_level)
            user_id = db.cursor.lastrowid

            session["user_id"] = user_id
            session["is_authenticated"] = True
            session["name"] = name
            session["surname"] = surname
            session["email"] = email
            session["user_level"] = users_level


            return redirect(url_for("home"))
        else:
            return render_template('register.html', error='Акаунт з такою поштою вже існує')
    else:
        return render_template('register.html')



@app.route("/logout")
def logout():
    session["is_authenticated"] = False
    session.pop("name")
    session.pop("surname")
    session.pop("email")
    return redirect(url_for("home"))

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    password = request.form["password"]

    db = Database("shop.db")
    user = db.check_user_credentials(email, password) 
    if user:
        session["user_id"] = user[0]  
        session["is_authenticated"] = True
        session["name"] = user[1]
        session["surname"] = user[2]
        session["email"] = user[3]

        query = "SELECT users_level FROM users WHERE id = ?"
        db.cursor.execute(query, (user[0],))
        user_level = db.cursor.fetchone()[0]
        session["user_level"] = user_level

        return redirect(url_for("home"))
    else:
        return render_template("login.html", error="Неправильний email або пароль")

@app.route("/")
def home():
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")

    if not session.get("is_authenticated"):
        cart_items_with_images = []  
    else:
        db = Database("shop.db")
        user_id = session.get("user_id")
        cart_items = db.get_buyers_items(user_id)

        cart_items_with_images = []
        for item in cart_items:
            image = b64encode(item[0]).decode('utf-8')
            status = item[1]  
            cart_items_with_images.append({
                'image': image,
                'status': status,  
            })

    return render_template('index.html',cart_items=cart_items_with_images, scripts=['static/js/main.js', 'static/js/wow.min.js'], name=name, surname=surname, email=email)

@app.route("/about")
def about():
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")
    return render_template('about.html', name=name, surname=surname, email=email)

@app.route("/delivery")
def delivery():
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")
    return render_template('delivery.html', name=name, surname=surname, email=email)

@app.route("/consultation")
def consultation():
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")
    return render_template('consultation.html', name=name, surname=surname, email=email)

@app.route("/contact")
def contact():
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")
    return render_template('contact.html', name=name, surname=surname, email=email)


@app.route("/dronList", methods=["GET"])
def dronList():
    params = {"is_authenticated": session.get("is_authenticated")}
    category = request.args.get("category")
    sort_by = request.args.get("sort_by")
    if not params["is_authenticated"]:
        return redirect(url_for("register"))
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")
    db = Database("shop.db")
    items_with_images = []

    
    if category:
        if sort_by == "price_asc":
            items = db.get_items_by_category_and_type(category, "дрон", order_by="price ASC")
        elif sort_by == "price_desc":
            items = db.get_items_by_category_and_type(category, "дрон", order_by="price DESC")
        else:
            items = db.get_items_by_category_and_type(category, "дрон")
    else:
        if sort_by == "price_asc":
            items = db.get_items_by_type("дрон", order_by="price ASC")
        elif sort_by == "price_desc":
            items = db.get_items_by_type("дрон", order_by="price DESC")
        else:
            items = db.get_items_by_type("дрон") 


    if items:
        for item in items:
            image = b64encode(item[1]).decode('utf-8')
            items_with_images.append({
                'id': item[0],
                'title': item[2],
                'price': item[4],
                'image': image,
            })

    return render_template('dronList.html', category=category, items=items_with_images,  name=name, surname=surname, email=email)


@app.route("/pultList", methods=["GET"])
def pultList():
    params = {"is_authenticated": session.get("is_authenticated")}
    category = request.args.get("category")
    if not params["is_authenticated"]:
        return redirect(url_for("register"))
    name = session.get("name")
    surname = session.get("surname")
    email = session.get("email")
    db = Database("shop.db")

    items_with_images = []
    
    items = db.get_items_by_type("пульт")

    sort_by = request.args.get("sort_by")
    if sort_by == "price_asc":
        items = db.get_items_by_type("пульт", order_by="price ASC")
    elif sort_by == "price_desc":
        items = db.get_items_by_type("пульт", order_by="price DESC")
    else:
        items = db.get_items_by_type("пульт") 

    if items:
        for item in items:
            image = b64encode(item[1]).decode('utf-8')
            items_with_images.append({
                'id': item[0],
                'title': item[2],
                'price': item[4],
                'image': image,
            })

    return render_template('pultList.html', category=category, items=items_with_images,  name=name, surname=surname, email=email)

@app.route("/drone/<int:id>")
def drone(id):
    params = {"is_authenticated": session.get("is_authenticated")}
    session["previous_url"] = request.headers.get("Referer")
    if not params["is_authenticated"]:
        return redirect(url_for("register"))
    name = session.get("name")
    db = Database("shop.db")
    item = db.get_item_by_id(id)

    if item:
        image = b64encode(item[1]).decode('utf-8')
        item_data = {
            'id': item[0],
            'title': item[2],
            'about': item[3],  
            'price': item[4],
            'isActive': item[5],
            'image': image,
        }
        return render_template('drone.html', item=item_data, name=name)
    else:
        return render_template('drone.html', error='Дрон не знайдено', name=name)

@app.route("/back")
def back():
    previous_url = session.get("previous_url")
    if previous_url:
        return redirect(previous_url)

    return redirect(url_for("home"))

@app.route("/admin", methods=['POST', 'GET'])
def admin():
        params = {"is_authenticated": session.get("is_authenticated")}
        if not params["is_authenticated"]:
            return redirect(url_for("register"))
        user_level = session.get("user_level")
        if user_level != 2:
            return redirect(url_for("home"))
        name = session.get("name")
        if request.method == 'POST':
            img = request.files['img']
            title = request.form['title']
            about = request.form['about']
            price = request.form['price']
            isActive = request.form.get('isActive')
            category = request.form['category']
            type = request.form['type']
            
            db = Database("shop.db")

            if not title or not about or not price or not isActive or not category or not type:
                return render_template('admin.html', error='Всі поля повинні бути заповнені')
            img_bytes = img.read()
            db.insert_item(img_bytes, title, about, price, isActive, category, type)

            return render_template('index.html', name=name)  
        else: 
            items_with_images = []
            buyer_item = []
            db = Database("shop.db")
            items = db.get_all_items()
            buyers = db.get_all_buyers()
            cart_items = db.get_buyers_all_items()

            cart_items_with_images = []
            for item in cart_items:
                image = b64encode(item[0]).decode('utf-8')
                status = item[3] 
                user_id = item[1]
                item_id = item[2]  
                cart_items_with_images.append({
                    'image': image,
                    'user_id': user_id,
                    'item_id': item_id,
                    'status': status,  
                })

            if items:
                for item in items:
                    image = b64encode(item[1]).decode('utf-8')
                    items_with_images.append({
                        'id': item[0],
                        'title': item[2],
                        'about': item[3],
                        'price': item[4],
                        'isActive': item[5],
                        'image': image,
                        'category': item[6],
                    })

            if buyers:
                for buyer in buyers:
                    buyer_item.append({
                        'id': buyer[0],
                        'name': buyer[1],
                        'phone': buyer[2],
                        'email': buyer[3],
                        'comment': buyer[4],
                        'total_price': buyer[5],
                        'user_id': buyer[6]
                    })
            return render_template('admin.html', items=items_with_images, buyers=buyer_item, cart_items=cart_items_with_images,name=name)  
        
@app.route("/admin/delete/<int:item_id>")
def delete_item(item_id):
    db = Database("shop.db")
    db.delete_item_buyers(item_id)  
    return redirect(url_for("admin"))

@app.route("/admin/delete/q/<int:user_id>")
def delete_buyers(user_id):
    db = Database("shop.db")
    db.delete_buyers(user_id)  
    return redirect(url_for("admin"))

@app.route("/search", methods=["GET"])
def search():
    db = Database("shop.db")
    query = request.args.get('query')
    if query:
        items = db.get_items_by_title_like(query)  
    else:
        items = None

    items_with_images = []
    if items:
        for item in items:
            image = b64encode(item[1]).decode('utf-8')
            items_with_images.append({
                'id': item[0],
                'title': item[2],
                'price': item[4],
                'image': image,
            })

    return render_template('dronList.html', items=items_with_images) 


if __name__ == '__main__':
    app.run(debug=True)  
