import hashlib
from datetime import datetime
from pymongo import MongoClient

class Bank:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="bank_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.blockchain = self.db["blockchain"]
        self.users = {}
        self.merchants = {}
        self.ifsc_codes = [
            "SBIN0001234", "SBIN0005678", "SBIN0009101",
            "HDFC0002345", "HDFC0006789", "HDFC0001122",
            "ICIC0003456", "ICIC0007890", "ICIC0002233"
        ]
        self.load_from_db()

    def get_collections(self, ifsc):
        return (
            self.db[f"users_{ifsc}"],
            self.db[f"merchants_{ifsc}"]
        )

    def load_from_db(self):
        self.users.clear()
        self.merchants.clear()
        for ifsc in self.ifsc_codes:
            users_coll, merchants_coll = self.get_collections(ifsc)
            for user in users_coll.find():
                mmid = user.pop("_id")
                self.users[(ifsc, mmid)] = user
            for merchant in merchants_coll.find():
                mid = merchant.pop("_id")
                self.merchants[(ifsc, mid)] = merchant

    def save_to_db(self, collection, key, data):
        print(f"Saving to {collection.name}: {key}")
        collection.update_one({"_id": key}, {"$set": data}, upsert=True)

    def generate_mid(self, name, password):
        current_time = datetime.now().isoformat()
        input_string = f"{name}{current_time}{password}"
        sha256_hash = hashlib.sha256()
        sha256_hash.update(input_string.encode('utf-8'))
        mid = sha256_hash.hexdigest()[:16]
        return mid

    def generate_mmid(self, uid, mobile_number):
        input_string = f"{uid}{mobile_number}"
        sha256_hash = hashlib.sha256()
        sha256_hash.update(input_string.encode('utf-8'))
        mmid = sha256_hash.hexdigest()[:16]
        return mmid

    def valid_ifsc(self, ifsc):
        return ifsc in self.ifsc_codes

    def find_user(self, mmid):
        for ifsc in self.ifsc_codes:
            if (ifsc, mmid) in self.users:
                return ifsc, self.users[(ifsc, mmid)]
        return None, None

    def find_merchant(self, mid):
        for ifsc in self.ifsc_codes:
            if (ifsc, mid) in self.merchants:
                return ifsc, self.merchants[(ifsc, mid)]
        return None, None

    def register_user(self, name, ifsc, password, pin, mobile_number, initial_balance=0):
        if not self.valid_ifsc(ifsc):
            return "INVALID IFSC"
        uid = self.generate_mid(name, password)
        mmid = self.generate_mmid(uid, mobile_number)
        if (ifsc, mmid) in self.users:
            return "MMID already exists"
        try:
            initial_balance = int(initial_balance)
        except ValueError:
            return "Invalid balance"
        user_data = {
            "Name": name,
            "IFSC": ifsc,
            "Password": password,
            "Balance": initial_balance,
            "Pin": pin
        }
        self.users[(ifsc, mmid)] = user_data
        users_coll, _ = self.get_collections(ifsc)
        self.save_to_db(users_coll, mmid, user_data)
        return mmid, uid

    def register_merchant(self, name, ifsc, password, initial_balance=0):
        if not self.valid_ifsc(ifsc):
            return "INVALID IFSC"
        mid = self.generate_mid(name, password)
        if (ifsc, mid) in self.merchants:
            return "MID already exists"
        try:
            initial_balance = int(initial_balance)
        except ValueError:
            return "Invalid balance"
        merchant_data = {
            "Name": name,
            "IFSC": ifsc,
            "Password": password,
            "Balance": initial_balance
        }
        self.merchants[(ifsc, mid)] = merchant_data
        _, merchants_coll = self.get_collections(ifsc)
        self.save_to_db(merchants_coll, mid, merchant_data)
        return mid

    def verify_user(self, mmid, pin):
        ifsc, user = self.find_user(mmid)
        return ifsc is not None and user["Pin"] == pin, ifsc

    def verify_merchant(self, mid):
        ifsc, _ = self.find_merchant(mid)
        return ifsc is not None

    def decrypt(self, cipher, priv_key):
        d, n = priv_key
        try:
            return ''.join([chr(pow(char, d, n)) for char in cipher])
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

    def process_transaction(self, encrypted_sender_mmid, encrypted_sender_pin, receiver_mid, amount):
        priv_key = (6305, 32639)  # p=127,q=257,n=32639
        sender_mmid = self.decrypt(encrypted_sender_mmid, priv_key)
        sender_pin = self.decrypt(encrypted_sender_pin, priv_key)
        
        if sender_mmid is None or sender_pin is None:
            return "Decryption failed"
        
        sender_ifsc, sender_data = self.find_user(sender_mmid)
        if sender_ifsc is None:
            return "Invalid sender MMID"
        
        is_valid_user, _ = self.verify_user(sender_mmid, sender_pin)
        if not is_valid_user:
            return "Incorrect Pin"
            
        receiver_ifsc, receiver_data = self.find_merchant(receiver_mid)
        if receiver_ifsc is None:
            return "Merchant not found"
            
        try:
            amount = int(amount)
        except ValueError:
            return "Invalid amount"
            
        sender_bal = sender_data["Balance"]
        if sender_bal < amount:
            return "Error: Insufficient balance"
            
        receiver_bal = receiver_data["Balance"]
        self.merchants[(receiver_ifsc, receiver_mid)]["Balance"] = receiver_bal + amount
        self.users[(sender_ifsc, sender_mmid)]["Balance"] = sender_bal - amount

        sender_coll, _ = self.get_collections(sender_ifsc)
        _, receiver_coll = self.get_collections(receiver_ifsc)
        self.save_to_db(sender_coll, sender_mmid, self.users[(sender_ifsc, sender_mmid)])
        self.save_to_db(receiver_coll, receiver_mid, self.merchants[(receiver_ifsc, receiver_mid)])

        tx_id = hashlib.sha256(f"{sender_mmid}{receiver_mid}{datetime.now()}{amount}".encode()).hexdigest()
        block = {
            "_id": tx_id,
            "Previous Block Hash": self.blockchain.find_one(sort=[("Timestamp", -1)])["_id"] if self.blockchain.count_documents({}) > 0 else "0" * 64,
            "Timestamp": datetime.now().isoformat(),
            "Sender MMID": sender_mmid,
            "Sender IFSC": sender_ifsc,
            "Receiver MID": receiver_mid,
            "Receiver IFSC": receiver_ifsc,
            "Amount": amount
        }
        self.blockchain.insert_one(block)
        print(f"Bank: Transaction logged in Blockchain - {tx_id}")

        return "Transaction successful"

    def get_balance_user(self, mmid, pin):
        is_valid, ifsc = self.verify_user(mmid, pin)
        if is_valid:
            return f"Current Balance: {self.users[(ifsc, mmid)]['Balance']}"
        return "Invalid credentials"

    def get_balance_merchant(self, mid):
        ifsc, merchant = self.find_merchant(mid)
        if ifsc is not None:
            return f"Current Balance: {merchant['Balance']}"
        return "Invalid mid"