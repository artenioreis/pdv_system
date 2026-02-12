from flask import render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.forms import LoginForm, RegistrationForm, ProductForm, CompanySettingsForm
from app.models import User, Product, Sale, SaleItem, CompanySettings
from functools import wraps
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Decorator para verificar permissão de admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'vendas':
        return redirect(url_for('pdv'))

    # Lógica para coletar dados do dashboard
    total_sales_today = db.session.query(db.func.sum(Sale.total_amount)).filter(
        db.func.date(Sale.sale_date) == datetime.utcnow().date()
    ).scalar() or 0

    total_items_sold_today = db.session.query(db.func.sum(SaleItem.quantity)).join(Sale).filter(
        db.func.date(Sale.sale_date) == datetime.utcnow().date()
    ).scalar() or 0

    low_stock_products = Product.query.filter(Product.stock < 10, Product.is_active == True).all() # Exemplo: estoque < 10

    # Produtos mais vendidos (exemplo simples, pode ser mais complexo com agrupamento)
    top_selling_products = db.session.query(
        Product.name, db.func.sum(SaleItem.quantity).label('total_quantity')
    ).join(SaleItem).group_by(Product.name).order_by(db.desc('total_quantity')).limit(5).all()

    return render_template('dashboard.html', title='Dashboard',
                           total_sales_today=total_sales_today,
                           total_items_sold_today=total_items_sold_today,
                           low_stock_products=low_stock_products,
                           top_selling_products=top_selling_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'vendas':
            return redirect(url_for('pdv'))
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if user.role == 'vendas':
                return redirect(next_page or url_for('pdv'))
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Nome de usuário ou senha inválidos', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuário {form.username.data} criado com sucesso!', 'success')
        return redirect(url_for('users'))
    return render_template('register.html', title='Registrar Usuário', form=form)

@app.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('users.html', title='Gerenciar Usuários', users=all_users)

@app.route('/products')
@login_required
@admin_required
def products():
    all_products = Product.query.all()
    return render_template('products.html', title='Produtos', products=all_products)

@app.route('/product/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        image_filename = 'default.jpg'
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            image_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        product = Product(name=form.name.data,
                          description=form.description.data,
                          price=form.price.data,
                          cost_price=form.cost_price.data,
                          stock=form.stock.data,
                          barcode=form.barcode.data,
                          unit=form.unit.data,
                          image_filename=image_filename)
        db.session.add(product)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('products'))
    return render_template('create_product.html', title='Novo Produto', form=form)

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    if form.validate_on_submit():
        if form.image.data:
            # Remover imagem antiga se não for a default
            if product.image_filename != 'default.jpg':
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename))
                except OSError:
                    pass # Ignora se o arquivo não existir

            filename = secure_filename(form.image.data.filename)
            image_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            product.image_filename = image_filename

        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.cost_price = form.cost_price.data
        product.stock = form.stock.data
        product.barcode = form.barcode.data
        product.unit = form.unit.data
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('products'))
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        form.cost_price.data = product.cost_price
        form.stock.data = product.stock
        form.barcode.data = product.barcode
        form.unit.data = product.unit
    return render_template('create_product.html', title='Editar Produto', form=form, product=product)

@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Em vez de deletar, podemos desativar o produto
    product.is_active = False
    db.session.commit()
    flash('Produto desativado com sucesso!', 'info')
    return redirect(url_for('products'))

