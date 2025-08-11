import qrcode
from PIL import Image
import os

class Machine:
    def __init__(self):
        self.merchant_qr_codes = {}
        self.speck_key = 0x1918111009080100
        self.qr_dir = os.path.join(os.path.dirname(__file__), 'qr_codes')
        if not os.path.exists(self.qr_dir):
            os.makedirs(self.qr_dir)

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

    def encrypt_mid(self, data):
        data_int = int(data, 16)  # Assumes data is a 16-character hex string
        block1 = (data_int >> 32) & 0xFFFFFFFF
        block2 = data_int & 0xFFFFFFFF
        enc_block1 = self._speck_encrypt(block1, self.speck_key)
        enc_block2 = self._speck_encrypt(block2, self.speck_key)
        return format((enc_block1 << 32) | enc_block2, '016x')

    def makeQR(self, mid, name):
        encrypted_mid = self.encrypt_mid(mid)
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(encrypted_mid)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(self.qr_dir, f"merchant_{name}_{mid}_qr.png")
        qr_img.save(qr_path)
        return qr_path  # Return the file path instead of the image object
    
    # def process_payment(self, encrypted_sender_mmid, encrypted_sender_pin, encrypted_receiver_mid, amount):
    #     response = self.bank.process_transaction(encrypted_sender_mmid, encrypted_sender_pin, encrypted_receiver_mid, amount)
    #     if response == "Transaction successful":
    #         print(f"UPI Machine: Payment successful - {amount} transferred")
    #     else:
    #         print(f"UPI Machine: Payment failed - {response}")
    #     return response