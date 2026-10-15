
"""Number theory functions for the calculator app."""

import math
import random
from functools import lru_cache

MAX_INTEGER = 10**15
BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _validate(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("Expected a whole number")
    if not 1 <= n <= MAX_INTEGER:
        raise ValueError("Number must be from 1 to 1000000000000000")
    return n


def is_prime(n):
    """Deterministic Miller-Rabin primality test for the supported range."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        return False

    for p in BASES:
        if n % p == 0:
            return n == p

    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in BASES:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue

        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False

    return True


def _pollard_rho(n):
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3

    while True:
        c = random.randrange(1, n - 1)
        x = random.randrange(0, n - 1)
        y = x
        divisor = 1

        while divisor == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            divisor = math.gcd(abs(x - y), n)

        if divisor != n:
            return divisor


def _factor_recursive(n, result):
    if n == 1:
        return
    if is_prime(n):
        result.append(n)
        return

    factor = _pollard_rho(n)
    _factor_recursive(factor, result)
    _factor_recursive(n // factor, result)


@lru_cache(maxsize=2048)
def _factor_tuple(n):
    result = []
    _factor_recursive(n, result)
    return tuple(sorted(result))


def prime_factors(n):
    """Return prime factors with repetition: 12 -> [2, 2, 3]."""
    n = _validate(n)
    if n == 1:
        return []
    return list(_factor_tuple(n))


def _factor_powers(n):
    powers = []
    for p in prime_factors(n):
        if powers and powers[-1][0] == p:
            powers[-1] = (p, powers[-1][1] + 1)
        else:
            powers.append((p, 1))
    return powers


def divisors(n):
    """Return every positive divisor in ascending order."""
    n = _validate(n)
    values = [1]

    for p, exponent in _factor_powers(n):
        existing = values[:]
        multiplier = 1

        for _ in range(exponent):
            multiplier *= p
            values.extend(v * multiplier for v in existing)

    return sorted(values)


def totient(n):
    """Calculate Euler's totient function."""
    n = _validate(n)
    result = n

    for p, _ in _factor_powers(n):
        result = result // p * (p - 1)

    return result


def next_prime(n):
    """Return the first prime strictly greater than n."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("Expected a whole number")
    if not 0 <= n <= MAX_INTEGER:
        raise ValueError("Number must be from 0 to 1000000000000000")

    candidate = n + 1
    if candidate > 2 and candidate % 2 == 0:
        candidate += 1

    while not is_prime(candidate):
        candidate = 3 if candidate < 3 else candidate + 2

    return candidate


def previous_prime(n):
    """Return the previous prime, or None if no previous prime exists."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("Expected a whole number")
    if not 0 <= n <= MAX_INTEGER:
        raise ValueError("Number must be from 0 to 1000000000000000")

    candidate = n - 1
    if candidate < 2:
        return None
    if candidate > 2 and candidate % 2 == 0:
        candidate -= 1

    while candidate >= 2 and not is_prime(candidate):
        candidate -= 2

    return candidate if candidate >= 2 else None


def format_factorization(n):
    """Format 360 as 2³ × 3² × 5."""
    n = _validate(n)
    powers = _factor_powers(n)

    if not powers:
        return "1"

    parts = []
    for prime, exponent in powers:
        if exponent == 1:
            parts.append(str(prime))
        else:
            parts.append(
                f"{prime}{str(exponent).translate(SUPERSCRIPTS)}"
            )

    return " × ".join(parts)


def _is_perfect_cube(n):
    root = round(n ** (1 / 3))

    while (root + 1) ** 3 <= n:
        root += 1
    while root ** 3 > n:
        root -= 1

    return root ** 3 == n


def describe_integer(n):
    """Return number facts for an integer from 1 through 10**15."""
    n = _validate(n)
    factors = prime_factors(n)
    all_divisors = divisors(n)
    divisor_sum = sum(all_divisors)

    if n == 1:
        classification = "neither prime nor composite"
    elif is_prime(n):
        classification = "prime"
    else:
        classification = "composite"

    if divisor_sum == 2 * n:
        abundance = "perfect"
    elif divisor_sum > 2 * n:
        abundance = "abundant"
    else:
        abundance = "deficient"

    return {
        "number": n,
        "classification": classification,
        "is_prime": is_prime(n),
        "prime_factors": factors,
        "factorization": format_factorization(n),
        "divisors": all_divisors,
        "divisor_count": len(all_divisors),
        "sum_of_divisors": divisor_sum,
        "totient": totient(n),
        "abundance": abundance,
        "is_perfect": abundance == "perfect",
        "is_abundant": abundance == "abundant",
        "is_deficient": abundance == "deficient",
        "is_perfect_square": math.isqrt(n) ** 2 == n,
        "is_perfect_cube": _is_perfect_cube(n),
        "previous_prime": previous_prime(n),
        "next_prime": next_prime(n),
    }
