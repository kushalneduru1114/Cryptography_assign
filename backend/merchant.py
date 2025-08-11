class Merchant:
    def __init__(self, name, bank, machine):
        self.Name = name
        self.bank = bank
        self.machine = machine
        self.mid = "nil"
        self.qr = "nil"
    
    def create_merchant(self, ifsc, password, initial_balance=0):
        if self.mid != "nil":
            print(f"Already a merchant with MID {self.mid}")
            return f"Already a merchant with MID {self.mid}"
        mid = self.bank.register_merchant(self.Name, ifsc, password, initial_balance)
        if mid in ["MID already exists", "INVALID IFSC"]:
            print(f"Merchant creation failed: {mid}")
            return f"Merchant creation failed: {mid}"
        print(f"Merchant registered successfully with MID {mid}")
        self.mid = mid
        return mid
         
    def generate_qr(self):
        if self.qr != "nil":
            print("A QR is already present")
            return "A QR is already present"
        if self.mid == "nil":
            print("No merchant registered yet")
            return "No merchant registered"
        self.qr = self.machine.makeQR(self.mid, self.Name)
        print(f"QR code generated for {self.Name}")
        return self.qr

# if __name__ == "__main__":
#     from bank import Bank
#     from machine import Machine
#     shared_bank = Bank(mongo_uri="mongodb://localhost:27017/", db_name="bank_db")
#     upi_machine = Machine(shared_bank)
#     mtest = Merchant("Naturals", shared_bank, upi_machine)
#     mtest.create_merchant("HDFC0002345", "SatyNaty", 850)
#     yumpyQR = mtest.generate_qr()
    