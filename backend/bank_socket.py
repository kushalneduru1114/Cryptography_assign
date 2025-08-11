import socket
import threading
import json
from bank import Bank

bank = Bank()

def handle_client(client_socket, address):
    print(f"Connected to {address}")
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            request = json.loads(data)
            response = {}

            if request['type'] == 'register_user':
                mmid, uid = bank.register_user(
                    request['name'], request['ifsc'], request['password'],
                    request['pin'], request['mobile'], request.get('balance', 0)
                )
                response = {'status': 'success', 'mmid': mmid, 'uid': uid} if mmid not in ["INVALID IFSC", "MMID already exists", "Invalid balance"] else {'status': 'error', 'message': mmid}
                if response['status'] == 'success':
                    print(f"Successfully registered a user [{request['name']},{request['ifsc']},{request['password']},{request['pin']},{request['mobile']}]")

            elif request['type'] == 'register_merchant':
                mid = bank.register_merchant(
                    request['name'], request['ifsc'], request['password'], request.get('balance', 0)
                )
                response = {'status': 'success', 'mid': mid} if mid not in ["INVALID IFSC", "MID already exists", "Invalid balance"] else {'status': 'error', 'message': mid}
                if response['status'] == 'success':
                    print(f"Successfully registered a merchant [{request['name']},{request['ifsc']},{request['password']}]")

            elif request['type'] == 'transaction':
                print(f"MMID: {request['encrypted_sender_mmid']}\nPin: {request['encrypted_sender_pin']}\nReceiver MID: {request['receiver_mid']}")
                result = bank.process_transaction(
                    request['encrypted_sender_mmid'], request['encrypted_sender_pin'],
                    request['receiver_mid'], request['amount']
                )
                response = {'status': 'success', 'message': result} if result == "Transaction successful" else {'status': 'error', 'message': result}

            elif request['type'] == 'get_balance_user':
                result = bank.get_balance_user(request['mmid'], request['pin'])
                response = {'status': 'success', 'balance': result} if "Current Balance" in result else {'status': 'error', 'message': result}
            
            elif request['type'] == 'get_balance_merchant':
                result = bank.get_balance_merchant(request['mid'])
                response = {'status': 'success', 'balance': result} if "Current Balance" in result else {'status': 'error', 'message': result}

            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Error with {address}: {e}")
            response = {'status': 'error', 'message': str(e)}
            client_socket.send(json.dumps(response).encode('utf-8'))
            break
    client_socket.close()

def start_bank_server():
    server = socket.socket()
    server.bind(('172.16.122.54', 5000))  # Bank's IP
    server.listen(5)
    print("Bank server is running")

    while True:
        client_socket, address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()

if __name__ == "__main__":
    start_bank_server()