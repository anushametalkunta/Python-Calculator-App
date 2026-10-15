
import pytest

from calculator.numtheory import (
    describe_integer,
    divisors,
    format_factorization,
    is_prime,
    next_prime,
    previous_prime,
    prime_factors,
    totient,
)


@pytest.mark.parametrize(
    "number, expected",
    [
        (2, True),
        (3, True),
        (7, True),
        (97, True),
        (1, False),
        (0, False),
        (-7, False),
        (100, False),
        (10403, False),
    ],
)
def test_is_prime(number, expected):
    assert is_prime(number) is expected


@pytest.mark.parametrize(
    "number, expected",
    [
        (1, []),
        (2, [2]),
        (12, [2, 2, 3]),
        (360, [2, 2, 2, 3, 3, 5]),
        (97, [97]),
    ],
)
def test_prime_factors(number, expected):
    assert prime_factors(number) == expected


def test_divisors():
    assert divisors(1) == [1]
    assert divisors(6) == [1, 2, 3, 6]
    assert divisors(12) == [1, 2, 3, 4, 6, 12]


def test_totient():
    assert totient(1) == 1
    assert totient(9) == 6
    assert totient(12) == 4
    assert totient(13) == 12


def test_factorization_format():
    assert format_factorization(1) == "1"
    assert format_factorization(12) == "2² × 3"
    assert format_factorization(360) == "2³ × 3² × 5"


def test_previous_and_next_prime():
    assert previous_prime(2) is None
    assert previous_prime(10) == 7
    assert next_prime(10) == 11
    assert next_prime(2) == 3


def test_describe_perfect_number():
    facts = describe_integer(28)

    assert facts["classification"] == "composite"
    assert facts["divisors"] == [1, 2, 4, 7, 14, 28]
    assert facts["sum_of_divisors"] == 56
    assert facts["totient"] == 12
    assert facts["abundance"] == "perfect"
    assert facts["is_perfect_square"] is False


def test_describe_prime_number():
    facts = describe_integer(13)

    assert facts["classification"] == "prime"
    assert facts["factorization"] == "13"
    assert facts["is_perfect_square"] is False
    assert facts["is_perfect_cube"] is False


@pytest.mark.parametrize("number", [0, -1, 10**15 + 1])
def test_invalid_describe_integer(number):
    with pytest.raises(ValueError):
        describe_integer(number)
