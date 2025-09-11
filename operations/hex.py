# File: operations/hex.py

def to_hex(input_string: str) -> tuple[bool, str]:
    """Encodes a standard string to a Hexadecimal string."""
    try:
        # Convert the string to bytes, then to a hex representation.
        input_bytes = input_string.encode('utf-8')
        hex_string = input_bytes.hex()
        return True, hex_string
    except Exception as e:
        return False, f"Failed to encode to Hex: {e}"


def from_hex(input_string: str) -> tuple[bool, str]:
    """Decodes a Hexadecimal string back to a standard string."""
    try:
        # Remove common prefixes and spaces
        cleaned_string = input_string.replace("0x", "").replace(" ", "").strip()
        if len(cleaned_string) % 2 != 0:
            return False, "Invalid Hex string: odd length."

        # Convert the hex string back to bytes, then to a readable string.
        decoded_bytes = bytes.fromhex(cleaned_string)
        decoded_string = decoded_bytes.decode('utf-8')
        return True, decoded_string
    except ValueError:
        return False, "Invalid characters in Hex string."
    except Exception as e:
        return False, f"Failed to decode from Hex: {e}"