from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import boto3
from boto3.dynamodb.conditions import Key
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import hashlib
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
DYNAMODB_TABLE_MOVIES = os.getenv('DYNAMODB_TABLE_MOVIES', 'Movies')
DYNAMODB_TABLE_BOOKINGS = os.getenv('DYNAMODB_TABLE_BOOKINGS', 'Bookings')
DYNAMODB_TABLE_USERS = os.getenv('DYNAMODB_TABLE_USERS', 'Users')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:booking-notifications')

# Initialize AWS services
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    sns = boto3.client('sns', region_name=AWS_REGION)
    
    # Get table references
    movies_table = dynamodb.Table(DYNAMODB_TABLE_MOVIES)
    bookings_table = dynamodb.Table(DYNAMODB_TABLE_BOOKINGS)
    users_table = dynamodb.Table(DYNAMODB_TABLE_USERS)
    
    print("AWS services initialized successfully")
except Exception as e:
    print(f"AWS initialization error: {e}")
    # For development without AWS, create mock objects
    dynamodb = None
    sns = None

# Sample data for development
SAMPLE_MOVIES = [
    {
        'id': '1',
        'title': 'Avatar: The Way of Water',
        'genre': 'Action/Adventure',
        'duration': 192,
        'rating': 'PG-13',
        'poster': 'https://images.pexels.com/photos/7991579/pexels-photo-7991579.jpeg?auto=compress&cs=tinysrgb&w=400',
        'description': 'Jake Sully lives with his newfound family formed on the extrasolar moon Pandora.',
        'showtimes': ['10:00 AM', '2:00 PM', '6:00 PM', '9:30 PM'],
        'price': 250.00
    },
    {
        'id': '2',
        'title': 'Top Gun: Maverick',
        'genre': 'Action/Drama',
        'duration': 131,
        'rating': 'PG-13',
        'poster': 'https://images.pexels.com/photos/8349023/pexels-photo-8349023.jpeg?auto=compress&cs=tinysrgb&w=400',
        'description': 'After thirty years, Maverick is still pushing the envelope as a top naval aviator.',
        'showtimes': ['11:00 AM', '3:00 PM', '7:00 PM', '10:00 PM'],
        'price': 250.00
    },
    {
        'id': '3',
        'title': 'Black Panther: Wakanda Forever',
        'genre': 'Action/Drama',
        'duration': 161,
        'rating': 'PG-13',
        'poster': 'https://images.pexels.com/photos/8129903/pexels-photo-8129903.jpeg?auto=compress&cs=tinysrgb&w=400',
        'description': 'The people of Wakanda fight to protect their home from intervening world powers.',
        'showtimes': ['12:00 PM', '4:00 PM', '8:00 PM', '11:00 PM'],
        'price': 250.00
    }
]

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)  # 16 bytes = 32 hex characters
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
    return salt + password_hash.hex()  # salt (32 hex chars) + hash

def verify_password(password, hashed_password):
    """Verify password against hash"""
    salt = hashed_password[:32]  # 16 bytes in hex = 32 chars
    stored_hash = hashed_password[32:]
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
    return password_hash.hex() == stored_hash


def get_movies():
    """Get all movies from DynamoDB or return sample data"""
    if movies_table:
        try:
            response = movies_table.scan()
            return response.get('Items', SAMPLE_MOVIES)
        except Exception as e:
            print(f"Error fetching movies: {e}")
            return SAMPLE_MOVIES
    return SAMPLE_MOVIES

def get_movie_by_id(movie_id):
    """Get a specific movie by ID"""
    movies = get_movies()
    return next((movie for movie in movies if movie['id'] == movie_id), None)

def create_user(user_data):
    """Create a new user in DynamoDB"""
    if users_table:
        try:
            user_data['user_id'] = str(uuid.uuid4())
            user_data['created_at'] = datetime.now().isoformat()
            users_table.put_item(Item=user_data)
            return user_data
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    # For development, just return the user data with an ID
    user_data['user_id'] = str(uuid.uuid4())
    user_data['created_at'] = datetime.now().isoformat()
    return user_data

