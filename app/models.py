from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='vendas') # 'admin' ou 'vendas'
    sales = db.relationship('Sale', backref='seller', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False) # Preço de venda
    cost_price = db.Column(db.Float) # Preço de custo
    stock = db.Column(db.Integer, default=0)
    barcode = db.Column(db.String(50), unique=True) # Código de barras ou SKU
    unit = db.Column(db.String(20), default='unidade') # Ex: unidade, kg, litro
    image_filename = db.Column(db.String(100), default='default.jpg')
    is_active = db.Column(db.Boolean, default=True) # Para desativar produtos sem excluí-los
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False) # Dinheiro, Pix, Cartão
    is_completed = db.Column(db.Boolean, default=False) # Para vendas em andamento
    # Adicionar campos para informações da empresa para o cupom não fiscal
    company_name = db.Column(db.String(100))
    company_address = db.Column(db.String(200))
    company_logo = db.Column(db.String(100)) # Caminho para o logo

    sale_items = db.relationship('SaleItem', backref='sale', lazy=True)

    def __repr__(self):
        return f'<Sale {self.id}>'

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False) # Preço do produto no momento da venda
    total_item_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<SaleItem {self.id}>'

class CompanySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    logo_filename = db.Column(db.String(100))
    # Outras configurações globais podem vir aqui

    def __repr__(self):
        return f'<CompanySettings {self.name}>'
