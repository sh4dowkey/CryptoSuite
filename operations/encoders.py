# File: operations/encoders.py

import base64


def to_base64(input_string: str) -> tuple[bool, str]:
    """Encodes a standard string to Base64."""
    try:
        # The base64 library works on bytes, so we encode the string first.
        input_bytes = input_string.encode('utf-8')
        base64_bytes = base64.b64encode(input_bytes)
        # Decode the result back to a string for the GUI.
        base64_string = base64_bytes.decode('utf-8')
        return True, base64_string
    except Exception as e:
        return False, f"Failed to encode: {e}"


def from_base64(input_string: str) -> tuple[bool, str]:
    """Decodes a Base64 string back to a standard string."""
    try:
        # We need to encode the string back to bytes to be decoded.
        base64_bytes = input_string.encode('utf-8')
        decoded_bytes = base64.b64decode(base64_bytes)
        # Decode the final bytes into a readable string.
        decoded_string = decoded_bytes.decode('utf-8')
        return True, decoded_string
    except Exception as e:
        # This usually happens if the input isn't valid Base64.
        return False, f"Invalid Base64 input: {e}"
