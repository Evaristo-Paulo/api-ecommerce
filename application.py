from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, current_user, login_user, logout_user, LoginManager, login_required

# INICIAL API
application = Flask(__name__)
# CONFIGUAR AUTENTICAÇÃO
application.config['SECRET_KEY'] = 'wedev.com'
# CONFIGUAR BANCO DE DADOS (ecommerce.db)
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()
db = SQLAlchemy(application)
login_manager.init_app(application)
login_manager.login_view = 'login'
CORS(application)

# MODELAGEM DA BDASE DE DADOS
# User (ID, name, password)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy=True)

# Produto (ID, name, price, description)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

# Produto (ID, name, price, description)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(Product.id), nullable=False)

# DEPOIS DA MODELAGEM, ENTRAR NO FLASK SHELL E RODAR OS COMENADOS
# 1 - flash shell, 2 - db.create_all(), 3 - db.session.commit()
# SQLLITE VIEWER
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@application.route('/api/login', methods=["POST"])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        login_user(user)
        return jsonify({"message": "Logged in successfully"})
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401
    
@application.route('/api/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successfully"})

@application.route('/api/products/add', methods=["POST"])
@login_required
def add_product():
    data = request.json
    
    if 'name' in data and 'price' in data:
        product = Product(name=data['name'], price=data['price'], description=data.get('description', ''))
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product stored successfully"})
    return jsonify({"message": "Invalid product data"}), 400
    
@application.route('/api/products/delete/<int:product_id>', methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)

    if product is not None:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"})
    return jsonify({"message": "Product not found"}), 404

@application.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    product = Product.query.get(product_id)

    if product is not None:
        return jsonify({ 
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description,
        })
    return jsonify({"message": "Product not found"}), 404

@application.route('/api/products/update/<int:product_id>', methods=["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)

    if product is None:
        return jsonify({"message": "Product not found"}), 404

    data = request.json
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']

    if 'description' in data:
        product.description = data['description']
    
    db.session.commit()
    return jsonify({"message": "Product updated successfully"})
    
@application.route('/api/products/', methods=["GET"])
def get_products():
    products = Product.query.all()
    items = list()

    for product in products:
        item = { 
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        items.append(item)

    return jsonify({"Products": items})
 
# CART 
@application.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({
            "user": user.username,
            "product": product.name
            })
    
    return jsonify({"message": "Failed to add item to the cart"}), 400

@application.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": "Item removed from the cart successfully"})
    
    return jsonify({"message": "Failed to remove item from the cart"}), 400

@application.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    
    if cart_items:
        cart_content = list()

        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
            cart_content.append({ 
                "id": cart_item.id,
                "user_id": cart_item.user_id,
                "product_name": product.name,
                "product_price": product.price,
            })
        return jsonify({"Cart": cart_content})
    
    return jsonify({"message": "Unauthorized. User not logged in"}), 401

@application.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    
    if cart_items:
        for cart_item in cart_items:
            db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": "Checkout successful. Cart has been cleared"})
    
    return jsonify({"message": "Unauthorized. User not logged in"}), 401

if __name__ == '__main__':
    application.run(debug=True)