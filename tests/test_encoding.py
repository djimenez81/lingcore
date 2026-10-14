"""Tests for lingcore.encoding."""

import math

import pytest

from lingcore import Value
from lingcore.encoding import ValueEncoder


class TestDefault:
    def test_plus(self) -> None:
        e = ValueEncoder.default()
        assert e.encode(Value("+")) == 1.0

    def test_minus(self) -> None:
        e = ValueEncoder.default()
        assert e.encode(Value("-")) == 0.0

    def test_zero_is_nan(self) -> None:
        e = ValueEncoder.default()
        assert math.isnan(e.encode(Value("0")))

    def test_none_is_nan(self) -> None:
        e = ValueEncoder.default()
        assert math.isnan(e.encode(None))

    def test_unknown_value_raises(self) -> None:
        e = ValueEncoder.default()
        with pytest.raises(ValueError, match="No encoding"):
            e.encode(Value("close"))


class TestCustom:
    def test_custom_mapping(self) -> None:
        e = ValueEncoder(
            {
                Value("high"): 2.0,
                Value("mid"): 1.0,
                Value("low"): 0.0,
                None: float("nan"),
            }
        )
        assert e.encode(Value("high")) == 2.0
        assert e.encode(Value("low")) == 0.0
        assert math.isnan(e.encode(None))

    def test_missing_key_raises(self) -> None:
        e = ValueEncoder({Value("+"): 1.0})
        with pytest.raises(ValueError, match="No encoding"):
            e.encode(Value("-"))


class TestImmutability:
    def test_mapping_is_frozen(self) -> None:
        e = ValueEncoder({Value("+"): 1.0})
        with pytest.raises(TypeError):
            e.mapping[Value("-")] = 0.0  # type: ignore[index]

    def test_source_dict_mutation_does_not_leak(self) -> None:
        src = {Value("+"): 1.0}
        e = ValueEncoder(src)
        src[Value("-")] = 0.0
        assert Value("-") not in e.mapping


class TestEquality:
    def test_equal_simple(self) -> None:
        e1 = ValueEncoder({Value("+"): 1.0})
        e2 = ValueEncoder({Value("+"): 1.0})
        assert e1 == e2

    def test_different_keys(self) -> None:
        e1 = ValueEncoder({Value("+"): 1.0})
        e2 = ValueEncoder({Value("-"): 0.0})
        assert e1 != e2

    def test_different_values(self) -> None:
        e1 = ValueEncoder({Value("+"): 1.0})
        e2 = ValueEncoder({Value("+"): 0.0})
        assert e1 != e2

    def test_nan_equal_to_nan(self) -> None:
        e1 = ValueEncoder({Value("0"): float("nan")})
        e2 = ValueEncoder({Value("0"): float("nan")})
        assert e1 == e2

    def test_nan_not_equal_to_number(self) -> None:
        e1 = ValueEncoder({Value("0"): float("nan")})
        e2 = ValueEncoder({Value("0"): 0.0})
        assert e1 != e2

    def test_default_encoders_are_equal(self) -> None:
        assert ValueEncoder.default() == ValueEncoder.default()

    def test_not_equal_to_other_type(self) -> None:
        assert ValueEncoder({Value("+"): 1.0}) != "not an encoder"

    def test_unhashable(self) -> None:
        e = ValueEncoder({Value("+"): 1.0})
        with pytest.raises(TypeError, match="unhashable"):
            hash(e)
