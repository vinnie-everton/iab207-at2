from flask import Blueprint, render_template, url_for, flash, redirect
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

<<<<<<< Updated upstream
=======
@main_bp.route('/history')
@login_required
def history():
    # Join Orders to Events for the current user
    rows = (
        db.session.query(Order, Event)
        .join(Event, Order.event_id == Event.id)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.date.desc())
        .all()
    )
    # Shape the data exactly as the template expects
    bookings = [
        {
            "id": o.id,  # used by the View button
            "title": getattr(e, "eventname", "Event"),
            "venue": e.venue,
            "date": o.date or getattr(e, "eventdate", None),
            "tickets": o.quantity,  # template expects 'tickets'
            "status": getattr(e, "status", "Confirmed"),
            "image": e.image,
        }
        for (o, e) in rows
    ]
    return render_template('history.html', bookings=bookings)

@main_bp.route('/booking/<int:booking_id>')
@login_required
def view_booking(booking_id):
    # Ensure the booking belongs to the current user
    order = Order.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    event = Event.query.get_or_404(order.event_id) if order.event_id else None

    # Reuse your existing event page with the booking form
    form = BookingForm()
    return render_template('event.html', event=event, booking_form=form)

    
@main_bp.route('/search')
def search():
    if request.args['search'] and request.args['search'] != "":
        print(request.args['search'])
        query = "%" + request.args['search'] + "%"
        destinations = db.session.scalars(db.select(Event).where(Event.description.like(query)))
        return render_template('index.html', destinations=destinations)
    else:
        return redirect(url_for('main.index'))
>>>>>>> Stashed changes

@main_bp.route('/user')
def user():
    return render_template("user.html")

@main_bp.route('/event', methods=['GET'])
@login_required
def event():
<<<<<<< Updated upstream
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
=======
    # Show all events or redirect to a specific event
    events = Event.query.all()
    return render_template('index.html', events=events)





>>>>>>> Stashed changes

# Duplicate history route removed - using the one above that joins with Events

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

<<<<<<< Updated upstream
=======




@main_bp.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    form = BookingForm()
    
    if form.validate_on_submit():
        # Calculate price based on ticket type
        ticket_prices = {"Standard": 50, "Premium": 100, "Family": 150}
        ticket_type = form.ticketType.data
        price = ticket_prices.get(ticket_type, 50) * form.ticketQty.data

        new_order = Order(
            user_id=current_user.id,
            quantity=form.ticketQty.data,
            ticket_type=ticket_type,
            price=price,
            event_id=event_id,  # Now we know the specific event ID
        )

        db.session.add(new_order)
        db.session.commit()
        flash(f'Booking successful! Your order ID is {new_order.id}', 'success')
        return redirect(url_for('main.history'))
    
    return render_template('event.html', event=event, booking_form=form)





# originally /event/<int:event_id/edit>
>>>>>>> Stashed changes
@main_bp.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
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
        if form.eDate.data < datetime.now().date():
            status = 'Inactive'
        elif form.eTickets.data == 0:
            status = 'Sold Out'
        else:
            status = 'Open'
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

