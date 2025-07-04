from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import boto3
from boto3.dynamodb.conditions import Key
import uuid
from datetime import datetime, timedelta
import os
import json
import hashlib
import secrets

app = Flask(__name__.)
app.secret_key = '2f9b3e7d56d749cdab6f9cf672d2a937c64f0f19c4eaefc17264f2d39a5314bb'

# AWS Configuration
AWS_REGION = 'us-east-1'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:841162700013:Moviemagic:f5a6d793-14c7-4b7f-a7c5-2c53d4fdaeb3'

# DynamoDB Table Names
DYNAMODB_TABLE_MOVIES = 'Movies'
DYNAMODB_TABLE_BOOKINGS = 'Bookings'
DYNAMODB_TABLE_USERS = 'Users'

# Initialize AWS services
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    sns = boto3.client('sns', region_name=AWS_REGION)
    
    movies_table = dynamodb.Table(DYNAMODB_TABLE_MOVIES)
    bookings_table = dynamodb.Table(DYNAMODB_TABLE_BOOKINGS)
    users_table = dynamodb.Table(DYNAMODB_TABLE_USERS)
    
    print("AWS services initialized successfully")
except Exception as e:
    print(f"AWS initialization error: {e}")
    dynamodb = None
    sns = None

# Sample fallback data
SAMPLE_MOVIES = [
    {
        'id': '1',
        'title': 'Avatar: The Way of Water',
        'genre': 'Action/Adventure',
        'duration': 192,
        'rating': 'PG-13',
        'poster': 'https://images.pexels.com/photos/7991579/pexels-photo-7991579.jpeg?auto=compress&cs=tinysrgb&w=400',
        'description': 'Jake Sully lives with his newfound family on Pandora.',
        'showtimes': ['10:00 AM', '2:00 PM', '6:00 PM', '9:30 PM'],
        'price': 250.00
    }
]

def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000)
    return salt + password_hash.hex()

def verify_password(password, hashed_password):
    salt = hashed_password[:32]
    stored_hash = hashed_password[32:]
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000)
    return password_hash.hex() == stored_hash

def get_movies():
    if movies_table:
        try:
            response = movies_table.scan()
            return response.get('Items', SAMPLE_MOVIES)
        except:
            return SAMPLE_MOVIES
    return SAMPLE_MOVIES

def get_movie_by_id(movie_id):
    return next((m for m in get_movies() if m['id'] == movie_id), None)

def create_user(user_data):
    try:
        user_data['user_id'] = str(uuid.uuid4())
        user_data['created_at'] = datetime.now().isoformat()
        users_table.put_item(Item=user_data)
        return user_data
    except Exception as e:
        print(f"User creation error: {e}")
        return None

def get_user_by_email(email):
    try:
        response = users_table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        return response['Items'][0] if response['Items'] else None
    except:
        return None

def get_user_bookings(email):
    try:
        response = bookings_table.query(
            IndexName='customer-email-index',
            KeyConditionExpression=Key('customer_email').eq(email)
        )
        return response.get('Items', [])
    except:
        return []

def create_booking(booking_data):
    try:
        booking_data['booking_id'] = str(uuid.uuid4())
        booking_data['created_at'] = datetime.now().isoformat()
        bookings_table.put_item(Item=booking_data)
        return booking_data
    except Exception as e:
        print(f"Booking error: {e}")
        return None

def send_booking_notification(phone_number, booking_details):
    if sns:
        try:
            message = f"""🎟 Movie Booking Confirmed!
Movie: {booking_details['movie_title']}
Showtime: {booking_details['showtime']}
Seats: {', '.join(booking_details['seats'])}
Total: ₹{booking_details['total_price']}
Booking ID: {booking_details['booking_id']}"""

            response = sns.publish(
                PhoneNumber=phone_number,
                Message=message,
                TopicArn=SNS_TOPIC_ARN
            )
            return response
        except Exception as e:
            print(f"SNS Error: {e}")
            return None
    return {"MessageId": "mock"}

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Login required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    return render_template('index.html', movies=get_movies())

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
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        if data['password'] != data['confirm_password']:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        if get_user_by_email(data['email']):
            flash('User already exists', 'error')
            return render_template('signup.html')
        user = create_user({
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'password': hash_password(data['password'])
        })
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash('Account created!', 'success')
            return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('index'))

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
    showtime = request.args.get('showtime')
    if not movie or not showtime:
        flash('Missing movie or showtime', 'error')
        return redirect(url_for('index'))
    return render_template('booking.html', movie=movie, showtime=showtime)

@app.route('/api/booking', methods=['POST'])
@login_required
def create_booking_api():
    try:
        data = request.get_json()
        required = ['movie_id', 'movie_title', 'showtime', 'seats', 'total_price']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing fields'}), 400
        data.update({
            'customer_name': session['user_name'],
            'customer_email': session['user_email'],
            'customer_phone': data.get('customer_phone', '')
        })
        booking = create_booking(data)
        if booking and data.get('customer_phone'):
            send_booking_notification(data['customer_phone'], booking)
        return jsonify({'success': True, 'booking_id': booking['booking_id']})
    except Exception as e:
        print(e)
        return jsonify({'error': 'Server error'}), 500

@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = get_user_bookings(session['user_email'])
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/confirmation/<booking_id>')
@login_required
def confirmation(booking_id):
    return render_template('confirmation.html', booking_id=booking_id)

@app.route('/admin')
def admin():
    return render_template('admin.html', movies=get_movies())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
