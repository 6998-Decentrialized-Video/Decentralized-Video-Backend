import requests

class IPFSWrapper:
    def __init__(self, address='http://127.0.0.1:5001/api/v0'):
        self.address = address

    def add_file(self, file_path):
        with open(file_path, 'rb') as file:
            response = requests.post(f"{self.address}/add", files={'file': file})
        return response.json()['Hash']

    def get_file(self, cid):
        response = requests.post(f"{self.address}/cat?arg={cid}")
        return response.content

    def pin_file(self, cid):
        response = requests.post(f"{self.address}/pin/add?arg={cid}")
        return response.json()

    def unpin_file(self, cid):
        response = requests.post(f"{self.address}/pin/rm?arg={cid}")
        return response.json()

    def list_pinned_files(self):
        response = requests.post(f"{self.address}/pin/ls")
        return response.json()
    
    def delete_file(self, cid):
        """Unpins the file and triggers garbage collection to delete from local node."""
        # Unpin the file first
        unpin_response = self.unpin_file(cid)
        # Trigger garbage collection to remove unpinned data
        gc_response = requests.post(f"{self.address}/repo/gc")
        
        return {
            "unpin": unpin_response,
            "garbage_collection": gc_response.json()
        }