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
    # get user's bookings
    orders = (db.session.query(Order, Event)
              .join(Event, Order.event_id == Event.id)
              .filter(Order.user_id == current_user.id)
              .order_by(Order.date.desc()).all())
    
    bookings = []
    for (order_record, event_record) in orders:
        # for Ticket Type mapping
        type_mapping = {1: "Standard", 2: "Premium", 3: "Family"}
        ticket_type = type_mapping[order_record.type]
        
        booking = {
            "id": order_record.id,
            "title": event_record.eventname,
            "venue": event_record.venue,
            "date": order_record.date,
            "tickets": order_record.quantity,
            "ticket_type": type_name,
            "price": order_record.price,
            "status": event_record.status,
            "image": event_record.image,
        }
        bookings.append(booking)
    return render_template('history.html', bookings=bookings)

@main_bp.route('/booking/<int:booking_id>')
@login_required
def view_booking(booking_id):
    # Get the user's booking
    booking = Order.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    event = Event.query.get_or_404(booking.event_id)

    # Show the event page
    booking_form = BookingForm()
    comment_form = CommentForm()
    return render_template('event.html', event=event, booking_form=booking_form, comment_form=comment_form, ticket_prices=ticket_prices)

    
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

# Ticket types for booking
ticket_prices = {
    'Standard': 50.0,
    'Premium': 100.0,
    'Family': 150.0
}
ticket_types = {1: "Standard", 2: "Premium", 3: "Family"}

@main_bp.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event(event_id):
    form = BookingForm()
    comment_form = CommentForm()

    # Loads the event row
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

    # Handle booking submission
    if form.submit.data and form.validate_on_submit():
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to make a booking.', 'warning')
            return redirect(url_for('auth.login'))
        

        
        # check event status
        if ev.status == "Cancelled":
            flash("This event has been cancelled.", "danger")
            return redirect(url_for("main.event", event_id=ev.id))
        elif ev.status == "Sold Out":
            flash("This event is sold out.", "warning")
            return redirect(url_for("main.event", event_id=ev.id))
        elif ev.status == "Inactive":
            flash("This event has already occurred.", "warning")
            return redirect(url_for("main.event", event_id=ev.id))
        elif ev.status != "Open":
            flash("This event is not currently available for booking.", "warning")
            return redirect(url_for("main.event", event_id=ev.id))
        
        # Check if enough tickets are available
        if ev.numticket < form.ticketQty.data:
            flash(f'Only {ev.numticket} tickets are available. Please select fewer tickets.', 'warning')
            return redirect(url_for('main.event', event_id=ev.id))
        
        # Calculate price based on ticket type
        selected_type = form.ticketType.data
        unit_price = ticket_prices[selected_type]
        total_price = unit_price * form.ticketQty.data
        
        # Get ticket type ID 
        if selected_type == "Standard":
            type_id = 1
        elif selected_type == "Premium":
            type_id = 2
        else:  # Family
            type_id = 3
        
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
        
        # Check if sold out
        if ev.numticket == 0:
            ev.status = 'Sold Out'
        
        db.session.add(new_order)
        db.session.commit()
        flash(f'Booking successful! Order ID: {new_order.id}', 'success')
        return redirect(url_for('main.history'))

    return render_template(
        'event.html',
        event=ev,
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
        # Ensures that endtime is after startime
        if form.eEnd.data <= form.eStart.data:
            flash('End time must be after start time.', 'warning')
            return render_template('create.html', form=form, event_form=form)

        event_dt = datetime.combine(form.eDate.data, form.eStart.data)
        start_dt = event_dt
        end_dt = datetime.combine(form.eDate.data, form.eEnd.data)

        img_filename = 'default.jpg'  
        if form.eImageFile.data:
            image_file = form.eImageFile.data
            if image_file.filename != '':
                filename = secure_filename(image_file.filename)
                # Add timestamp to avoid conflicts
                new_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = os.path.join(current_app.root_path, 'static', 'img', new_filename)
                image_file.save(filepath)
                img_filename = new_filename

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
        return redirect(url_for('main.event', event_id=event.id))
    
    form = EventForm(obj=event)

    relax_for_edit(form)


    if form.validate_on_submit():
        # Again ensures that endtime is after starttime
        if form.eEnd.data <= form.eStart.data:
            flash('End time must be after start time.', 'warning')
            return render_template('create.html', event_form=form, form=form, edit=True)
            a
        event.eventname = form.eName.data
        event.description = form.eDesc.data
        event.category = form.eCategory.data
        event.venue = form.eVenue.data
        event_dt = datetime.combine(form.eDate.data, form.eStart.data)
        event.eventdate = event_dt
        event.starttime = event_dt
        event.endtime = datetime.combine(form.eDate.data, form.eEnd.data)
        event.numticket = form.eTickets.data
        # image upload
        if form.eImageFile.data and form.eImageFile.data.filename != '':
            image_file = form.eImageFile.data
            filename = secure_filename(image_file.filename)
            # Add timestamp to avoid conflicts
            new_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = os.path.join(current_app.root_path, 'static', 'img', new_filename)
            image_file.save(filepath)
            event.image = new_filename
        
        #EVENT STATUS
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
        return redirect(url_for('main.event', event_id=event.id))
    
    event.status = 'Cancelled'
    db.session.commit()
    flash('Event cancelled successfully!', 'success')
    return redirect(url_for('main.index'))