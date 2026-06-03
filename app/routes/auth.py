from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    last_name = request.form.get('last_name', '').strip()
    first_name = request.form.get('first_name', '').strip()
    patronymic = request.form.get('patronymic', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not all([last_name, first_name, email, password]):
        flash('Заполните все обязательные поля.', 'error')
        return redirect(url_for('main.index'))
    
    if len(password) < 6:
        flash('Пароль должен содержать минимум 6 символов.', 'error')
        return redirect(url_for('main.index'))


    if User.query.filter_by(email=email).first():
        flash('Пользователь с такой почтой уже существует.', 'error')
        return redirect(url_for('main.index'))

    new_user = User(
        last_name=last_name,
        first_name=first_name,
        patronymic=patronymic,
        email=email,
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    session['user_id'] = new_user.id
    session['user_name'] = f"{first_name} {last_name}"
    flash('Регистрация успешна!', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['user_name'] = f"{user.first_name} {user.last_name}"
        flash('Вы успешно вошли.', 'success')
        return redirect(url_for('auth.profile'))
    
    flash('Неверная почта или пароль.', 'error')
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return render_template('profile.html', user=None)
        
    user = db.session.get(User, user_id)
    return render_template('profile.html', user=user)