from pymongo import MongoClient
from gridfs import GridFSBucket
from flask_jwt_extended import JWTManager

# JWT initialization
jwt = JWTManager()

# MongoDB variables
mongo_client = None
db = None
gridfs_bucket = None


def init_extensions(app):

    global mongo_client
    global db
    global gridfs_bucket

    # Connect to MongoDB
    mongo_client = MongoClient(
        app.config["MONGO_URI"],
        serverSelectionTimeoutMS=10000
    )

    # Select database
    db = mongo_client[
        app.config["DATABASE_NAME"]
    ]

    # Initialize GridFS
    gridfs_bucket = GridFSBucket(db)

    # Initialize JWT
    jwt.init_app(app)

    print("MongoDB client initialized successfully!")