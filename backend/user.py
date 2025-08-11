class User:
    def __init__(self, name, bank):
        self.Name = name
        self.bank = bank
        self.Accounts = []
        self.speck_key = 0x1918111009080100

    def _speck_encrypt(self, plaintext, key):
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

    def encrypt_data(self, data):
        data_int = int(data)  # Convert string to integer directly
        block1 = (data_int >> 32) & 0xFFFFFFFF
        block2 = data_int & 0xFFFFFFFF
        enc_block1 = self._speck_encrypt(block1, self.speck_key)
        enc_block2 = self._speck_encrypt(block2, self.speck_key)
        return format((enc_block1 << 32) | enc_block2, '016x')

    def create_account(self, ifsc, password, pin, mobile_number, initial_balance=0):
        for mmid in self.Accounts:
            existing_ifsc = self.bank.users[mmid]["IFSC"]
            if existing_ifsc == ifsc:
                print(f"Account creation failed: {self.Name} already has an account with IFSC {ifsc}")
                return f"Account creation failed: {self.Name} already has an account with IFSC {ifsc}"
        mmid = self.bank.register_user(self.Name, ifsc, password, pin, mobile_number, initial_balance)
        if mmid in ["MMID already exists", "INVALID IFSC"]:
            print(f"Account creation failed: {mmid}")
            return f"Account creation failed: {mmid}"
        print(f"Account created successfully. MMID: {mmid}")
        self.Accounts.append(mmid)
        return mmid

    def make_transaction(self, mmid, pin, encrypted_receiver_mid, amount,machine):
        if mmid not in self.Accounts:
            return "Invalid MMID"
        encrypted_mmid = self.encrypt_data(mmid)
        encrypted_pin = self.encrypt_data(pin)
        return machine.process_payment(encrypted_mmid, encrypted_pin, encrypted_receiver_mid, amount)

# if __name__ == "__main__":
#     from bank import Bank
#     from merchant import Merchant
#     shared_bank = Bank(mongo_uri="mongodb://localhost:27017/", db_name="bank_db")
#     user1 = User("Vivek Mudireddy", shared_bank)
    
#     mmid2 = user1.create_account("HDFC0002345", "pass304", "8364", "9876543212", 4000)

#     shared_bank.close()