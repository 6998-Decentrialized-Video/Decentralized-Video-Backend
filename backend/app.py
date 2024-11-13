import os
import json
import requests
from flask import Flask, request, jsonify, redirect, url_for, session
from web3 import Web3

from mongo_wrapper import MongoDBWrapper

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Initialize Web3
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")
web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

# Load Contract ABI
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
with open('contract_abi.json', 'r') as abi_file:
    CONTRACT_ABI = json.load(abi_file)
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Set up account
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
account = web3.eth.account.from_key(PRIVATE_KEY)

# Coinbase OAuth configuration
COINBASE_REDIRECT_URI = os.getenv("COINBASE_REDIRECT_URI")
COINBASE_CLIENT_ID = os.getenv("COINBASE_CLIENT_ID")
COINBASE_CLIENT_SECRET = os.getenv("COINBASE_CLIENT_SECRET")

mongo = MongoDBWrapper()

@app.route('/loginCoinbase', methods=['GET'])
def login_coinbase():
    return redirect(f"https://www.coinbase.com/oauth/authorize"
                    f"?response_type=code&"
                    f"client_id={COINBASE_CLIENT_ID}&"
                    f"redirect_uri={COINBASE_REDIRECT_URI}&scope=wallet:user:read")

@app.route('/auth/callback', methods=['GET'])
def coinbase_callback():
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400

        token_url = 'https://api.coinbase.com/oauth/token'
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': COINBASE_CLIENT_ID,
            'client_secret': COINBASE_CLIENT_SECRET,
            'redirect_uri': COINBASE_REDIRECT_URI
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_response = requests.post(token_url, data=data, headers=headers)
        token_response_data = token_response.json()

        if 'access_token' not in token_response_data:
            return jsonify({'error': 'Failed to obtain access token'}), 400

        access_token = token_response_data['access_token']
        user_info_url = 'https://api.coinbase.com/v2/user'
        user_info_headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=user_info_headers)
        user_info = user_info_response.json()

        if 'data' not in user_info:
            return jsonify({'error': 'Failed to obtain user information'}), 400

        session['coinbase_user'] = user_info['data']

        return jsonify({'message': 'Login successful', 'user': user_info['data']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        ipfs_hash = data.get('ipfs_hash')  # From front end
        file_name = data.get('file_name')
        tags = data.get('tags', [])
        profile_pic_url = session['coinbase_user'].get('avatar_url', '')
        user_id = session['coinbase_user']['id']

        # Add video metadata to MongoDB
        mongo.add_video_metadata(
            user_id=user_id,
            file_name=file_name,
            video_cid=ipfs_hash,
            preview_cid='',  # Update this if you have a preview CID
            title=title,
            description=description,
            tags=tags,
            profile_pic_url=profile_pic_url
        )

        # Upload to blockchain
        nonce = web3.eth.get_transaction_count(account.address)
        txn = contract.functions.uploadVideo(
            title,
            description,
            ipfs_hash,
            tags
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': web3.toWei('20', 'gwei')
        })

        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        return jsonify({
            'message': 'Successfully uploaded metadata',
            'transaction_receipt': tx_receipt.hex()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/like', methods=['POST'])
def like_video():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        data = request.get_json()
        cid = data.get('cid')
        likes = mongo.increment_like_count(cid)
        return jsonify({'message': 'Successfully liked video',
                        'likes': likes}
                        ), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/unlike', methods=['POST'])
def unlike_video():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        data = request.get_json()
        cid = data.get('cid')
        likes = mongo.decrement_like_count(cid)
        return jsonify({'message': 'Successfully unliked video',
                         'likes': likes}
                        ), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view', methods=['POST'])
def view_video():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        data = request.get_json()
        cid = data.get('cid')
        views = mongo.increment_view_count(cid)
        return jsonify({'message': 'Successfully viewed video',
                        'views': views}
                        ), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/getUserInfo', methods=['GET'])
def get_user_info():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        return jsonify({'user_info': session['coinbase_user']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/videos', methods=['GET'])
def list_videos():
    user_id = request.args.get('user_id', default=None)
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    if page < 1 or limit < 1:
        return jsonify(
            {'error': 'Page and limit must be positive integers'}), 400

    skip = (page - 1) * limit

    try:
        total_videos = mongo.count_videos(user_id)
        videos = mongo.list_all_videos(user_id=user_id, skip=skip, limit=limit)
        total_pages = max(1, (total_videos + limit - 1) // limit)
        has_next_page = page < total_pages
        has_previous_page = page > 1

        response = {
            'videos': videos,
            'page': page,
            'limit': limit,
            'total_videos': total_videos,
            'total_pages': total_pages,
            'has_next_page': has_next_page,
            'has_previous_page': has_previous_page
        }
        return jsonify(response)
    except ValueError:
        return jsonify({'error': 'Page and limit must be valid integers'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
