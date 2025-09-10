# File: operations/ciphers.py

def caesar_cipher(text: str, shift: int, decrypt: bool = False) -> tuple[bool, str]:
    """
    Encrypts or decrypts text using the Caesar cipher method.

    Args:
        text (str): The input string to be processed.
        shift (int): The number of positions to shift letters.
        decrypt (bool): If True, the function will decrypt the text.
                         If False, it will encrypt.

    Returns:
        A tuple containing a boolean for success and the resulting string.
    """
    if not isinstance(shift, int):
        return False, "Shift value must be an integer."

    if decrypt:
        shift = -shift

    result = ""
    for char in text:
        if 'a' <= char <= 'z':
            # Handle lowercase letters
            shifted_char = chr(((ord(char) - ord('a') + shift) % 26) + ord('a'))
            result += shifted_char
        elif 'A' <= char <= 'Z':
            # Handle uppercase letters
            shifted_char = chr(((ord(char) - ord('A') + shift) % 26) + ord('A'))
            result += shifted_char
        else:
            # Keep non-alphabetic characters unchanged
            result += char

    return True, result