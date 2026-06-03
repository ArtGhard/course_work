# app/routes/tickets.py
from app.models import User
from flask import Blueprint, render_template, session
from app.models import Ticket, Session, Movie, Seat
from app import db
from flask import render_template_string
from app import db
from app.models import Ticket


tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/tickets')
def user_tickets():
    user_id = session.get('user_id')
    
    if not user_id:
        return render_template('tickets.html', user=None, tickets=[])
    
    user = db.session.get(User, user_id)
    
    tickets = db.session.query(Ticket)\
        .join(Session, Ticket.session_id == Session.id)\
        .join(Movie, Session.movie_id == Movie.id)\
        .join(Seat, Ticket.seat_id == Seat.id)\
        .filter(Ticket.user_id == user_id)\
        .order_by(Ticket.created_at.desc())\
        .all()
    
    return render_template('tickets.html', user=user, tickets=tickets)

@tickets_bp.route('/tickets/verify/<ticket_code>')
def verify_ticket(ticket_code):
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()

    if not ticket:
        html = """
        <div style="text-align:center; margin-top:50px; font-family: sans-serif; color: #ff4444;">
            <h1 style="font-size: 4rem;">❌</h1>
            <h2>Билет не найден</h2>
            <p>Этот QR-код недействителен или был сгенерирован с ошибкой.</p>
        </div>
        """
        return render_template_string(html), 404

    if ticket.status == 'used':
        html = f"""
        <div style="text-align:center; margin-top:50px; font-family: sans-serif; color: #ff9800;">
            <h1 style="font-size: 4rem;">⚠️</h1>
            <h2>Билет уже использован</h2>
            <p>Этот билет был отсканиран ранее.</p>
            <p><small>Фильм: {ticket.session.movie.title}</small></p>
        </div>
        """
        return render_template_string(html), 403

    if ticket.status == 'booked':
        ticket.status = 'used'
        db.session.commit()

        html = f"""
        <div style="text-align:center; margin-top:30px; font-family: sans-serif; color: #4caf50;">
            <h1 style="font-size: 5rem; margin: 0;">✅</h1>
            <h2 style="color: #fff; margin-top: 10px;">БИЛЕТ ДЕЙСТВИТЕЛЕН</h2>
            
            <div style="background: #222; padding: 20px; border-radius: 12px; margin: 20px auto; max-width: 400px; color: #fff; text-align: left;">
                <p style="font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 10px;">
                    {ticket.session.movie.title}
                </p>
                <p>📅 Дата: <strong>{ticket.session.session_date.strftime('%d.%m.%Y')}</strong></p>
                <p>⏰ Время: <strong>{ticket.session.start_time.strftime('%H:%M')}</strong></p>
                <p>🚪 Зал: <strong>{ticket.session.hall.hall_name}</strong></p>
                <p>💺 Место: <strong>№{ticket.seat.seat_number}</td></strong></p>
            </div>
            
            <p style="color: #888; font-size: 0.9rem;">Статус билета изменен на "Использован"</p>
        </div>
        """
        return render_template_string(html)