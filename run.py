from app import app, db
from app.models import User, Product, CompanySettings
from werkzeug.security import generate_password_hash

@app.cli.command('init-db')
def init_db_command():
    """Inicializa o banco de dados e cria o usuário admin padrão."""
    db.create_all()
    print('Banco de dados inicializado.')

    # Cria o usuário admin padrão se não existir
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@pdv.com', role='admin')
        admin_user.set_password('admin') # Senha padrão 'admin'
        db.session.add(admin_user)
        print('Usuário admin padrão criado.')

    # Cria configurações da empresa padrão se não existir
    if not CompanySettings.query.first():
        default_settings = CompanySettings(name='Minha Empresa PDV', address='Rua Exemplo, 123, Cidade - UF')
        db.session.add(default_settings)
        print('Configurações da empresa padrão criadas.')

    db.session.commit()
    print('Dados iniciais commitados.')

if __name__ == '__main__':
    app.run(debug=True)
