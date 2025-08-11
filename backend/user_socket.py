import socket
import json
import random
from math import gcd

def connect_to_bank():
    client = socket.socket()
    client.connect(('172.16.122.54', 5000))  # Bank's IP
    return client

def connect_to_machine():
    client = socket.socket()
    client.connect(('172.16.122.54', 5001))  # Machine IP
    return client

def send_request(client, request):
    client.send(json.dumps(request).encode('utf-8'))
    response = client.recv(1024).decode('utf-8')
    if not response:
        raise Exception("Received empty response from server")
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Error decoding response: {response}")
        raise Exception(f"Invalid JSON response: {e}")

def register_user():
    client = connect_to_bank()
    name = input("Enter the user's name: ")
    isfc = input("Enter the bank's ISFC code: ")
    password = input("Enter your account's password: ")
    pin = input("Enter your account's pin: ")
    mobile = input("Enter your mobile phone number: ")
    balance = input("Enter your initial balance: ")
    request = {
        'type': 'register_user',
        'name': name,
        'ifsc': isfc,
        'password': password,
        'pin': pin,
        'mobile': mobile,
        'balance': balance
    }
    response = send_request(client, request)
    if response['status'] == 'success':
        mmid = response['mmid']
        print(f"Account created with\nMMID: {mmid}\nUID: {response['uid']}\n")
    else:
        print(f"Failed to create account: {response['message']}")
    client.close()

def encrypt(msg, pub_key):
    e, n = pub_key
    return [pow(ord(char), e, n) for char in msg]

def trans():
    public_key = (353, 32639)  # p=127,q=257,n=32639
    client = connect_to_machine()
    mmid = input("Enter user's MMID: ")
    pin = input("Enter user's pin: ")
    vmid = input("Enter the merchant's VMID: ")
    amount = input("Enter the amount to deduct: ")
    try:
        amount = int(amount)
    except ValueError:
        print("Error: Amount must be an integer")
        client.close()
        return None, None
    encrypted_mmid = encrypt(mmid, public_key)
    encrypted_pin = encrypt(pin, public_key)
    print(f"\nEncrypted MMID: {encrypted_mmid}\nEncrypted Pin: {encrypted_pin}\n")
    request = {
        'type': 'transaction',
        'encrypted_sender_mmid': encrypted_mmid,
        'encrypted_sender_pin': encrypted_pin,
        'encrypted_receiver_mid': vmid,
        'amount': amount
    }
    response = send_request(client, request)
    print(f"Transaction result: {response['message']}\n")
    client.close()
    return encrypted_mmid, encrypted_pin

def modular_exponentiation(base, exponent, modulus):
    result = 1
    base = base % modulus
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulus
        base = (base * base) % modulus
        exponent >>= 1
    return result

def find_period(a, N):
    for r in range(1, N):
        if modular_exponentiation(a, r, N) == 1:
            return r
    return None

def shors_algorithm(N):
    if N % 2 == 0:
        return 2, N // 2
    a = random.randrange(2, N)
    d = gcd(a, N)
    if d > 1:
        return d, N // d
    r = find_period(a, N)
    if r and r % 2 == 0:
        r_half = r // 2
        if modular_exponentiation(a, r_half, N) != N - 1:
            factor1 = gcd(modular_exponentiation(a, r_half, N) + 1, N)
            factor2 = gcd(modular_exponentiation(a, r_half, N) - 1, N)
            if factor1 > 1 and factor2 > 1 and factor1 * factor2 == N:
                return factor1, factor2
    return None, None

def mod_inverse(e, phi):
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    gcd_val, x, _ = extended_gcd(e, phi)
    if gcd_val != 1:
        raise Exception('Modular inverse does not exist')
    return x % phi

def decrypt(cipher, priv_key):
    d, n = priv_key
    return ''.join([chr(pow(char, d, n)) for char in cipher])

def attacker(ciphertext1, ciphertext2):
    public_key = (353, 32639)
    print(f"Encrypted MMID: {ciphertext1}")
    print(f"Encrypted Pin: {ciphertext2}")
    try:
        p, q = shors_algorithm(public_key[1])
        if p is None or q is None:
            print("Failed to factorize modulus")
            return
        phi = (p - 1) * (q - 1)
        d = mod_inverse(public_key[0], phi)
        key = (d, p * q)
        decrypted1 = decrypt(ciphertext1, key)
        decrypted2 = decrypt(ciphertext2, key)
        print(f"Decrypted MMID by the attacker: {decrypted1}\nDecrypted Pin by the attacker: {decrypted2}")
    except Exception as e:
        print(f"Attack failed: {e}")

emmid = []
epin = []
while True:
    func = int(input("Type 1 to register a user\nType 2 to pay a merchant\nType 3 to show vulnerabilities in the encryption using Shor's\nType 4 to exit: "))
    if func == 1:
        register_user()
    elif func == 2:
        result = trans()
        if result:
            emmid, epin = result
    elif func == 3:
        if emmid and epin:
            attacker(emmid, epin)
        else:
            print("No transaction data available to attack")
    elif func == 4:
        break
    else:
        print("Please enter 1, 2, 3, or 4\n")