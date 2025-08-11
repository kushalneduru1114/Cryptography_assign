import os
import hashlib
import base64
import random
import math
import sympy
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class SHA256:
    @staticmethod
    def hash(data):
        """Generate SHA256 hash of the given data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

class QuantumCryptography:
    """
    Simulation of quantum cryptography concepts, particularly Shor's Algorithm 
    for factoring large numbers, which could break RSA encryption
    """

    @staticmethod
    def gcd(a, b):
        """Calculate greatest common divisor of a and b"""
        while b:
            a, b = b, a % b
        return a

    @staticmethod
    def find_period(x, n):
        """
        Simulate finding the period of f(a) = x^a mod n
        In a real quantum computer, this would use quantum Fourier transform
        """
        # This is a classical simulation - in a quantum setting this would be much faster
        a = 1
        values = {}
        max_iterations = 10000  # Prevent infinite loops

        for i in range(max_iterations):
            val = pow(x, a, n)
            if val in values:
                return a - values[val]
            values[val] = a
            a += 1

        # If no period found, return a large number
        return -1

    @staticmethod
    def simulate_shors_algorithm(n, max_attempts=5):
        """
        Simulate Shor's algorithm to find the prime factors of n
        This is a simplified version for educational purposes
        """
        if n % 2 == 0:
            return 2, n // 2

        for _ in range(max_attempts):
            # Choose random x where 1 < x < n
            x = random.randint(2, n - 1)

            # Calculate GCD of x and n
            g = QuantumCryptography.gcd(x, n)
            if g != 1:
                # Found a factor
                return g, n // g

            # Try to find the period of f(a) = x^a mod n
            r = QuantumCryptography.find_period(x, n)

            if r == -1 or r % 2 != 0:
                # No period found or period is odd, try again
                continue

            # Calculate y = x^(r/2) mod n
            y = pow(x, r // 2, n)

            if y == n - 1:
                # Special case, try again
                continue

            # Calculate potential factors
            factor1 = QuantumCryptography.gcd(y - 1, n)
            factor2 = QuantumCryptography.gcd(y + 1, n)

            if factor1 > 1:
                return factor1, n // factor1
            if factor2 > 1:
                return factor2, n // factor2

        # Could not find factors
        return None, None

# --------------------------------------------
# Added Main Method for RSA Encryption and Breaking a 4-Digit PIN
# --------------------------------------------

if _name_ == "_main_":
    print("=== RSA Encryption and Quantum Attack Simulation ===\n")

    # --- RSA SETUP ---
    # For demonstration we choose two small primes
    p = 61
    q = 53
    n = p * q  # RSA modulus (3233)
    e = 17     # Public exponent
    print("Sample RSA Public Key Parameters:")
    print(f"  p = {p}")
    print(f"  q = {q}")
    print(f"  n (p*q) = {n}")
    print(f"  Public exponent (e) = {e}")
    print("\nEnter a 4-digit PIN to encrypt (e.g., 1234).")

    # Get user input for the PIN
    pin_input = input("Enter 4-digit PIN: ").strip()
    if not (pin_input.isdigit() and len(pin_input) == 4):
        print("Invalid PIN! Please run the program again and enter a 4-digit numeric PIN.")
        exit(1)

    # Convert PIN string to integer
    pin = int(pin_input)

    # --- RSA ENCRYPTION ---
    # Encrypt the PIN using RSA: ciphertext = PIN^e mod n
    ciphertext = pow(pin, e, n)
    print(f"\nEncrypted PIN (as integer ciphertext): {ciphertext}")

    # --- Simulated Quantum Attack using Shor's Algorithm ---
    print("\nAttempting to factor n using simulated Shor's algorithm...")
    factor1, factor2 = QuantumCryptography.simulate_shors_algorithm(n)
    print(factor1, factor2)
    if factor1 is None or factor2 is None:
        print("Failed to factor the RSA modulus n. Quantum attack simulation unsuccessful.")
        exit(1)

    print(f"Factors of n found: {factor1} and {factor2}")

    # --- RSA PRIVATE KEY CALCULATION ---
    # Compute Euler's Totient: phi(n) = (p-1)*(q-1)
    phi = (factor1 - 1) * (factor2 - 1)

    # Compute the private exponent d which is the modular inverse of e modulo phi(n)
    d = sympy.mod_inverse(e, phi)
    print(f"Calculated private exponent (d): {d}")

    # --- RSA DECRYPTION ---
    # Decrypt the ciphertext: decrypted_pin = ciphertext^d mod n
    decrypted_pin = pow(ciphertext, d, n)
    print(f"Decrypted PIN (after factoring and using d): {decrypted_pin}")

    # Verify if the decrypted PIN matches the original
    if decrypted_pin == pin:
        print("\nSuccess! The decrypted PIN matches the original PIN.")
    else:
        print("\nFailure! The decrypted PIN does not match the original PIN.")