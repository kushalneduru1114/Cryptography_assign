import random
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

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

N = 15
factor1, factor2 = shors_algorithm(N)
print(f"Factors of {N}: {factor1}, {factor2}")