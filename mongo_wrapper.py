from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

class MongoDBWrapper:
    def __init__(self, db_name="video_platform", collection_name="videos",  uri="mongodb+srv://zz2915:drdlMkeyyYHupBXz@videodata.vtrh4.mongodb.net/?retryWrites=true&w=majority&appName=videodata"):
        # Initialize MongoDB connection
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def add_video_metadata(self, user_id, file_name, video_cid, preview_cid, title, description, tags, profile_pic_url, visibility="public", pinned=True):
        """Add a new video metadata document to MongoDB, including uploader profile pic URL and preview CID."""
        metadata = {
            "user_id": user_id,
            "profile_pic_url": profile_pic_url,  # Uploader's profile picture URL from Coinbase 
            "file_name": file_name,
            "video_cid": video_cid,  # CID of the main video file
            "preview_cid": preview_cid,  # CID of the generated preview (thumbnail)
            "title": title,
            "description": description,
            "tags": tags,
            "upload_date": datetime.now(),
            "visibility": visibility,
            "pinned": pinned,
            "view_count": 0,
            "like_count": 0,
            "comments": []  # Initialize empty list for comments
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

    def add_comment(self, video_cid, user_id, comment_text, profile_pic_url, parent_comment_id=None):
        """Add a comment to a video, with optional nesting (replies to other comments)."""
        comment = {
            "_id": ObjectId(),  # Unique identifier for the comment
            "user_id": user_id,
            "profile_pic_url": profile_pic_url,  # Commenter's profile picture URL from coinbase 
            "comment": comment_text,
            "timestamp": datetime.now(),
            "replies": []  # Initialize empty list for replies
        }
        
        # If it's a reply to an existing comment
        if parent_comment_id:
            result = self.collection.update_one(
                {"video_cid": video_cid, "comments._id": ObjectId(parent_comment_id)},
                {"$push": {"comments.$.replies": comment}}
            )
        else:
            # Add as a top-level comment
            result = self.collection.update_one({"video_cid": video_cid}, {"$push": {"comments": comment}})
        
        return result.modified_count > 0

    def delete_comment(self, video_cid, comment_id, parent_comment_id=None):
        """Delete a comment from a video by video_cid and comment ID, considering nested comments."""
        if parent_comment_id:
            # Delete a reply to a comment
            result = self.collection.update_one(
                {"video_cid": video_cid, "comments._id": ObjectId(parent_comment_id)},
                {"$pull": {"comments.$.replies": {"_id": ObjectId(comment_id)}}}
            )
        else:
            # Delete a top-level comment
            result = self.collection.update_one(
                {"video_cid": video_cid},
                {"$pull": {"comments": {"_id": ObjectId(comment_id)}}}
            )
        return result.modified_count > 0

    def get_video_metadata(self, video_cid):
        """Retrieve video metadata by video_cid."""
        return self.collection.find_one({"video_cid": video_cid})

    def list_all_videos(self, user_id=None, skip=0, limit=10):
        """List all videos with optional pagination, optionally filtered by user_id."""
        query = {"user_id": user_id} if user_id else {}
        return list(self.collection.find(query).skip(skip).limit(limit))

    def count_videos(self, user_id=None):
        """Count the number of videos, optionally filtered by user_id."""
        query = {"user_id": user_id} if user_id else {}
        return self.collection.count_documents(query)