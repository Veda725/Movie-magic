"""
AWS DynamoDB and SNS Setup Script
Run this script to create the necessary AWS resources for the movie booking app.
"""

import boto3
from botocore.exceptions import ClientError
import json

def create_dynamodb_tables():
    """Create DynamoDB tables for the movie booking app"""
    
    dynamodb = boto3.resource('dynamodb')
    
    # Movies table schema
    movies_table_def = {
        'TableName': 'Movies',
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    }
    
    # Bookings table schema
    bookings_table_def = {
        'TableName': 'Bookings',
        'KeySchema': [
            {'AttributeName': 'booking_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'booking_id', 'AttributeType': 'S'},
            {'AttributeName': 'customer_email', 'AttributeType': 'S'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'customer-email-index',
                'KeySchema': [
                    {'AttributeName': 'customer_email', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    }
    
    # Users table schema
    users_table_def = {
        'TableName': 'Users',
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'email-index',
                'KeySchema': [
                    {'AttributeName': 'email', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    }
    
    tables_to_create = [movies_table_def, bookings_table_def, users_table_def]
    
    for table_def in tables_to_create:
        try:
            table = dynamodb.create_table(**table_def)
            print(f"Creating table {table_def['TableName']}...")
            table.wait_until_exists()
            print(f"✅ Table {table_def['TableName']} created successfully!")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_def['TableName']} already exists")
            else:
                print(f"❌ Error creating table {table_def['TableName']}: {e}")

def populate_sample_movies():
    """Populate the Movies table with sample data"""
    
    dynamodb = boto3.resource('dynamodb')
    movies_table = dynamodb.Table('Movies')
    
    sample_movies = [
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
    
    try:
        for movie in sample_movies:
            movies_table.put_item(Item=movie)
        print("✅ Sample movies added successfully!")
    except ClientError as e:
        print(f"❌ Error adding sample movies: {e}")

def create_sns_topic():
    """Create SNS topic for booking notifications"""
    
    sns = boto3.client('sns')
    
    try:
        response = sns.create_topic(Name='booking-notifications')
        topic_arn = response['TopicArn']
        print(f"✅ SNS Topic created: {topic_arn}")
        
        # Set SMS preferences
        sns.set_sms_attributes(
            attributes={
                'DefaultSMSType': 'Transactional',
                'DefaultSenderID': 'MovieMax'
            }
        )
        print("✅ SMS preferences configured")
        
        return topic_arn
    except ClientError as e:
        print(f"❌ Error creating SNS topic: {e}")
        return None

def main():
    """Main setup function"""
    print("🎬 Setting up AWS resources for MovieMax booking app...")
    print("=" * 50)
    
    # Create DynamoDB tables
    print("\n📁 Creating DynamoDB tables...")
    create_dynamodb_tables()
    
    # Populate sample movies
    print("\n🎭 Adding sample movies...")
    populate_sample_movies()
    
    # Create SNS topic
    print("\n📱 Setting up SMS notifications...")
    topic_arn = create_sns_topic()
    
    print("\n" + "=" * 50)
    print("🎉 AWS setup complete!")
    print("\n📝 Next steps:")
    print("1. Update your .env file with the correct AWS credentials")
    print("2. Replace the SNS_TOPIC_ARN in .env with:", topic_arn if topic_arn else "your-topic-arn")
    print("3. Run the Flask app with: python app.py")
    print("\n⚠️  Note: Make sure your AWS credentials have the necessary permissions for DynamoDB and SNS")

if __name__ == "__main__":
    main()