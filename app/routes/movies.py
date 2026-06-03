# app/routes/movies.py
import os
import uuid
import qrcode
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, abort, jsonify, session, flash, redirect, url_for
from app.models import Movie, Session, Seat, Ticket
from app import db

movies_bp = Blueprint('movies', __name__)

def ensure_rolling_schedule():
    today = datetime.now().date()
    
    oldest_session = Session.query.order_by(Session.session_date.asc()).first()
    
    if oldest_session and oldest_session.session_date < today:
        week_start = oldest_session.session_date
        week_end = week_start + timedelta(days=6)
        
        template_sessions = Session.query.filter(
            Session.session_date >= week_start,
            Session.session_date <= week_end
        ).all()
        
        for ts in template_sessions:
            new_date = ts.session_date + timedelta(days=7)
            
            exists = Session.query.filter_by(
                movie_id=ts.movie_id,
                hall_id=ts.hall_id,
                session_date=new_date,
                start_time=ts.start_time
            ).first()
            
            if not exists:
                new_session = Session(
                    movie_id=ts.movie_id,
                    hall_id=ts.hall_id,
                    session_date=new_date,
                    start_time=ts.start_time,
                    price=ts.price
                )
                db.session.add(new_session)
        
        db.session.commit()

@movies_bp.route('/movies')
def catalog():
    ensure_rolling_schedule()
    
    selected_genre = request.args.get('genre')
    query = Movie.query

    if selected_genre:
        query = query.filter(Movie.genre.contains(selected_genre))

    movies = query.order_by(Movie.id).all()
    genres_list = ["Фантастика", "Боевик", "Криминал", "Комедия", "Драма", "Мелодрама", "Аниме", "Фэнтези", "Биография", "Триллер", "Мультфильм", "Приключения"]

    return render_template('movies.html', movies=movies, genres=genres_list, selected_genre=selected_genre)

@movies_bp.route('/movies/<int:movie_id>')
def movie_detail(movie_id):
    ensure_rolling_schedule()
    
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        abort(404)
    
    today = datetime.now().date()
    
    sessions = Session.query.filter(
        Session.movie_id == movie_id,
        Session.session_date >= today 
    ).order_by(Session.session_date, Session.start_time).all()
    
    return render_template('movie_detail.html', movie=movie, sessions=sessions)

@movies_bp.route('/api/sessions/<int:session_id>/seats')
def get_session_seats(session_id):
    session_obj = db.session.get(Session, session_id)
    if not session_obj:
        return jsonify({'error': 'Сеанс не найден'}), 404

    seats = Seat.query.filter_by(hall_id=session_obj.hall_id).order_by(Seat.seat_number).all()
    booked_tickets = Ticket.query.filter_by(session_id=session_id).all()
    booked_seat_ids = [ticket.seat_id for ticket in booked_tickets]

    seat_data = []
    for seat in seats:
        seat_data.append({
            'id': seat.id,
            'number': seat.seat_number,
            'is_booked': seat.id in booked_seat_ids
        })

    return jsonify({
        'seats': seat_data,
        'price': float(session_obj.price),
        'hall_name': session_obj.hall.hall_name,
        'date': session_obj.session_date.strftime('%d.%m.%Y'),
        'time': session_obj.start_time.strftime('%H:%M')
    })

@movies_bp.route('/api/book_ticket', methods=['POST'])
def book_ticket():
    if 'user_id' not in session:
        return jsonify({'error': 'Необходимо войти в аккаунт'}), 401

    data = request.get_json()
    session_id = data.get('session_id')
    seat_id = data.get('seat_id')

    if not session_id or not seat_id:
        return jsonify({'error': 'Некорректные данные'}), 400

    existing_ticket = Ticket.query.filter_by(session_id=session_id, seat_id=seat_id).first()
    if existing_ticket:
        return jsonify({'error': 'Это место только что заняли'}), 409

    unique_code = str(uuid.uuid4())

    new_ticket = Ticket(
        user_id=session['user_id'],
        session_id=session_id,
        seat_id=seat_id,
        ticket_code=unique_code,
        status='booked'
    )
    
    try:
        db.session.add(new_ticket)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при бронировании'}), 500

# ----Айпишник сети вместо localhost для теста qr кода-----
    local_ip = "127.0.0.1" 
    verify_url = f"http://{local_ip}:5000/tickets/verify/{unique_code}"
    
    qr = qrcode.make(verify_url)
    qr_dir = "app/static/qr_codes"
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = f"qr_codes/{unique_code}.png"
    qr.save(f"app/static/{qr_path}")

    return jsonify({
        'success': True,
        'message': 'Билет успешно оформлен!',
        'qr_path': qr_path
    })