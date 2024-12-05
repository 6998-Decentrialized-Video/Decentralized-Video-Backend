import math
import os
import requests
import json

from dns.message import make_response
import requests
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS

from web3 import Web3
from eth_utils import to_wei

from mongo_wrapper import MongoDBWrapper

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
# CORS(app)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_DOMAIN="localhost",
)

WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")
web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
with open('contract_abi.json', 'r') as abi_file:
    CONTRACT_ABI = json.load(abi_file)
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
account = web3.eth.account.from_key(PRIVATE_KEY)

COINBASE_REDIRECT_URI = os.getenv("COINBASE_REDIRECT_URI")
COINBASE_CLIENT_ID = os.getenv("COINBASE_CLIENT_ID")
COINBASE_CLIENT_SECRET = os.getenv("COINBASE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")

mongo = MongoDBWrapper()

@app.route('/', methods=['GET'])
def home():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    return "Welcome to BTube - a Decentralized Video Platform!"

@app.route('/loginCoinbase', methods=['GET'])
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
        user_info_headers = {'Authorization': f'Bearer {access_token}',
                             'Content-Type': "application/json"}
        user_info_response = requests.get(user_info_url, headers=user_info_headers)
        user_info = user_info_response.json()

        if 'data' not in user_info:
            return jsonify({'error': 'Failed to obtain user information'}), 400

        session['coinbase_user'] = user_info['data']
        app.logger.info(f"Session set: {session.get('coinbase_user')}")
        response = redirect(f"{FRONTEND_URL}/oauth/callback")
        response.headers[
            'Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

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
        video_cid = data.get('video_cid')
        preview_cid = data.get('preview_cid')
        file_name = data.get('file_name')
        tags = data.get('tags', [])

        profile_pic_url = session['coinbase_user'].get('avatar_url', '')
        user_id = session['coinbase_user']['id']

        mongo.add_video_metadata(
            user_id=user_id,
            file_name=file_name,
            video_cid=video_cid,
            preview_cid=preview_cid,
            title=title,
            description=description,
            tags=tags,
            profile_pic_url=profile_pic_url
        )

        nonce = web3.eth.get_transaction_count(account.address)
        txn = contract.functions.uploadVideo(
            title,
            description,
            video_cid,
            tags
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': to_wei('20', 'gwei')
        })

        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)


        print(f"Transaction hash: {tx_hash.hex()}")

        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(tx_receipt)

        return jsonify({
            'message': 'Successfully uploaded metadata',
            'transaction_receipt': tx_receipt.transactionHash.hex(),
            'video_cid': video_cid
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/like', methods=['POST'])
def like_video():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        data = request.get_json()

        video_cid = data.get('video_cid')
        if not isinstance(video_cid, str):
            return jsonify({'error': 'video_cid must be a string'}), 400

        status = data.get('status')
        try:
            status = int(status)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid status type; must be an integer'}), 400
        if status not in [1, -1]:
            return jsonify({'error': 'Invalid status value; must be 1 or -1'}), 400

        # Use hardcoded user_id for testing
        # user_id = "079dc906-9f13-4aaa-892e-d1f515925265"

        user_id = session['coinbase_user']['id']
        user_id_hash = web3.keccak(text=user_id)

        if not isinstance(user_id_hash, bytes) or len(user_id_hash) != 32:
            return jsonify({'error': 'user_id_hash must be bytes32'}), 500

        # Build and send the transaction
        nonce = web3.eth.get_transaction_count(account.address)
        txn = contract.functions.setLikeStatus(
            video_cid,
            user_id_hash,
            status
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': to_wei('20', 'gwei')
        })

        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if status == 1:
            likes = mongo.increment_like_count(video_cid)
        else:
            likes = mongo.decrement_like_count(video_cid)

        return jsonify({
            'message': 'Successfully updated like status',
            'transaction_receipt': tx_receipt.transactionHash.hex(),
            'likes': likes
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/view', methods=['POST'])
def view_video():
    if 'coinbase_user' not in session:
        return redirect(url_for('login_coinbase'))
    try:
        data = request.get_json()

        video_cid = data.get('video_cid')
        if not isinstance(video_cid, str):
            return jsonify({'error': 'video_cid must be a string'}), 400

        # Use hardcoded user_id for testing
        # user_id = "079dc906-9f13-4aaa-892e-d1f515925265"

        user_id = session['coinbase_user']['id']
        user_id_hash = web3.keccak(text=user_id)

        # Build and send the transaction
        nonce = web3.eth.get_transaction_count(account.address)
        txn = contract.functions.viewVideo(
            video_cid,
            user_id_hash
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': to_wei('20', 'gwei')
        })

        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        views = mongo.increment_view_count(video_cid)
        response = {
            'message': 'Successfully viewed video',
            'transaction_receipt': tx_receipt.transactionHash.hex(),
            'views': views
        }
        print(response)
        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getUserInfo', methods=['GET'])
def get_user_info():
    if 'coinbase_user' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    try:
        return jsonify({'user_info': session['coinbase_user']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('user_id')
    user_avatar = mongo.get_profile_pic_url(user_id)
    try:
        return jsonify({'user_id': user_id, 'user_profile_pic':user_avatar}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/video', methods=['GET'])
def get_video():
    cid = request.args.get('cid')
    try:
        video_data = mongo.get_video_metadata(cid)
        video_data['_id'] = str(video_data['_id'])
        for comment in video_data['comments']:
            comment['_id'] = str(comment['_id'])
            for reply in comment['replies']:
                reply['_id'] = str(reply['_id'])
        return jsonify({'video_data': video_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/videos', methods=['GET'])
def list_videos():
    user_id = request.args.get('user_id', default=None)
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    if page < 1 or limit < 1:
        return jsonify(
            {'error': 'Page and limit must be positive integers'}), 400

    skip = (page - 1) * limit

    try:
        total_videos = mongo.count_videos(user_id)
        print(total_videos)
        videos = mongo.list_all_videos(user_id=user_id, skip=skip, limit=limit)
        print(videos)
        total_pages = max(1, (total_videos + limit - 1) // limit)
        has_next_page = page < total_pages
        has_previous_page = page > 1

        for video in videos:
            video['_id'] = str(video['_id'])
            for comment in video['comments']:
                comment['_id'] = str(comment['_id'])
                for reply in comment['replies']:
                    reply['_id'] = str(reply['_id'])
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
