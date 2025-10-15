from flask import Blueprint, render_template, url_for, flash
from flask_login import login_required, current_user
from .forms import BookingForm
from .models import Order
from .import db
from datetime import datetime
from .forms import EventForm
from .models import Event

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    #return '<h1>Starter code for assignment 3<h1>'
    return render_template('index.html')

@main_bp.route('/history')
def history():
    
      # Temporary sample data while DB is paused
    bookings = [
        {
            "id": 1,
            "title": "Acoustic Night",
            "venue": "QUT Gardens Theatre",
            "date": "2025-10-20",
            "tickets": 2,
            "status": "Confirmed",
            "image": "event1.jpg"
        },
        {
            "id": 2,
            "title": "Tech Expo 2025",
            "venue": "Brisbane Convention Centre",
            "date": "2025-11-03",
            "tickets": 1,
            "status": "Pending",
            "image": "event2.jpg"
        },
        {
            "id": 3,
            "title": "Food Fest",
            "venue": "South Bank Parklands",
            "date": "2025-08-14",
            "tickets": 4,
            "status": "Cancelled",
            "image": "event3.jpg"
        }
    ]
    return render_template('history.html', bookings=bookings)

@main_bp.route('/user')
def user():
    return render_template("user.html")

@main_bp.route('/event', methods=['GET', 'POST'])
@login_required
def event():
    form = BookingForm()
    if form.validate_on_submit():
        new_order = Order(
            user_id=current_user.id,
            quantity=form.ticketQty.data,
            ticket_type=form.ticketType.data
        )
        db.session.add(new_order)
        db.session.commit()
        flash(f'Booking successful! Your order ID is {new_order.id}', 'success')
        return redirect(url_for('main.history'))
    return render_template('event.html', booking_form=form)

@main_bp.route('/history')
@login_required
def history():
    bookings = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', bookings=bookings)

@main_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = EventForm()
    if form.validate_on_submit():
        # Logic for EVENT STATUS
        if form.eDate.data<datetime.now():
            status = 'Inactive'           
        elif form.eTickets.data == 0:
            status = 'Sold Out'
        else:
            status = 'Open'
        new_event = Event(
            eventname=form.eName.data,
            description=form.eDesc.data,
            category=form.eCategory.data,
            venue=form.eVenue.data,
            eventdate=form.eDate.data,
            starttime=form.eStart.data,
            endtime=form.eEnd.data,
            numticket=form.eTickets.data,
            image=form.eImageUrl.data,
            owner_id=current_user.id,
            status=status
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('main.event'))
    return render_template('create.html', event_form=form)

@main_bp.route('/event/<int:event_id/edit>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.owner_id != current_user.id:
        flash('You do not have permission to edit this event.', 'danger')
        return redirect(url_for('main.event'))
    
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.eventname = form.eName.data
        event.description = form.eDesc.data
        event.category = form.eCategory.data
        event.venue = form.eVenue.data
        event.eventdate = form.eDate.data
        event.starttime = form.eStart.data
        event.endtime = form.eEnd.data
        event.numticket = form.eTickets.data
        event.image = form.eImageUrl.data
        
        # Logic for EVENT STATUS
        if event.eventdate < datetime.now():
            event.status = 'Inactive'
        elif event.numticket == 0:
            event.status = 'Sold Out'
        else:
            event.status = 'Open'
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('create.html', event_form=form, edit=True)

@main_bp.route('/event/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.owner_id != current_user.id:
        flash('You do not have permission to cancel this event.', 'danger')
        return redirect(url_for('main.event'))
    
    event.status = 'Cancelled'
    db.session.commit()
    flash('Event cancelled successfully!', 'success')
    return redirect(url_for('main.index'))