@app.route('/pdv', methods=['GET', 'POST'])
@login_required
def pdv():
    # Lógica para o PDV
    # - Busca de produtos (pode ser via AJAX)
    # - Adicionar/remover itens do carrinho (sessão ou JS no frontend)
    # - Finalizar venda, processar pagamento, atualizar estoque
    # - Gerar cupons (HTML para impressão)

    # Exemplo de busca de produto via AJAX (GET request)
    if request.method == 'GET' and 'search_query' in request.args:
        search_query = request.args.get('search_query')
        products_found = Product.query.filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Product.barcode.ilike(f'%{search_query}%'))
        ).filter_by(is_active=True).limit(10).all()
        # Retornar JSON com os produtos encontrados
        return {'products': [{'id': p.id, 'name': p.name, 'price': p.price, 'stock': p.stock, 'barcode': p.barcode} for p in products_found]}

    # Lógica para finalizar a venda (POST request)
    if request.method == 'POST':
        cart_items = request.json.get('cart_items') # Espera uma lista de {'product_id': X, 'quantity': Y}
        payment_method = request.json.get('payment_method')
        total_amount = request.json.get('total_amount')

        if not cart_items or not payment_method or not total_amount:
            return {'status': 'error', 'message': 'Dados da venda incompletos.'}, 400

        # Obter configurações da empresa para o cupom
        company_settings = CompanySettings.query.first()
        company_name = company_settings.name if company_settings else 'Empresa PDV'
        company_address = company_settings.address if company_settings else 'Endereço Padrão'
        company_logo = company_settings.logo_filename if company_settings else None

        new_sale = Sale(
            user_id=current_user.id,
            total_amount=total_amount,
            payment_method=payment_method,
            company_name=company_name,
            company_address=company_address,
            company_logo=company_logo,
            is_completed=True
        )
        db.session.add(new_sale)
        db.session.flush() # Para ter acesso ao new_sale.id antes do commit

        coupons_data = [] # Para armazenar os dados de cada cupom individual

        for item_data in cart_items:
            product = Product.query.get(item_data['product_id'])
            if not product or product.stock < item_data['quantity']:
                db.session.rollback()
                return {'status': 'error', 'message': f'Estoque insuficiente para {product.name}.'}, 400

            sale_item = SaleItem(
                sale_id=new_sale.id,
                product_id=product.id,
                quantity=item_data['quantity'],
                price_at_sale=product.price,
                total_item_price=product.price * item_data['quantity']
            )
            db.session.add(sale_item)

            # Atualiza o estoque
            product.stock -= item_data['quantity']

            # Geração de dados para cupons individuais (conforme sua solicitação)
            for _ in range(item_data['quantity']):
                coupons_data.append({
                    'company_name': company_name,
                    'company_address': company_address,
                    'company_logo': company_logo,
                    'product_name': product.name,
                    'product_price': product.price,
                    'sale_date': new_sale.sale_date.strftime('%d/%m/%Y %H:%M:%S'),
                    'seller_name': current_user.username,
                    'payment_method': payment_method,
                    'total_sale_amount': total_amount # O total da venda ainda é o total, mesmo que o cupom seja por item
                })

        db.session.commit()
        flash('Venda finalizada com sucesso!', 'success')
        return {'status': 'success', 'message': 'Venda finalizada!', 'coupons': coupons_data}, 200

    return render_template('pdv.html', title='PDV')

@app.route('/reports')
@login_required
@admin_required
def reports():
    # Lógica para relatórios de vendas e estoque
    # Exemplo: Vendas por método de pagamento
    sales_by_payment = db.session.query(
        Sale.payment_method, db.func.sum(Sale.total_amount).label('total_value')
    ).group_by(Sale.payment_method).all()

    # Exemplo: Vendas por vendedor
    sales_by_seller = db.session.query(
        User.username, db.func.sum(Sale.total_amount).label('total_value'), db.func.count(Sale.id).label('total_sales')
    ).join(Sale).group_by(User.username).all()

    # Exemplo: Estoque atual
    current_stock = Product.query.filter_by(is_active=True).order_by(Product.name).all()

    return render_template('reports.html', title='Relatórios',
                           sales_by_payment=sales_by_payment,
                           sales_by_seller=sales_by_seller,
                           current_stock=current_stock)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    company_settings = CompanySettings.query.first()
    if not company_settings:
        company_settings = CompanySettings(name='Nome da Empresa', address='Endereço da Empresa')
        db.session.add(company_settings)
        db.session.commit()

    form = CompanySettingsForm()
    if form.validate_on_submit():
        if form.logo.data:
            # Remover logo antiga se existir e não for a default
            if company_settings.logo_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], company_settings.logo_filename))
                except OSError:
                    pass

            filename = secure_filename(form.logo.data.filename)
            logo_filename = f"logo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            form.logo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
            company_settings.logo_filename = logo_filename

        company_settings.name = form.name.data
        company_settings.address = form.address.data
        db.session.commit()
        flash('Configurações da empresa atualizadas com sucesso!', 'success')
        return redirect(url_for('settings'))
    elif request.method == 'GET':
        form.name.data = company_settings.name
        form.address.data = company_settings.address
    return render_template('settings.html', title='Configurações da Empresa', form=form, company_settings=company_settings)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
