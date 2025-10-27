from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from .forms import BookingForm, CommentForm, relax_for_edit
from .models import Order, Comment
from .import db
from datetime import datetime, date, time
from .forms import EventForm
from .models import Event
from sqlalchemy import asc, desc

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    #return '<h1>Starter code for assignment 3<h1>'
    events = Event.query.order_by(asc(Event.eventdate)).all()
    return render_template('index.html', events=events)

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
    bookings = []
    for (o, e) in rows:
        # Determine ticket type based on price per ticket
        price = getattr(o, "price", 0.0)
        quantity = o.quantity if o.quantity > 0 else 1
        price_per_ticket = price / quantity
        
        if price_per_ticket == 150.0:
            ticket_type = "Family"
        elif price_per_ticket == 100.0:
            ticket_type = "Premium"
        else:
            ticket_type = "Standard"
        
        booking = {
            "id": o.id,  # used by the View button
            "title": getattr(e, "eventname", "Event"),
            "venue": e.venue,
            "date": o.date or getattr(e, "eventdate", None),
            "tickets": o.quantity,  # template expects 'tickets'
            "ticket_type": ticket_type,  # determined from price
            "price": price,
            "status": getattr(e, "status", "Confirmed"),
            "image": e.image,
        }
        bookings.append(booking)
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
        events = db.session.scalars(db.select(Event).where(Event.eventname.like(query)))
        return render_template('index.html', events=events)
    else:
        return redirect(url_for('main.index'))

@main_bp.route('/user')
def user():
    return render_template("user.html")

@main_bp.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event(event_id):
    form = BookingForm()
    comment_form = CommentForm()

    # Load the event row; avoid variable name 'event' to not shadow the function
    ev = Event.query.get_or_404(event_id)

   # --- Handle comment submission ---
    if comment_form.submit.data and comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to post a comment.', 'warning')
            return redirect(url_for('auth.login'))
        
        new_comment = Comment(
            text=comment_form.text.data.strip(),
            user_id=current_user.id,
            event_id=ev.id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment posted!', 'success')
        return redirect(url_for('main.event', event_id=ev.id))


    # Pull comments for this event, newest first (ordered by relationship)
    comments = ev.comments.all()

    # --- Handle booking submission ---
    if form.submit.data and form.validate_on_submit():
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to make a booking.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check event status before allowing booking
        if ev.status == 'Cancelled':
            flash('This event has been cancelled and is no longer available for booking.', 'danger')
            return redirect(url_for('main.event', event_id=ev.id))
        elif ev.status == 'Sold Out':
            flash('This event is sold out. No tickets are available.', 'warning')
            return redirect(url_for('main.event', event_id=ev.id))
        elif ev.status == 'Inactive':
            flash('This event has already occurred and is no longer available for booking.', 'warning')
            return redirect(url_for('main.event', event_id=ev.id))
        elif ev.status != 'Open':
            flash('This event is not currently available for booking.', 'warning')
            return redirect(url_for('main.event', event_id=ev.id))
        
        # Check if enough tickets are available
        if ev.numticket < form.ticketQty.data:
            flash(f'Only {ev.numticket} tickets are available. Please select fewer tickets.', 'warning')
            return redirect(url_for('main.event', event_id=ev.id))
        
        # Calculate price based on ticket type
        ticket_prices = {
            'Standard': 50.0,
            'Premium': 100.0,
            'Family': 150.0
        }
        ticket_type = form.ticketType.data
        unit_price = ticket_prices.get(ticket_type, 50.0)
        total_price = unit_price * form.ticketQty.data
        
        # Create the booking (temporarily without ticket_type until DB is fixed)
        new_order = Order(
            user_id=current_user.id,
            quantity=form.ticketQty.data,
            price=total_price,
            event_id=ev.id
        )
        
        # Update available ticket count
        ev.numticket -= form.ticketQty.data
        
        # Update event status if sold out
        if ev.numticket == 0:
            ev.status = 'Sold Out'
        
        db.session.add(new_order)
        db.session.commit()
        flash(f'Booking successful! Your order ID is {new_order.id}', 'success')
        return redirect(url_for('main.history'))

    return render_template(
        'event.html',
        event=ev,                    # pass DB object as "event"
        comment_form=comment_form,
        comments=comments,
        booking_form=form
    )

@main_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = EventForm()
    if form.validate_on_submit():

        event_dt = datetime.combine(form.eDate.data, form.eStart.data or time.min)
        start_dt = event_dt
        end_dt = datetime.combine(form.eDate.data, form.eEnd.data or time.max)

        # Logic for EVENT STATUS
        if form.eDate.data<date.today():
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
            eventdate=event_dt,      
            starttime=start_dt,     
            endtime=end_dt,     
            numticket=form.eTickets.data,
            image=form.eImageFile.data,
            owner_id=current_user.id,
            status=status
            
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create.html', form=form, event_form=form)


# originally /event/<int:event_id/edit>
@main_bp.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.owner_id != current_user.id:
        flash('You do not have permission to edit this event.', 'danger')
        return redirect(url_for('main.event'))
    
    form = EventForm(obj=event)

    relax_for_edit(form)


    if form.validate_on_submit():
        event.eventname = form.eName.data
        event.description = form.eDesc.data
        event.category = form.eCategory.data
        event.venue = form.eVenue.data
        event_dt = datetime.combine(form.eDate.data, form.eStart.data or time.min)
        event.eventdate = event_dt
        event.starttime = event_dt
        event.endtime   = datetime.combine(form.eDate.data, form.eEnd.data or time.max)
        event.numticket = form.eTickets.data
        event.image = form.eImageFile.data
        
        # Logic for EVENT STATUS
        if event.eventdate.date() < date.today():
            event.status = 'Inactive'
        elif event.numticket == 0:
            event.status = 'Sold Out'
        else:
            event.status = 'Open'
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('create.html', event_form=form, form=form, edit=True)

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





