from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField, IntegerField, SelectField, DateField, TimeField, FileField
from wtforms.validators import InputRequired, Length, Email, EqualTo, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import Optional

# Creates the login form
class LoginForm(FlaskForm):
    user_name=StringField("User Name", validators=[InputRequired('Enter user name')])
    password=PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")

 # Creates the user registration form
class RegisterForm(FlaskForm):
    user_name = StringField("User Name", validators=[InputRequired()])
    full_name = StringField("Full Name", validators=[InputRequired()])
    email = StringField("Email Address", validators=[Email("Please enter a valid email")])
    address = StringField("Address", validators=[InputRequired()])
    contact = StringField("Phone Number", validators=[InputRequired()])
    password=PasswordField("Password", validators=[InputRequired(),
                  EqualTo('confirm', message="Passwords should match")])
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Register")

 # Booking form
class BookingForm(FlaskForm):
    ticketQty = IntegerField("Number of Tickets", validators=[InputRequired(), NumberRange(min=1, message='Enter at least 1 ticket')])
    ticketType = SelectField("Ticket Type", choices=[("Standard", "Standard"), ("Premium", "Premium"), ("Family", "Family")], validators=[InputRequired()])
    submit = SubmitField("Book Now")

 # Create Event form
class EventForm(FlaskForm):
    eName = StringField("Event Name", validators=[InputRequired(), Length(min=5, max=100)])
    eDesc = TextAreaField("Event Description", validators=[InputRequired(), Length(min=10)])
    eCategory = SelectField("Category", choices=[("Football", "Football"), ("Rugby", "Rugby"), ("Cricket", "Cricket"), ("Concert", "Concert")], validators=[InputRequired()])
    eVenue = StringField("Venue", validators=[InputRequired(), Length(min=5, max=100)])
    eDate = DateField("Event Date", format='%Y-%m-%d', validators=[InputRequired()])
    eStart = TimeField("Start Time", format='%H:%M', validators=[InputRequired()])
    eEnd   = TimeField("End Time",   format='%H:%M', validators=[InputRequired()])
    eTickets = IntegerField("Tickets Available", validators=[InputRequired(), NumberRange(min=0, message='Tickets must be 0 or greater')])
    eImageFile = FileField("Upload Image (optional)", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Only JPG, PNG, and JPEG files are allowed!')])
    submit = SubmitField("Save Event")

def relax_for_edit(form):
    """
    Replaces InputRequired validators with Optional() so blank fields
    don't break validation during edit.
    """
    for fname in [
        "eName", "eDesc", "eVenue", "eDate",
        "eStart", "eEnd", "eTickets", "eImageFile"
    ]:
        field = getattr(form, fname, None)
        if field:
            field.validators = [
                v for v in field.validators
                if v.__class__.__name__ != "InputRequired"
            ]
            field.validators.append(Optional())


class CommentForm(FlaskForm):
    text = TextAreaField(
        "Add a comment",
        validators=[InputRequired(), Length(max=400)]
    )
    submit = SubmitField("Post")

