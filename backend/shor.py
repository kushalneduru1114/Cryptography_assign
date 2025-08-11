import random
from math import gcd

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

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def generate_prime(start=100, end=300):
    while True:
        p = random.randint(start, end)
        if is_prime(p):
            return p

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

def generate_keys():
    p = 127
    q = 257
    while p == q:
        q = generate_prime()
    n = p * q
    phi = (p - 1) * (q - 1)
    e = generate_prime(3,phi-1)
    print(f"p={p},q={q},n={n}")
    if gcd(e, phi) != 1:
        e = 3
        while gcd(e, phi) != 1:
            e += 2
    d = mod_inverse(e, phi)
    print(f"d={d}")
    return (e, n), (d, n)

def encrypt(msg, pub_key):
    e, n = pub_key
    return [pow(ord(char), e, n) for char in msg]

def decrypt(cipher, priv_key):
    d, n = priv_key
    return ''.join([chr(pow(char, d, n)) for char in cipher])

def attacker(public_key,ciphertext):
    p,q = shors_algorithm(public_key[1])
    phi = (p - 1) * (q - 1)
    d=mod_inverse(public_key[0],phi)
    key=d,p*q
    decrypted=decrypt(ciphertext,key)
    print(f"Decrypted text by the attacker: {decrypted}")

###########################################################################################

#p=127,q=257,n=32639

public_key, private_key = generate_keys()

print(public_key)
print(private_key)


message = "1041679551518590"
print("Original:", message)

cipher = encrypt(message, public_key)
print("Encrypted:", cipher)

#attacker(public_key,cipher)

decrypted = decrypt(cipher, private_key)
print("Decrypted:", decrypted)