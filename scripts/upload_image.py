import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

# Load environment variables from .env file
print("Loading environment variables...")
env_path = os.path.join("..", ".env")  # Adjust the path as needed
load_dotenv(env_path)

# Extract credentials
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")
filename = '/home/mirage/.distros/codeblox/Codes/Project/HospiLink/scripts/generated_faces/f_0b4232d3-9f30-4006-aa4e-50d0d009e7c3.jpg'
username = 'shadabtanjeed'  # Username to be inserted/updated

# Debugging credentials
print(f"Connecting to DB with host: {db_host}, port: {db_port}, user: {db_user}, dbname: {db_name}")

# Verify environment variable loading
if not all([db_name, db_user, db_password, db_host, db_port]):
    print("Error: Missing one or more required environment variables. Check your .env file.")
    exit()

# Open the image file
print(f"Opening the image file: {filename}...")
try:
    with open(filename, 'rb') as f:
        file_data = f.read()
    print("Image file opened successfully!")
except Exception as e:
    print(f"Error opening image file: {e}")
    exit()

# Connect to PostgreSQL
print("Connecting to the PostgreSQL database...")
try:
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    print("Connected to the database!")
except Exception as e:
    print(f"Error connecting to the database: {e}")
    exit()

# Insert into profile_picture table
print("Preparing to insert into the profile_picture table...")
try:
    cur = conn.cursor()
    cur.execute(sql.SQL("""
        INSERT INTO profile_picture (username, image)
        VALUES (%s, %s)
        ON CONFLICT (username) DO UPDATE SET image = EXCLUDED.image
    """), (username, psycopg2.Binary(file_data)))
    print("Query executed successfully!")
    
    # Commit the changes
    conn.commit()
    print("Changes committed to the database.")
except Exception as e:
    print(f"Error executing the query: {e}")
    conn.rollback()
    exit()

# Close the cursor and connection
print("Closing the database connection...")
cur.close()
conn.close()
print("Database connection closed.")
