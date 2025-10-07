from flask import Blueprint, render_template, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return '<h1>Starter code for assignment 3<h1>'

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