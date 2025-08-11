import socket
import threading
import json
import qrcode
import os
import datetime

def connect_to_bank():
    client = socket.socket()
    client.connect(('172.16.122.54', 5000))  # Bank's IP
    return client

def send_request(client, request):
    client.send(json.dumps(request).encode('utf-8'))
    response = client.recv(1024).decode('utf-8')
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print("Error: Invalid response from server")
        return {'status': 'error', 'message': 'Invalid server response'}

def speck_encrypt(plaintext, key):
    x = (plaintext >> 16) & 0xFFFF
    y = plaintext & 0xFFFF
    k = [key & 0xFFFF, (key >> 16) & 0xFFFF, (key >> 32) & 0xFFFF, (key >> 48) & 0xFFFF]
    for i in range(22):
        x = (x >> 7 | x << 9) & 0xFFFF
        x = (x + y) & 0xFFFF
        x = x ^ k[i % 4]
        y = (y << 2 | y >> 14) & 0xFFFF
        y = y ^ x
    return (x << 16) | y

def speck_decrypt(ciphertext, key):
    x = (ciphertext >> 16) & 0xFFFF
    y = ciphertext & 0xFFFF
    k = [key & 0xFFFF, (key >> 16) & 0xFFFF, (key >> 32) & 0xFFFF, (key >> 48) & 0xFFFF]
    for i in range(21, -1, -1):
        y = y ^ x
        y = (y >> 2 | y << 14) & 0xFFFF
        x = x ^ k[i % 4]
        x = (x - y) & 0xFFFF
        x = (x << 7 | x >> 9) & 0xFFFF
    return (x << 16) | y

def encrypt_mid(data):
    current_datetime = datetime.datetime.now()
    datetime_str = current_datetime.strftime("%Y%m%d%H%M%S")
    datetime_int = int(datetime_str, 10)
    data_int = int(data, 16)
    combined_data = (data_int ^ datetime_int) & 0xFFFFFFFFFFFFFFFF
    speck_key = 0x1918111009080100
    block1 = (combined_data >> 32) & 0xFFFFFFFF
    block2 = combined_data & 0xFFFFFFFF
    enc_block1 = speck_encrypt(block1, speck_key)
    enc_block2 = speck_encrypt(block2, speck_key)
    encrypted_result = (enc_block1 << 32) | enc_block2
    return format(encrypted_result, '016x'), datetime_str

def decrypt_mid(encrypted_mid, timestamp):
    try:
        enc_int = int(encrypted_mid, 16)
        speck_key = 0x1918111009080100
        block1 = (enc_int >> 32) & 0xFFFFFFFF
        block2 = enc_int & 0xFFFFFFFF
        dec_block1 = speck_decrypt(block1, speck_key)
        dec_block2 = speck_decrypt(block2, speck_key)
        decrypted_int = (dec_block1 << 32) | dec_block2
        timestamp_int = int(timestamp, 10)
        original_mid = (decrypted_int ^ timestamp_int) & 0xFFFFFFFFFFFFFFFF
        return format(original_mid, '016x')
    except ValueError:
        print("Error: Invalid QR data")
        return None

def makeQR(mid, name):
    encrypted_mid, timestamp = encrypt_mid(mid)
    print(f"VMID is {encrypted_mid}")
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(encrypted_mid)
    qr.make(fit=True)
    qr_dir = os.path.join(os.path.dirname(__file__), 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(qr_dir, f"merchant_{name}_{mid}_qr.png")
    qr_img.save(qr_path)
    return qr_path, timestamp

def generate_qr(mid, name):
    qr_path, timestamp = makeQR(mid, name)
    print(f"QR code generated for {mid}")
    return qr_path, timestamp 

def register_merchant():
    client = connect_to_bank()
    name = input("Enter the merchant's name: ")
    isfc = input("Enter the bank's ISFC code: ")
    password = input("Enter your account's password: ")
    balance = input("Enter your initial balance: ")
    request = {
        'type': 'register_merchant',
        'name': name,
        'ifsc': isfc,
        'password': password,
        'balance': balance
    }
    response = send_request(client, request)
    if response['status'] == 'success':
        new_mid = response['mid']
        print(f"Merchant registered with MID: {new_mid}\n")
    else:
        print(f"Failed to register: {response['message']}")
    client.close()
    
def get_merchant_balance(client):
    mid = input("Enter the VMID from the QR code: ")
    request = {
        'type': 'get_balance_merchant',
        'mid': mid
    }
    response = send_request(client, request)
    if response['status'] == 'success':
        print(f"Balance left = {response['balance']}")
    else:
        print(f"{response['message']}")

def handle_client(client_socket, address, time):
    bank_client = connect_to_bank()
    while True:
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            break
        try:
            request = json.loads(data)
            if request['type'] == 'transaction':
                receiver_mid = decrypt_mid(request['encrypted_receiver_mid'], time)
                if receiver_mid is None:
                    client_socket.send(json.dumps({'status': 'error', 'message': 'Invalid QR code'}).encode('utf-8'))
                    break
                bank_request = {
                    'type': 'transaction',
                    'encrypted_sender_mmid': request['encrypted_sender_mmid'],
                    'encrypted_sender_pin': request['encrypted_sender_pin'],
                    'receiver_mid': receiver_mid,
                    'amount': request['amount']
                }
                result = send_request(bank_client, bank_request)
                client_socket.send(json.dumps(result).encode('utf-8'))
                if result['status'] == 'success':
                    print("Transaction Successful\n")
                    bank_client.close()
                    client_socket.close()
                    break
                else:
                    print(f"Transaction Failed: {result['message']}\n")
        except Exception as e:
            print(f"Error handling client: {e}")
            client_socket.send(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            break
    client_socket.close()

def forward_transaction():
    server = socket.socket()
    server.bind(('172.16.122.54', 5001))  # Machine IP
    server.listen(5)
    print("Merchant server is running")
    mid = input("Enter Merchant's MID: ")
    name = input("Enter merchant's name: ")
    qr_path, time = generate_qr(mid, name)
    print(f"QR generated in the qr_codes folder\n")
    client_socket, address = server.accept()
    handle_client(client_socket, address, time)

while True:
    func = int(input("Type 1 to register a merchant\nType 2 to initiate a transaction\nType 3 to turn the server off: "))
    if func == 1:
        register_merchant()
    elif func == 2:
        forward_transaction()
    elif func == 3:
        break
    else:
        print("Please enter 1, 2, or 3\n")