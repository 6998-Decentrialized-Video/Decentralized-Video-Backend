import requests
import os 
import cv2
from tempfile import NamedTemporaryFile

class IPFSWrapper:
    def __init__(self, address='http://127.0.0.1:5001/api/v0'):
        self.address = address

    def add_file(self, file_path, preview_percentage=10):
        """
        Adds a video file to IPFS.
        Automatically generates a preview clip, uploads both the video and preview to IPFS,
        and returns both CIDs.
        """
        # Upload the main video file to IPFS
        with open(file_path, 'rb') as file:
            response = requests.post(f"{self.address}/add", files={'file': file})
        video_cid = response.json().get('Hash')
        
        # Generate and upload the preview clip based on percentage
        preview_path = self.generate_percentage_preview(file_path, percentage=preview_percentage)
        preview_cid = self.add_preview(preview_path)

        # Clean up the temporary preview file after upload
        os.remove(preview_path)

        # Return both video and preview CIDs
        return {
            "video_cid": video_cid,
            "preview_cid": preview_cid
        }

    def generate_percentage_preview(self, video_path, percentage=10):
        """
        Generates a preview clip that is a specified percentage of the video's total duration.
        """
        # Open the video file and retrieve properties
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise Exception("Error: Could not open video.")

        fps = int(video.get(cv2.CAP_PROP_FPS))
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        total_duration = total_frames / fps  # Total duration in seconds

        # Calculate the duration for the preview clip based on percentage
        preview_duration = total_duration * (percentage / 100)
        preview_frame_count = int(preview_duration * fps)

        # Create a temporary file for the preview clip
        with NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            preview_path = temp_file.name
            # Define the codec and create VideoWriter for the preview
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(preview_path, fourcc, fps, (width, height))

            # Read and save frames for the preview duration
            frame_counter = 0
            while frame_counter < preview_frame_count:
                ret, frame = video.read()
                if not ret:
                    break
                out.write(frame)
                frame_counter += 1

            # Release resources
            video.release()
            out.release()
            return preview_path

    def add_preview(self, preview_path):
        """Uploads the generated preview clip to IPFS and returns its CID."""
        with open(preview_path, 'rb') as file:
            response = requests.post(f"{self.address}/add", files={'file': file})
        return response.json().get('Hash')

    def get_file(self, cid):
        """Retrieves a file from IPFS by CID."""
        response = requests.post(f"{self.address}/cat?arg={cid}")
        return response.content

    def pin_file(self, cid):
        """Pins a file to the local IPFS node to prevent it from being garbage collected."""
        response = requests.post(f"{self.address}/pin/add?arg={cid}")
        return response.json()

    def unpin_file(self, cid):
        """Unpins a file from the local IPFS node."""
        response = requests.post(f"{self.address}/pin/rm?arg={cid}")
        return response.json()

    def list_pinned_files(self):
        """Lists all pinned files on the local IPFS node."""
        response = requests.post(f"{self.address}/pin/ls")
        return response.json()
    
    def delete_file(self, cid):
        """Unpins the file and triggers garbage collection to delete it from the local node."""
        unpin_response = self.unpin_file(cid)
        gc_response = requests.post(f"{self.address}/repo/gc")
        return {
            "unpin": unpin_response,
            "garbage_collection": gc_response.json()
        }
