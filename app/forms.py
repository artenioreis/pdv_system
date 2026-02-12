from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User, Product

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Nível de Permissão', choices=[('vendas', 'Vendas'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está em uso. Por favor, escolha outro.')

class ProductForm(FlaskForm):
    name = StringField('Nome do Produto', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição')
    price = DecimalField('Preço de Venda (R$)', validators=[DataRequired(), NumberRange(min=0.01)])
    cost_price = DecimalField('Preço de Custo (R$)', default=0.00, validators=[NumberRange(min=0.00)])
    stock = IntegerField('Quantidade em Estoque', validators=[DataRequired(), NumberRange(min=0)])
    barcode = StringField('Código de Barras / SKU', validators=[Length(max=50)])
    unit = StringField('Unidade de Medida', default='unidade', validators=[DataRequired(), Length(max=20)])
    image = FileField('Imagem do Produto', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Salvar Produto')

class CompanySettingsForm(FlaskForm):
    name = StringField('Nome da Empresa', validators=[DataRequired(), Length(max=100)])
    address = StringField('Endereço da Empresa', validators=[DataRequired(), Length(max=200)])
    logo = FileField('Logotipo da Empresa', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Salvar Configurações')