def get_user_by_email(email):
    """Get user by email"""
    if users_table:
        try:
            response = users_table.query(
                IndexName='email-index',
                KeyConditionExpression=Key('email').eq(email)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    return None

def get_user_bookings(user_email):
    """Get all bookings for a user"""
    if bookings_table:
        try:
            response = bookings_table.query(
                IndexName='customer-email-index',
                KeyConditionExpression=Key('customer_email').eq(user_email)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error fetching bookings: {e}")
            return []
    return []

def create_booking(booking_data):
    """Create a new booking in DynamoDB"""
    if bookings_table:
        try:
            booking_data['booking_id'] = str(uuid.uuid4())
            booking_data['created_at'] = datetime.now().isoformat()
            bookings_table.put_item(Item=booking_data)
            return booking_data
        except Exception as e:
            print(f"Error creating booking: {e}")
            return None
    # For development, just return the booking data with an ID
    booking_data['booking_id'] = str(uuid.uuid4())
    booking_data['created_at'] = datetime.now().isoformat()
    return booking_data

def send_booking_notification(phone_number, booking_details):
    """Send SMS notification via AWS SNS"""
    if sns:
        try:
            message = f"Booking Confirmed!\nMovie: {booking_details['movie_title']}\nShowtime: {booking_details['showtime']}\nSeats: {', '.join(booking_details['seats'])}\nTotal: ₹{booking_details['total_price']}\nBooking ID: {booking_details['booking_id']}"
            
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            return response
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return None
    print(f"SMS would be sent to {phone_number}: {booking_details}")
    return {"MessageId": "mock-message-id"}

def login_required(f):
    """Decorator to require login for certain routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    movies = get_movies()
    return render_template('index.html', movies=movies)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = get_user_by_email(email)
        if user and verify_password(password, user['password']):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create new user
        user_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': hash_password(password)
        }
        
        user = create_user(user_data)
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Error creating account. Please try again.', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = get_user_bookings(session['user_email'])
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/movie/<movie_id>')
def movie_details(movie_id):
    movie = get_movie_by_id(movie_id)
    if not movie:
        flash('Movie not found', 'error')
        return redirect(url_for('index'))
    return render_template('movie_details.html', movie=movie)

@app.route('/book/<movie_id>')
@login_required
def book_movie(movie_id):
    movie = get_movie_by_id(movie_id)
    if not movie:
        flash('Movie not found', 'error')
        return redirect(url_for('index'))
    
    showtime = request.args.get('showtime')
    if not showtime:
        flash('Please select a showtime', 'error')
        return redirect(url_for('movie_details', movie_id=movie_id))
    
    return render_template('booking.html', movie=movie, showtime=showtime)

@app.route('/api/booking', methods=['POST'])
@login_required
def create_booking_api():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['movie_id', 'movie_title', 'showtime', 'seats', 'total_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Add user information from session
        data['customer_name'] = session['user_name']
        data['customer_email'] = session['user_email']
        data['customer_phone'] = session.get('user_phone', '')
        
        # Create booking
        booking = create_booking(data)
        if not booking:
            return jsonify({'error': 'Failed to create booking'}), 500
        
        # Send notification
        if data.get('customer_phone'):
            notification_result = send_booking_notification(data['customer_phone'], booking)
        
        return jsonify({
            'success': True,
            'booking_id': booking['booking_id'],
            'message': 'Booking created successfully!'
        })
        
    except Exception as e:
        print(f"Booking error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/confirmation/<booking_id>')
@login_required
def confirmation(booking_id):
    return render_template('confirmation.html', booking_id=booking_id)

@app.route('/admin')
def admin():
    movies = get_movies()
    return render_template('admin.html', movies=movies)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



