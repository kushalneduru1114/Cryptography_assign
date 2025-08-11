from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bank import Bank
from machine import Machine
from user import User
from merchant import Merchant
import os

app = Flask(__name__, static_folder='static')  # Set static folder
CORS(app)  # Allow cross-origin requests

shared_bank = Bank()
upi_machine = Machine(shared_bank)

@app.route('/api/user/create', methods=['POST'])
def create_user():
    data = request.json
    user = User("Anonymous", shared_bank, upi_machine)
    result = user.create_account(data['ifsc'], data['password'], data['pin'], data['mobile'], int(data['balance']))
    return jsonify({"message": result})

@app.route('/api/user/transaction', methods=['POST'])
def transaction():
    data = request.json
    user = User("Anonymous", shared_bank, upi_machine)
    result = user.make_transaction(data['mmid'], data['pin'], data['receiverMid'], int(data['amount']))
    return jsonify({"message": result})

@app.route('/api/merchant/qrs', methods=['GET'])
def merchant_qrs():
    # For demo, create a test merchant if none exist
    if not shared_bank.merchants:
        merchant = Merchant("TestMerchant", shared_bank, upi_machine)
        mid = merchant.create_merchant("SBIN0001234", "pass123")
        merchant.generate_qr()
    
    # List all QR images in the static folder
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    qr_files = [f for f in os.listdir(static_dir) if f.endswith('.png')]
    qr_urls = [f"http://localhost:5000/static/{filename}" for filename in qr_files]
    return jsonify(qr_urls)

@app.route('/api/bank/user-balance', methods=['POST'])
def user_balance():
    data = request.json
    result = shared_bank.get_balance_user(data['mmid'], data['pin'])
    return jsonify({"message": result})

@app.route('/api/bank/merchant-balance', methods=['POST'])
def merchant_balance():
    data = request.json
    mid = data['mid']
    if mid in shared_bank.merchants:
        return jsonify({"message": f"Current Balance: {shared_bank.merchants[mid]['Balance']}"})
    return jsonify({"message": "Merchant not found"})

@app.route('/api/bank/blockchain', methods=['GET'])
def blockchain():
    blocks = list(shared_bank.blockchain.find())
    for block in blocks:
        block['_id'] = str(block['_id'])  # Convert ObjectId to string
        block.pop('_id', None)  # Remove MongoDB ObjectId
        # Rename fields to match frontend expectation
        block['SenderMMID'] = block.pop('Sender MMID')
        block['ReceiverMID'] = block.pop('Receiver MID')
        block['Amount'] = block['Amount']
    return jsonify(blocks)

# Serve static files (QR images)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)