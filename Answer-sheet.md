# Answers
## 2.1 The Unicode Standard

1. What Unicode character does `chr(0)` return?

    Answer: `'\x00'`

2. How does this character’s string representation (`__repr__()`) differ from its printed representation?

    Answer: Its printed representation is total blank (nothing printed).

3. What happens when this character occurs in text? It may be helpful to play around with the following in your Python interpreter and see if it matches your expectations:

    ```python
    >>> chr(0)
    >>> print(chr(0))
    >>> "this is a test" + chr(0) + "string"
    >>> print("this is a test" + chr(0) + "string")
    ```

    Answer: 

    ```python
    >>> "this is a test" + chr(0) + "string"
    'this is a test\x00string'
    >>> print("this is a test" + chr(0) + "string")
    this is a teststring
    ```

## 2.2 Unicode Encodings

1. What are some reasons to prefer training our tokenizer on UTF-8 encoded bytes, rather than UTF-16 or UTF-32? It may be helpful to compare the output of these encodings for various input strings.

    Answer:

    ```python
    >>> test_string = "hello! こんにちは!"
    >>> utf8_encoded = test_string.encode("utf-8")
    >>> print(utf8_encoded)
    b'hello! \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf!'
    >>> print(type(utf8_encoded))
    <class 'bytes'>
    >>> list(utf8_encoded)
    [104, 101, 108, 108, 111, 33, 32, 227, 129, 147, 227, 130, 147, 227, 129, 171, 227, 129, 161, 227, 129, 175, 33]
    >>> print(len(test_string))
    13
    >>> print(len(utf8_encoded))
    23
    >>> print(utf8_encoded.decode("utf-8"))
    hello! こんにちは!
    >>> utf16_encoded = test_string.encode("utf-16")
    >>> print(utf16_encoded)
    b'\xff\xfeh\x00e\x00l\x00l\x00o\x00!\x00 \x00S0\x930k0a0o0!\x00'
    >>> print(len(utf16_encoded))
    28
    >>> utf32_encoded = test_string.encode("utf-32")
    >>> print(utf32_encoded)
    b'\xff\xfe\x00\x00h\x00\x00\x00e\x00\x00\x00l\x00\x00\x00l\x00\x00\x00o\x00\x00\x00!\x00\x00\x00 \x00\x00\x00S0\x00\x00\x930\x00\x00k0\x00\x00a0\x00\x00o0\x00\x00!\x00\x00\x00'
    >>> print(len(utf32_encoded))
    56
    ```
    The sequence length of the UTF-16's and UTF-32's encoded bytes are longer than UTF-8's, because they use more bytes to represent a codepoint.

2. Consider the following (incorrect) function, which is intended to decode a UTF-8 byte string into a Unicode string. Why is this function incorrect? Provide an example of an input byte string that yields incorrect results.
    ```python
    >>> def decode_utf8_bytes_to_str_wrong(bytestring: bytes):
    ...     return "".join([bytes([b]).decode("utf-8") for b in bytestring])
    ... 
    >>> decode_utf8_bytes_to_str_wrong("hello".encode("utf-8"))
    'hello'
    ```

    Answer:
    ```python
    >>> decode_utf8_bytes_to_str_wrong("こんにちは".encode("utf-8"))
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "<stdin>", line 2, in decode_utf8_bytes_to_str_wrong
    File "<stdin>", line 2, in <listcomp>
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe3 in position 0: unexpected end of data
    ```
    Only ASCII words use 1 bytes in Unicode, while other words use 2 (or more) bytes in UTF-8.

3. Give a two byte sequence that does not decode to any Unicode character(s).

    Answer:
    ```python
    >>> b'\x00\xe3'.decode('utf8')
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe3 in position 1: unexpected end of data
    >>> b'\xe3\x81\x93'.decode('utf8')
    'こ'
    ```