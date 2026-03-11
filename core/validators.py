"""
Input validation and sanitization utilities for Cinema Project
Centralised validation to prevent XSS, SQL injection, and invalid data.
"""
from __future__ import annotations

import re
import os
from typing import Any, Sequence
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.core.files.uploadedfile import UploadedFile


def sanitize_string(value: Any, max_length: int = 500) -> str:
    """
    Sanitize string input:
    - Strip HTML tags (XSS prevention)
    - Remove null bytes
    - Enforce max length
    - Strip leading/trailing whitespace
    """
    if value is None:
        return ''
    value = str(value)
    value = value.replace('\x00', '')   
    value = strip_tags(value)           
    value = value.strip()
    return value[:max_length]


def validate_seat(row: Any, seat_number: Any, hall: Any) -> tuple[int, int]:
    """
    Validate seat coordinates against hall dimensions.
    Returns (row, seat_number) as ints or raises ValueError.
    """
    try:
        row = int(row)
        seat_number = int(seat_number)
    except (TypeError, ValueError):
        raise ValueError("Érvénytelen sor- vagy székszám.")
    
    if row < 1 or row > hall.rows:
        raise ValueError(f"Érvénytelen sor: {row}. Maximum: {hall.rows}.")
    
    if seat_number < 1 or seat_number > hall.seats_per_row:
        raise ValueError(f"Érvénytelen szék: {seat_number}. Maximum: {hall.seats_per_row}.")
    
    return row, seat_number


def validate_email_input(email: Any) -> str:
    """Validate email format."""
    if not email:
        raise ValueError("Az e-mail cím megadása kötelező.")
    
    email = sanitize_string(email, max_length=254)
    
    try:
        django_validate_email(email)
    except ValidationError:
        raise ValueError("Érvénytelen e-mail cím formátum.")
    
    return email


def validate_phone_input(phone: Any) -> str:
    """Validate phone number format."""
    if not phone:
        raise ValueError("A telefonszám megadása kötelező.")
    
    phone = sanitize_string(phone, max_length=20)
    
    if not re.match(r'^[\d\s\+\-\(\)]+$', phone):
        raise ValueError("Érvénytelen telefonszám formátum.")
    
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise ValueError("A telefonszámnak 7-15 számjegyből kell állnia.")
    
    return phone


def validate_positive_int(value: Any, field_name: str = "érték") -> int:
    """Validate that a value is a positive integer."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"A(z) {field_name} egész szám kell legyen.")
    
    if value < 1:
        raise ValueError(f"A(z) {field_name} pozitív szám kell legyen.")
    
    return value


def validate_file_upload(
    uploaded_file: UploadedFile | None,
    max_size_mb: int = 5,
    allowed_extensions: Sequence[str] | None = None,
) -> UploadedFile | None:
    """
    Validate uploaded file:
    - Check file size
    - Check file extension
    - Check MIME type basics
    """
    if allowed_extensions is None:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    if not uploaded_file:
        return None
    

    max_bytes = max_size_mb * 1024 * 1024
    if uploaded_file.size is not None and uploaded_file.size > max_bytes:
        raise ValueError(f"A fájl mérete maximum {max_size_mb}MB lehet.")
    

    name = uploaded_file.name or ""
    _, ext = os.path.splitext(name)
    if ext.lower() not in allowed_extensions:
        raise ValueError(
            f"Nem engedélyezett fájltípus: {ext}. "
            f"Engedélyezett: {', '.join(allowed_extensions)}"
        )
    

    content_type = uploaded_file.content_type
    allowed_mimes = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    ]
    if content_type not in allowed_mimes:
        raise ValueError(f"Érvénytelen fájltípus: {content_type}")
    
    return uploaded_file
