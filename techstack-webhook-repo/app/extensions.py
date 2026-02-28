from pymongo import MongoClient


# Setup MongoDB here

client = MongoClient("mongodb://localhost:27017/")
db = client["webhook_db"]