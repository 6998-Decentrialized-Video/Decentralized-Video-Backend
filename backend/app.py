import math
import os
import requests
import json
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS

from web3 import Web3

from mongo_wrapper import MongoDBWrapper



def load_env_vars(file_path='.env.local'):
    """Load environment variables from a file."""
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

load_env_vars()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CORS(app, origins=["http://localhost:3000"])


# WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")
# web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

# CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
# CONTRACT_ABI = json.loads(os.getenv('CONTRACT_ABI'))
# contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

COINBASE_REDIRECT_URI = "http://localhost:8000/auth/callback"
COINBASE_CLIENT_ID = os.getenv("COINBASE_CLIENT_ID")
COINBASE_CLIENT_SECRET = os.getenv("COINBASE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")

mongo = MongoDBWrapper()



@app.route('/loginCoinbase', methods=['POST'])
def login_coinbase():
    coinbase_url = (
        f"https://www.coinbase.com/oauth/authorize"
        f"?response_type=code&"
        f"client_id={COINBASE_CLIENT_ID}&"
        f"redirect_uri={COINBASE_REDIRECT_URI}&scope=wallet:user:read"
    )
    return {"url": coinbase_url}

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

        redirect_url = f"{FRONTEND_URL}/home?token={access_token}"
        return redirect(redirect_url)

        # return jsonify({'message': 'Login successful', 'user': user_info['data']}), 200
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
        ipfs_hash = data.get('ipfs_hash') # from front end
        file_name = data.get('file_name')
        tags = data.get('tags')
        mongo.add_video_metadata(
            session['coinbase_user']['id'],
            file_name,
            ipfs_hash,
            title,
            description,
            tags
        )
        # upload to chain
        # tx_hash = contract.functions.addVideo(title, ipfs_hash).transact({
        #     'from': web3.eth.accounts[0]
        # })

        # tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        # return jsonify({
        #     'message': 'Successfully uploaded metadata',
        #     'transaction_receipt': tx_receipt
        # }), 200
    except Exception as e:
        return jsonify({'error happened while uploading': str(e)}), 500

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
                        ),200
    except Exception as e:
        return jsonify({'error happened while liking a video': str(e)}), 500

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
        return jsonify({'error happened while unliking a video': str(e)}), 500

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
        return jsonify({'error happened while viewing a video': str(e)}), 500

@app.route('/getUserInfo', methods=['GET'])
def get_user_info():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        return jsonify({'user_info': session['coinbase_user']}), 200
    except Exception as e:
        return jsonify({'error happened while getting user info': str(e)}), 500

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
        total_pages = math.ceil(total_videos / limit)
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
    except:
        return jsonify({'error': 'Failed to list videos'}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)