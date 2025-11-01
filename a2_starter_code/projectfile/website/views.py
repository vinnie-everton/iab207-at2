from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from .forms import BookingForm, CommentForm, relax_for_edit
from .models import Order, Comment
from .import db
from datetime import datetime, date, time
from .forms import EventForm
from .models import Event
from sqlalchemy import asc, desc, func
from werkzeug.utils import secure_filename
from flask import current_app
import os

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
    user_booking_records = (
        db.session.query(Order, Event)
        .join(Event, Order.event_id == Event.id)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.date.desc())
        .all()
    )
    
    bookings = []
    for (order_record, event_record) in user_booking_records:
        # for Ticket Type mapping
        type_mapping = {1: "Standard", 2: "Premium", 3: "Family"}
        ticket_type = type_mapping.get(order_record.type, "Standard")
        
        booking = {
            "id": order_record.id,
            "title": getattr(event_record, "eventname", "Event"),
            "venue": event_record.venue,
            "date": order_record.date or getattr(event_record, "eventdate", None),
            "tickets": order_record.quantity,
            "ticket_type": ticket_type,
            "price": getattr(order_record, "price", 0.0),
            "status": getattr(event_record, "status", "Confirmed"),
            "image": event_record.image,
        }
        bookings.append(booking)
    return render_template('history.html', bookings=bookings)

@main_bp.route('/booking/<int:booking_id>')
@login_required
def view_booking(booking_id):
    # Ensure the booking belongs to the current user
    user_booking_order = Order.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    booked_event = Event.query.get_or_404(user_booking_order.event_id) if user_booking_order.event_id else None

    ticket_prices = {
        'Standard': 50.0,
        'Premium': 100.0,
        'Family': 150.0
    }

    # Reuse existing event page with the booking form
    form = BookingForm()
    comment_form = CommentForm()
    return render_template('event.html', event=event, booking_form=form, comment_form=comment_form, ticket_prices=ticket_prices)

    
@main_bp.route('/search')
def search():
    search_query = request.args.get('search', '').strip()

    if not search_query:
        return redirect(url_for('main.index'))

    query = f"%{search_query}%"
    events = list(db.session.scalars(db.select(Event).where(Event.eventname.like(query))))

    if not events:
        # No events found — show a message instead
        return render_template('index.html', search_query=search_query)
    else:
        return render_template('index.html', events=events)

@main_bp.route('/filter')
def filter(): #function regarding filters
    selected_category = request.args.get('category') 
    event_query = db.select(Event) # initial sql event query
    if selected_category != 'All': #if selected category button is not All query for the specific button 
        event_query = event_query.where(func.lower(Event.category) == selected_category.lower())
    events = list(db.session.scalars(event_query))
    return render_template('index.html', events=events, selected_category=selected_category)

@main_bp.route('/user')
def user():
    return render_template("user.html")

@main_bp.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event(event_id):
    form = BookingForm()
    comment_form = CommentForm()

    # Loads the event row
    ev = Event.query.get_or_404(event_id)
    ticket_prices = {
            'Standard': 50.0,
            'Premium': 100.0,
            'Family': 150.0
        }

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

    # Handle booking submission
    if form.submit.data and form.validate_on_submit():
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to make a booking.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Event status
        status_messages = {
            "Cancelled": ("This event has been cancelled.", "danger"),
            "Sold Out": ("This event is sold out.", "warning"),
            "Inactive": ("This event has already occurred.", "warning")
        }

        # Prevent booking based on event status
        if ev.status in status_messages:
            msg, level = status_messages[ev.status]
            flash(msg, level)
            return redirect(url_for("main.event", event_id=ev.id))
        if ev.status != "Open":
            flash("This event is not currently available for booking.", "warning")
            return redirect(url_for("main.event", event_id=ev.id))
        
        # Check if enough tickets are available
        if ev.numticket < form.ticketQty.data:
            flash(f'Only {ev.numticket} tickets are available. Please select fewer tickets.', 'warning')
            return redirect(url_for('main.event', event_id=ev.id))
        
        # Calculate price based on ticket type
      
        ticket_type = form.ticketType.data
        unit_price = ticket_prices.get(ticket_type, 50.0)
        total_price = unit_price * form.ticketQty.data
        
        # ticket type database storage
        type_mapping = {"Standard": 1, "Premium": 2, "Family": 3}
        type_id = type_mapping.get(form.ticketType.data, 1)
        
        # Create booking
        new_order = Order(
            user_id=current_user.id,
            quantity=form.ticketQty.data,
            price=total_price,
            type=type_id,
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
        event=ev, # passes DB object as "event"
        comment_form=comment_form,
        comments=comments,
        booking_form=form,
        ticket_prices=ticket_prices
    )

@main_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = EventForm()
    if form.validate_on_submit():

        event_dt = datetime.combine(form.eDate.data, form.eStart.data or time.min)
        start_dt = event_dt
        end_dt = datetime.combine(form.eDate.data, form.eEnd.data or time.max)


        img_filename = 'default.jpg'  
        if form.eImageFile.data:
            image_file = form.eImageFile.data
            if image_file.filename != '':
                filename = secure_filename(image_file.filename)
                # Make filename unique by adding timestamp
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = os.path.join(current_app.root_path, 'static', 'img', unique_filename)
                image_file.save(filepath)
                img_filename = unique_filename





        # Event Status
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
            image=img_filename,
            owner_id=current_user.id,
            status=status
            
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create.html', form=form, event_form=form)


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
        # image upload
        if form.eImageFile.data and form.eImageFile.data.filename != '':
            image_file = form.eImageFile.data
            filename = secure_filename(image_file.filename)
            # Filename timestamp to prevent overwriting
            unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = os.path.join(current_app.root_path, 'static', 'img', unique_filename)
            image_file.save(filepath)
            event.image = unique_filename
        
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







