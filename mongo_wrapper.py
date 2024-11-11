from pymongo import MongoClient
from datetime import datetime

class MongoDBWrapper:
    def __init__(self, db_name="video_platform", collection_name="videos", uri="mongodb+srv://zz2915:drdlMkeyyYHupBXz@videodata.vtrh4.mongodb.net/?retryWrites=true&w=majority&appName=videodata"):
        # Initialize MongoDB connection
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def add_video_metadata(self, user_id, file_name, cid, title, description, tags, visibility="public", pinned=True):
        """Add a new video metadata document to MongoDB."""
        metadata = {
            "user_id": user_id,
            "file_name": file_name,
            "cid": cid,
            "title": title,
            "description": description,
            "tags": tags,
            "upload_date": datetime.now(),
            "visibility": visibility,
            "pinned": pinned,
            "view_count": 0,   # initialize view count to 0
            "like_count": 0,   # initialize like count to 0
            "comments": []
        }
        result = self.collection.insert_one(metadata)
        return str(result.inserted_id)  # Return the ID of the inserted document

    def get_video_metadata(self, cid):
        """Retrieve video metadata by CID."""
        return self.collection.find_one({"cid": cid})

    def increment_view_count(self, cid):
        """Increment the view count for a video by CID."""
        result = self.collection.update_one({"cid": cid}, {"$inc": {"view_count": 1}})
        if result.matched_count < 1:
            raise ValueError(f"No document found with CID: {cid}")
        views = self.collection.find_one({"cid": cid})
        return views

    def increment_like_count(self, cid):
        """Increment the like count for a video by CID."""
        result = self.collection.update_one({"cid": cid}, {"$inc": {"like_count": 1}})
        if result.matched_count < 1:
            raise ValueError(f"No document found with CID: {cid}")
        likes = self.collection.find_one({"cid": cid})
        return likes

    def decrement_like_count(self, cid):
        """Decrement the like count for a video by CID (ensuring it doesn't go below zero)."""
        result = self.collection.update_one({"cid": cid, "like_count": {"$gt": 0}}, {"$inc": {"like_count": -1}})
        if result.matched_count < 1:
            raise ValueError(f"No document found with CID: {cid}")
        likes = self.collection.find_one({"cid": cid})
        return likes

    def add_comment(self, cid, user_id, comment_text):
        """Add a comment to a video."""
        comment = {
            "user_id": user_id,
            "comment": comment_text,
            "timestamp": datetime.now()
        }
        result = self.collection.update_one({"cid": cid}, {"$push": {"comments": comment}})
        return result.modified_count > 0

    def delete_comment(self, cid, comment_timestamp):
        """Delete a comment from a video by CID and comment timestamp."""
        result = self.collection.update_one(
            {"cid": cid},
            {"$pull": {"comments": {"timestamp": comment_timestamp}}}
        )
        return result.modified_count > 0  # Return True if deletion was successful

    def delete_video_metadata(self, cid):
        """Delete video metadata by CID."""
        result = self.collection.delete_one({"cid": cid})
        return result.deleted_count > 0  # Return True if deletion was successful

    def list_all_videos(self, user_id=None, skip=0, limit=10):
        """List all videos with optional pagination, optionally filtered by user_id."""
        query = {"user_id": user_id} if user_id else {}
        return list(self.collection.find(query).skip(skip).limit(limit))

    def count_videos(self, user_id=None):
        """Count the number of videos, optionally filtered by user_id."""
        query = {"user_id": user_id} if user_id else {}
        return self.collection.count_documents(query)