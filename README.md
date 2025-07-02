# MovieMax - Premium Cinema Booking App

A modern, production-ready movie booking application built with Flask and integrated with AWS DynamoDB and SNS services.

## Features

🎬 **Movie Management**
- Browse current movies with detailed information
- Interactive seat selection with real-time availability
- Multiple showtime options

🎫 **Booking System**
- Real-time seat reservation
- Customer information collection
- Booking confirmation with unique IDs

📱 **Notifications**
- SMS notifications via AWS SNS
- Email confirmation support
- Booking status updates

🛠️ **Admin Panel**
- Movie management interface
- Booking analytics and reports
- Revenue tracking

## Technology Stack

- **Backend**: Python 3.8+, Flask
- **Database**: AWS DynamoDB
- **Notifications**: AWS SNS
- **Frontend**: HTML5, CSS3, JavaScript
- **Cloud**: AWS (DynamoDB, SNS)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. AWS Configuration

1. Set up your AWS credentials:
```bash
aws configure
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your AWS credentials and configuration:
```env
FLASK_SECRET_KEY=your-super-secret-key-here
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-here
AWS_SECRET_ACCESS_KEY=your-secret-key-here
DYNAMODB_TABLE_MOVIES=Movies
DYNAMODB_TABLE_BOOKINGS=Bookings
DYNAMODB_TABLE_USERS=Users
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:booking-notifications
```

### 3. Set up AWS Resources

Run the setup script to create DynamoDB tables and SNS topic:

```bash
python aws_setup.py
```

This will create:
- DynamoDB tables (Movies, Bookings, Users)
- SNS topic for notifications
- Sample movie data

### 4. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## AWS Services Configuration

### DynamoDB Tables

**Movies Table**
- Primary Key: `id` (String)
- Attributes: title, genre, duration, rating, poster, description, showtimes, price

**Bookings Table**
- Primary Key: `booking_id` (String)
- Global Secondary Index: `customer_email`
- Attributes: movie_id, movie_title, showtime, seats, customer details, total_price, created_at

**Users Table**
- Primary Key: `user_id` (String)
- Global Secondary Index: `email`
- Attributes: email, name, phone, created_at

### SNS Configuration

- Topic: `booking-notifications`
- SMS notifications for booking confirmations
- Transactional SMS type for reliable delivery

## API Endpoints

### Public Endpoints
- `GET /` - Movie listings
- `GET /movie/<id>` - Movie details
- `GET /book/<id>` - Booking page
- `POST /api/booking` - Create booking
- `GET /confirmation/<booking_id>` - Booking confirmation

### Admin Endpoints
- `GET /admin` - Admin dashboard
- Movie management operations

## Features in Detail

### Seat Selection
- Interactive seat map with 8 rows (A-H)
- 12 seats per row with center aisle
- Real-time availability checking
- Visual feedback for seat states

### Booking Process
1. Select movie and showtime
2. Choose seats on interactive map
3. Enter customer details
4. Confirm booking
5. Receive SMS confirmation

### Admin Dashboard
- Movie management (CRUD operations)
- Booking analytics
- Revenue tracking
- Popular movie reports

## Security Features

- Environment variable configuration
- AWS IAM integration
- Input validation and sanitization
- HTTPS ready (configure in production)

## Production Deployment

### AWS IAM Permissions Required

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/Movies",
                "arn:aws:dynamodb:*:*:table/Bookings",
                "arn:aws:dynamodb:*:*:table/Users",
                "arn:aws:dynamodb:*:*:table/*/index/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish",
                "sns:SetSMSAttributes"
            ],
            "Resource": "*"
        }
    ]
}
```

### Environment Variables for Production

Ensure all environment variables are properly set:
- `FLASK_SECRET_KEY` - Strong secret key
- AWS credentials and region
- DynamoDB table names
- SNS topic ARN

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or support, please contact the development team or create an issue in the repository.