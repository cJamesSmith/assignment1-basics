"""
Contains:
    1. Base Tokenizer class (with save / load methods)
    2. Helper functions
"""

import unicodedata


# ---------------------------------------------------------
# Helper functions
def get_stats(ids: list, counts: dict | None) -> dict:
    """
    Given a list of integers, return a dictionary of counts of consecutive pairs
    Example: [1, 2, 3, 1, 2] -> {(1, 2): 2, (2, 3): 1, (3, 1): 1}
    Optionally allows to update an existing dictionary of counts
    """
    counts = {} if counts is None else counts
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1
    return counts


def merge(ids: list, pair: tuple, idx: int) -> list:
    """
    In the list of integers (ids), replace all consecutive occurrences
    of pair with the new integer token idx
    Example: ids=[1, 2, 3, 1, 2], pair=(1, 2), idx=4 -> [4, 3, 4]
    """
    newids = []
    i = 0
    while i < len(ids):
        # If not at the very last position AND the pair matches, replace it
        if ids[i] == pair[0] and i < len(ids) - 1 and ids[i + 1] == pair[1]:
            newids.append(idx)
            i += 2
        # Not matching, use the old id:
        else:
            newids.append(ids[i])
            i += 1
    return newids


def replace_control_characters(text: str) -> str:
    """
    We don't want to print control characters
    which distort the output (e.g. \n or much worse)
    https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python/19016117#19016117
    http://www.unicode.org/reports/tr44/#GC_Values_Table
    """
    chars = []
    for ch in text:
        if unicodedata.category(ch)[0] != "C":
            chars.append(ch)  # This is not a control character
        else:
            chars.append(f"\\u{ord(ch):04x}")  # Escape
    return "".join(chars)


def render_token(token: bytes) -> str:
    """
    Pretty print a token / escaping control characters
    """
    # Decode the token to a string
    text = token.decode("utf-8", errors="replace")
    # Replace control characters
    text = replace_control_characters(text)
    # Return the string
    return text


# ---------------------------------------------------------
# The base Tokenizer class


class Tokenizer:
    """
    Base class for a tokenizer
    """

    def __init__(self):
        """
        Default: vocab size of 256 (all bytes), no merges, no patterns
        """
        self.merges = {}  # type: dict[tuple[int, int], int]
        self.patterns = ""  # type: str
        self.special_tokens = {}  # type: dict[str, int]
        self.vocab = self._build_vocab()  # type: dict[int, bytes]
        self.__VERSION__ = "bpe v1.0"  # type: str

    def _build_vocab(self) -> dict[int, bytes]:
        """
        Vocab is simply and deterministically derived from the merges
        """
        vocab = {idx: bytes([idx]) for idx in range(256)}
        for (p0, p1), idx in self.merges.items():
            # Merge the two tokens into one
            vocab[idx] = vocab[p0] + vocab[p1]
        for special, idx in self.special_tokens.items():
            # Add special tokens to the vocab
            vocab[idx] = special.encode("utf-8")
        return vocab

    def train(self, text: str, vocab_size: int = 256, verbose: bool = False) -> None:
        """
        Train a vocabulary of size `vocab_size` from `text
        """
        raise NotImplementedError

    def encode(self, text: str) -> list[int]:
        """
        Encode a string into a list of integers
        """
        raise NotImplementedError

    def decode(self, ids: list[int]) -> str:
        """
        Decode a list of integers into a string
        """
        raise NotImplementedError

    def save(self, file_prefix: str) -> None:
        """
        Save two files:
            1. {file_prefix}.model: the model
            2. {file_prefix}.vocab: the vocab
        This is inspired (but not equivalent to!) sentencepiece's model saving:
        - model file is the critical one, intended for load()
        - vocab file is just a pretty printed version for human inspection only
        """
        model_file = file_prefix + ".model"
        with open(model_file, "w") as f:
            # Write the version, pattern, and merges
            f.write(f"{self.__VERSION__}\n")
            f.write(f"{self.patterns}\n")
            # Write the special tokens
            f.write(f"{len(self.special_tokens)}\n")
            for special, idx in self.special_tokens.items():
                f.write(f"{special} {idx}\n")
            # Write the merges
            for idx1, idx2 in self.merges:
                f.write(f"{idx1} {idx2}\n")
        # Write the vocab: for the human to look at
        vocab_file = file_prefix + ".vocab"
        inverted_merges = {idx: pair for pair, idx in self.merges.items()}
        with open(vocab_file, "w", encoding="utf-8") as f:
            for idx, token in self.vocab.items():
                # Note: many tokens may be partial utf-8 sequences
                # and cannot be decoded into valid strings. Here we're using
                # errors='replace' to replace them with the replacement char �.
                # this also means that we couldn't possibly use .vocab in load()
                # because decoding in this way is a lossy operation!
                s = render_token(token)
                # Find the children of this token, if any
                if idx in inverted_merges:
                    # If this token has children, render it nicely as a merge
                    idx0, idx1 = inverted_merges[idx]
                    s0 = render_token(self.vocab[idx0])
                    s1 = render_token(self.vocab[idx1])
                    f.write(f"[{s0}][{s1}] -> [{s}] {idx}\n")
                else:
                    # Otherwise, this is a leaf token, just print it
                    # This should just be the first 256 tokens, the bytes
                    f.write(f"[{s}] {idx}\n")

    def load(self, model_file: str) -> None:
        assert model_file.endswith(".model")
        merges = {}
        special_tokens = {}
        idx = 256
        # Read the model file
        with open(model_file, encoding="utf-8") as f:
            # Read the version
            version = f.readline().strip()
            assert (
                version == self.__VERSION__
            ), f"Version mismatch: {version} != {self.__VERSION__}"
            # Read the patterns
            self.patterns = f.readline().strip()
            # Read the special tokens
            n_special_tokens = int(f.readline().strip())
            for _ in range(n_special_tokens):
                special, idx = f.readline().strip().split()
                special_tokens[special] = int(idx)
            # Read the merges
            for line in f:
                idx1, idx2 = map(int, line.strip().split())
                merges[(idx1, idx2)] = idx
                idx += 1

        self.merges = merges
        self.special_tokens = special_tokens
        self.vocab = self._build_vocab()
