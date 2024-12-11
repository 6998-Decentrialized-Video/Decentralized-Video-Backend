import os
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
#os.environ["MONGODB_URI"] = "mongodb+srv://zz2915:drdlMkeyyYHupBXz@videodata.vtrh4.mongodb.net/?retryWrites=true&w=majority&appName=videodata"
class MongoDBWrapper:
    def __init__(self, db_name="video_platform", collection_name="videos"):
        uri = os.getenv("MONGODB_URI")
        print(uri)
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.user_profile = self.db["user_profile"]

    def get_user_info(self,user_id):
        """
        get the user profile metadata by user_id
        """ 
        user_profile = self.user_profile.find_one({"user_id": user_id})
        return user_profile
    
    def create_user_profile(self, user_id, user_name,profile_pic_url):
        """
        Create a new user profile after log in 
        """
        existing_profile = self.user_profile.find_one({"user_id": user_id})

        if existing_profile:
            print("User profile already exists.")
            return existing_profile  # Return existing profile if found

        # Create a new profile
        new_profile = {
            "user_id": user_id,
            "user_name":user_name,
            "profile_pic_url": profile_pic_url,
            "liked_videos": [],
            "viewed_videos": [],
            "uploaded_videos": []
        }

        # add it to the collection 
        self.user_profile.insert_one(new_profile)
        print("User profile created successfully.")
        return new_profile


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
        
        # update the uploaded video section in user profile 
        self.user_profile.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "uploaded_videos": {
                    "videoCid": video_cid,
                    "timestamp": datetime.now()
                }
            }
        },
        upsert=True  # Ensure the user profile exists
        )

        return str(result.inserted_id)  # Return the ID of the inserted document

    def increment_view_count(self, video_cid, user_id):
        """
        Increment the view count for a video and add the video to the user's viewed videos in the user_profile schema.
        """
        result = self.collection.update_one(
            {"video_cid": video_cid},
            {"$inc": {"view_count": 1}}
        )
        if result.matched_count < 1:
            raise ValueError(f"No document found with video_cid: {video_cid}")

        # Add the video to the user's viewed videos in user_profile
        self.user_profile.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "viewed_videos": {
                        "videoCid": video_cid,
                        "timestamp": datetime.now()
                    }
                }
            },
            upsert=True  
        )

        # return the updated view count
        views = self.collection.find_one({"video_cid": video_cid}, {"_id": 0, "view_count": 1})
        return views.get("view_count", 0)
        
    def has_liked(self, video_cid, user_id):
        """
        check if the user has liked the video, return True if the user has liked it 
        """
        user_profile = self.user_profile.find_one({"user_id": user_id})
        print(user_profile)
        if user_profile:
            for liked_video in user_profile.get("liked_videos", []):
                if liked_video["videoCid"] == video_cid:
                    return True
        return False

    def has_liked(self, video_cid, user_id):
        interaction = self.db.user_interactions.find_one(
            {"user_id": user_id, "likedVideos.videoCid": video_cid},
            {"likedVideos.$": 1}
        )
        if interaction:
            current_status = interaction["likedVideos"][0]["status"]
            return current_status == 1

    def increment_like_count(self, video_cid, user_id):
        """
        Increment the like count for a video 
        """
        # Check if the videoCid is already liked by the user
        user_profile = self.user_profile.find_one({"user_id": user_id, "liked_videos.videoCid": video_cid})
        if user_profile:
            # Video is already liked; do nothing
            likes = self.collection.find_one({"video_cid": video_cid}, {"_id": 0, "like_count": 1})
            return likes.get("like_count", 0)

        # Add the video to the user's liked_videos
        self.user_profile.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "liked_videos": {
                        "videoCid": video_cid,
                        "timestamp": datetime.now()
                    }
                }
            },
            upsert=True  # Ensure the user profile exists
        )

        # Increment the like count in the videos collection
        self.collection.update_one({"video_cid": video_cid}, {"$inc": {"like_count": 1}})

        # Return the updated like count
        likes = self.collection.find_one({"video_cid": video_cid}, {"_id": 0, "like_count": 1})
        return likes.get("like_count", 0)


    def decrement_like_count(self, video_cid, user_id):
        """
        Decrement the like count for a video 
        """
        # Check if the videoCid is already liked - we only do unlike 
        user_profile = self.user_profile.find_one({"user_id": user_id, "liked_videos.videoCid": video_cid})
        if not user_profile:
            # Video is not liked; do nothing
            likes = self.collection.find_one({"video_cid": video_cid}, {"_id": 0, "like_count": 1})
            return likes.get("like_count", 0)

        # Remove the video from the user's liked_videos
        self.user_profile.update_one(
            {"user_id": user_id},
            {"$pull": {"liked_videos": {"videoCid": video_cid}}}
        )

        # Decrement the like count in the videos collection (ensure it doesn't go below 0)
        self.collection.update_one(
            {"video_cid": video_cid, "like_count": {"$gt": 0}},  
            {"$inc": {"like_count": -1}}
        )
        
        # Return the updated like count
        likes = self.collection.find_one({"video_cid": video_cid}, {"_id": 0, "like_count": 1})
        return likes.get("like_count", 0)



    def add_comment(self, video_cid, user_id, comment_text, profile_pic_url, parent_comment_id=None):
        """Add a comment to a video, with optional nesting (replies to other comments)."""
        comment = {
            "_id": ObjectId(),  # Unique identifier for the comment
            "user_id": user_id,
            "profile_pic_url": profile_pic_url,  # Commenter's profile picture URL from Coinbase 
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
    

    def list_all_comments(self, video_cid):
        """List all comments for a specific video."""
        video = self.collection.find_one({"video_cid": video_cid})
        if not video:
            raise ValueError(f"Video with video_cid {video_cid} does not exist.")
        
        comments = video.get("comments", [])
        if not comments:
            return []  # Return an empty list if no comments exist
        
        for comment in comments:
            comment['_id'] = str(comment['_id'])
            for reply in comment.get('replies', []):
                reply['_id'] = str(reply['_id'])
    
        
        sorted_comments = sorted(comments, key=lambda x: x.get("timestamp", datetime.min))
        return sorted_comments


    def get_video_metadata(self, video_cid):
        """Retrieve video metadata by video_cid."""
        # print("meta", video_cid)
        return self.collection.find_one({"video_cid": video_cid})

    def list_all_videos(self, user_id=None, skip=0, limit=10):
        """List all videos with optional pagination, optionally filtered by user_id."""
        query = {"user_id": user_id} if user_id else {}
        return list(self.collection.find(query).skip(skip).limit(limit))

    def count_videos(self, user_id=None):
        """Count the number of videos, optionally filtered by user_id."""
        query = {"user_id": user_id} if user_id else {}
        return self.collection.count_documents(query)
    
    def get_profile_pic_url(self, user_id):
        """Retrieve the profile picture URL for a given user ID."""
        user_data = self.collection.find_one({"user_id": user_id}, {"profile_pic_url": 1})
        if not user_data:
            raise ValueError(f"No user found with user_id: {user_id}")
        return user_data.get("profile_pic_url")
