# BTube - A Decentralized Video Platform

This project is a backend implementation for a decentralized video platform. It leverages Ethereum smart contracts, IPFS for decentralized storage, and integrates with Coinbase for user authentication. The backend is built using Python's Flask framework and interacts with MongoDB for metadata storage.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Smart Contract Deployment](#smart-contract-deployment)
- [Running the Application](#running-the-application)
- [Testing the Endpoints](#testing-the-endpoints)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- Python 3.8 or later
- Node.js and NPM (if you have Node.js components)
- IPFS (InterPlanetary File System)
- MongoDB Atlas Account
- MetaMask Wallet (for deploying contracts and testing)
- Infura Account (for connecting to the Ethereum network)
- Coinbase Developer Account (for OAuth integration)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Decentralized-Video-Backend.git
cd Decentralized-Video-Backend
```

### 2. Navigate to the Backend Directory
```bash
cd backend
```

### 3. Set Up a Python Virtual Environment
It's recommended to use a virtual environment to manage dependencies.

#### Using venv
```bash
python3 -m venv venv
```
Activate the virtual environment:

- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```
- On Windows:
  ```bash
  venv\Scripts\activate
  ```

### 4. Install Required Python Packages
Ensure you are in the `/backend` directory where `requirements.txt` is located.
```bash
pip install -r requirements.txt
```

### 5. Install Node.js Dependencies (If Applicable)
If your project includes any Node.js components (like a frontend or IPFS interaction scripts), navigate to the respective directory and run:
```bash
npm install
```

### 6. Install IPFS
Follow the instructions on the [IPFS Documentation](https://docs.ipfs.io/) to install IPFS on your system.

#### Example for macOS (using Homebrew):
```bash
brew install ipfs
ipfs init
```

## Environment Setup

Create a `.env` file in the `/backend` directory to store environment variables.
```bash
touch .env
```
Open the `.env` file with your preferred text editor and add the following variables:

```ini
# Web3 Configuration
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
CONTRACT_ADDRESS=YourContractAddress
PRIVATE_KEY=YourPrivateKey

# Coinbase OAuth Configuration
COINBASE_CLIENT_ID=YourCoinbaseClientID
COINBASE_CLIENT_SECRET=YourCoinbaseClientSecret
COINBASE_REDIRECT_URI=http://localhost:8000/auth/callback

# Flask Configuration
FLASK_SECRET_KEY=YourFlaskSecretKey

# MongoDB Configuration
MONGODB_URI=mongodb+srv://<username>:<password>@yourcluster.mongodb.net/?retryWrites=true&w=majority
```

### Example `.env` File
```ini
# Web3 Configuration
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/123abc456def789ghi012jkl345mno678pqr
CONTRACT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
PRIVATE_KEY=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef

# Coinbase OAuth Configuration
COINBASE_CLIENT_ID=abcdef1234567890abcdef1234567890
COINBASE_CLIENT_SECRET=abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef
COINBASE_REDIRECT_URI=http://localhost:8000/auth/callback

# Flask Configuration
FLASK_SECRET_KEY=your_flask_secret_key_here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://yourusername:yourpassword@cluster0.mongodb.net/?retryWrites=true&w=majority
```

**Important:** Never commit your `.env` file or share your private keys and secrets. This information should remain confidential.

## Smart Contract Deployment

### 1. Install Solidity Compiler (Optional)
If you need to compile the smart contract:

#### Example for macOS (using Homebrew):
```bash
brew tap ethereum/ethereum
brew install solidity
```

### 2. Compile the Smart Contract
Use Remix IDE or Truffle to compile your smart contract and generate the ABI.

#### Using Remix:
1. Open Remix IDE.
2. Paste your smart contract code.
3. Compile it using the appropriate Solidity compiler version.

### 3. Deploy the Smart Contract
Deploy your smart contract to the Ethereum Sepolia testnet.

#### Using Remix:
1. In the **Deploy & Run Transactions** panel, set the environment to **Injected Web3**.
2. Connect MetaMask to Sepolia testnet.
3. Deploy the contract.
4. Confirm the transaction in MetaMask.

### 4. Update the Contract Address and ABI
- **Contract Address:** After deployment, update the `CONTRACT_ADDRESS` in your `.env` file.
- **Contract ABI:** Save the ABI JSON file as `contract_abi.json` in the `/backend` directory.

## Running the Application

### 1. Start the IPFS Daemon
Ensure IPFS is installed and initialized.
```bash
ipfs daemon
```
You should see output indicating that IPFS is running:
```yaml
Initializing daemon...
Kubo version: ...
Repo version: ...
System version: ...
Golang version: ...
...

Daemon is ready
```

### 2. Run the Flask Application
Ensure you are in the `/backend` directory and your virtual environment is activated.
```bash
python app.py
```
You should see output indicating that the server is running:
```text
WEB3_PROVIDER_URI: https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
CONTRACT_ADDRESS: 0xYourContractAddress
PRIVATE_KEY: YourPrivateKey
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
...
 * Running on http://127.0.0.1:8000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: XXX-XXX-XXX
```

## Testing the Endpoints
You can test the API endpoints using Postman, `curl`, or any other HTTP client.

### 1. Upload a Video
#### Endpoint:
`POST http://127.0.0.1:8000/upload`

#### Headers:
```http
Content-Type: application/json
```

#### Body (JSON):
```json
{
  "title": "Test Video",
  "description": "This is a test video.",
  "ipfs_hash": "QmYourIPFSHash",
  "file_name": "test_video.mp4",
  "tags": ["test", "video"]
}
```

#### Example using curl:
```bash
curl -X POST http://127.0.0.1:8000/upload \
-H 'Content-Type: application/json' \
-d '{
      "title": "Test Video",
      "description": "This is a test video.",
      "ipfs_hash": "QmYourIPFSHash",
      "file_name": "test_video.mp4",
      "tags": ["test", "video"]
    }'
```

#### Expected Response:
```json
{
  "message": "Successfully uploaded metadata",
  "transaction_receipt": "0xTransactionHash",
  "video_id": 0
}
```

### 2. Like a Video
#### Endpoint:
`POST http://127.0.0.1:8000/like`

#### Headers:
```http
Content-Type: application/json
```

#### Body (JSON):
```json
{
  "video_id": 0
}
```

#### Example using curl:
```bash
curl -X POST http://127.0.0.1:8000/like \
-H 'Content-Type: application/json' \
-d '{
      "video_id": 0
    }'
```

#### Expected Response:
```json
{
  "message": "Successfully liked video",
  "transaction_receipt": "0xTransactionHash"
}
```

## Troubleshooting

### 1. SSL Handshake Failed (MongoDB Connection)
#### Error Message:
```yaml
SSL handshake failed: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

#### Solution:
- Ensure your `MONGODB_URI` is using `mongodb+srv://`.
- Install the `certifi` package:
  ```bash
  pip install certifi
  ```
- Update the MongoDB client initialization in `mongo_wrapper.py`:
  ```python
  import certifi
  self.client = MongoClient(uri, tlsCAFile=certifi.where())
  ```

### 2. Attribute Errors with Web3.py
#### Error Messages:
- `'Web3' object has no attribute 'toWei'`
- `'SignedTransaction' object has no attribute 'rawTransaction'`

#### Solution:
- Import `to_wei` from `eth_utils`:
  ```python
  from eth_utils import to_wei
  ```
- Use `to_wei` instead of `Web3.toWei`:
  ```python
  'gasPrice': to_wei('20', 'gwei')
  ```
- Update attribute names to match Web3.py version 6.x:
  - Use `raw_transaction` instead of `rawTransaction`:
    ```python
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    ```
  - Use `transaction_hash` instead of `transactionHash` when accessing transaction receipt attributes:
    ```python
    tx_receipt.transaction_hash.hex()
    ```

### 3. Session Not Being Maintained
If you're being redirected to the login page when trying to access protected endpoints:
- Ensure you have a valid session or use token-based authentication.
- For API testing, consider disabling authentication checks temporarily or implement token-based authentication.
