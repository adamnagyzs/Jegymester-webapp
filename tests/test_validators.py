"""
Tests for core validators and template tags.
"""
from django.test import TestCase

from core.models import CinemaHall
from core.validators import (
    sanitize_string,
    validate_seat,
    validate_email_input,
    validate_phone_input,
    validate_positive_int,
)


class SanitizeStringTests(TestCase):

    def test_strips_html(self):
        self.assertEqual(sanitize_string('<b>hello</b>'), 'hello')

    def test_removes_null_bytes(self):
        self.assertNotIn('\x00', sanitize_string('a\x00b'))

    def test_enforces_max_length(self):
        self.assertEqual(len(sanitize_string('a' * 1000, max_length=50)), 50)

    def test_strips_whitespace(self):
        self.assertEqual(sanitize_string('  hello  '), 'hello')

    def test_none_returns_empty(self):
        self.assertEqual(sanitize_string(None), '')


class ValidateSeatTests(TestCase):

    def setUp(self):
        self.hall = CinemaHall.objects.create(name='H', rows=10, seats_per_row=15)

    def test_valid_seat(self):
        r, s = validate_seat('5', '10', self.hall)
        self.assertEqual((r, s), (5, 10))

    def test_invalid_row_too_high(self):
        with self.assertRaises(ValueError):
            validate_seat('11', '1', self.hall)

    def test_invalid_seat_too_high(self):
        with self.assertRaises(ValueError):
            validate_seat('1', '16', self.hall)

    def test_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            validate_seat('abc', '1', self.hall)

    def test_zero_row(self):
        with self.assertRaises(ValueError):
            validate_seat('0', '1', self.hall)

    def test_negative_seat(self):
        with self.assertRaises(ValueError):
            validate_seat('1', '-1', self.hall)


class ValidateEmailInputTests(TestCase):

    def test_valid_email(self):
        self.assertEqual(validate_email_input('test@example.com'), 'test@example.com')

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            validate_email_input('')

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            validate_email_input(None)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            validate_email_input('not-an-email')


class ValidatePhoneInputTests(TestCase):

    def test_valid_phone(self):
        self.assertEqual(validate_phone_input('+36 30 1234567'), '+36 30 1234567')

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            validate_phone_input('')

    def test_invalid_chars_raises(self):
        with self.assertRaises(ValueError):
            validate_phone_input('abc-phone')

    def test_too_short_raises(self):
        with self.assertRaises(ValueError):
            validate_phone_input('12345')


class ValidatePositiveIntTests(TestCase):

    def test_valid(self):
        self.assertEqual(validate_positive_int('42'), 42)

    def test_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            validate_positive_int('abc')

    def test_zero_raises(self):
        with self.assertRaises(ValueError):
            validate_positive_int('0')

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            validate_positive_int('-5')


class TemplateTagTests(TestCase):

    def test_to_range(self):
        from core.templatetags.cinema_tags import to_range
        self.assertEqual(list(to_range(3)), [1, 2, 3])

    def test_to_range_zero(self):
        from core.templatetags.cinema_tags import to_range
        self.assertEqual(list(to_range(0)), [])

    def test_to_range_invalid(self):
        from core.templatetags.cinema_tags import to_range
        self.assertEqual(list(to_range('abc')), [])
