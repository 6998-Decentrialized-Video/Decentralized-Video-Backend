import os

from flask import Flask, request, jsonify
import json
import requests
from web3 import Web3

app = Flask(__name__)

WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")
web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CONTRACT_ABI = json.loads(os.getenv('CONTRACT_ABI'))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

videos = []

@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        ipfs_hash = data.get('ipfs_hash') # from front end
        video_info = {
            'title': title,
            'description': description,
            'ipfs_hash': ipfs_hash
        }
        videos.append(video_info)

        # upload
        tx_hash = contract.functions.addVideo(title, ipfs_hash).transact({
            'from': web3.eth.accounts[0]
        })

        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({
            'message': 'Successfully uploaded metadata',
            'transaction_receipt': tx_receipt
        }), 200
    except Exception as e:
        return jsonify({'error happened while uploading': str(e)}), 500

@app.route('/videos', methods=['GET'])
def get_videos():
    try:
        return jsonify(videos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)