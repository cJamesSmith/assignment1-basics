"""
Minimal (byte-level) Byte Pair Encoding tokenizer.

Algorithmically follows along the GPT tokenizer:
https://github.com/openai/gpt-2/blob/master/src/encoder.py

But:
- Does not handle the regular expression splitting pattern.
- Does not handle any special tokens.
"""

from .base import Tokenizer, get_stats, merge

class BaseTokenizer(Tokenizer):
    """
    Minimal (byte-level) Byte Pair Encoding tokenizer.
    """

    def __init__(self):
        super().__init__()

    def train(self, text, vocab_size = 256, verbose = False) -> None:
        assert vocab_size >= 256, "Vocab size must be at least 256"
        num_merges = vocab_size - 256

        # Input text preprocessing
        test_bytes = text.encode("utf-8")  # Raw bytes
        ids = list(test_bytes)  # List of integers in range [0, 255]

        # Iteratively merge the most frequent pairs
        merges = {}  # type: dict[tuple[int, int], int]
        vocab = {idx: bytes([idx]) for idx in range(256)}  # type: dict[int, bytes]
        for i in range(num_merges):
            # Get the most frequent pair
            stats = get_stats(ids)
            # Find the most frequent pair
            pair = max(stats, key=stats.get)
            # New token id
            idx = 256 + i
            # Merge the pair
            ids = merge(ids, pair, idx)
            # Add the merge to the list
            merges[pair] = idx
            # Add the new token to the vocab
            vocab[idx] = vocab[pair[0]] + vocab[pair[1]]
            # Print
            if verbose:
                print(f"Merge {i + 1}/{num_merges}: {pair} -> {idx} ({vocab[idx]}) had {stats[pair]} occurrences")
        
        # Save class variables
        self.merges = merges
        self.vocab = vocab

    def decode(self, ids: list[int]) -> str:
        """
        Decode a list of integers into a string
        """
        # Decode the list of integers into bytes
        text_bytes = b"".join([self.vocab[idx] for idx in ids])
        text = text_bytes.decode("utf-8", errors="replace")
        return text
    
    def encode(self, text: str) -> list[int]:
        """
        Encode a string into a list of integers
        """
        # Encode the string into bytes
        text_bytes = text.encode("utf-8")
        # Convert the bytes to a list of integers in range [0, 255]
        ids = list(text_bytes)
        while len(ids) >= 2:
            # Find the pair with the lowest frequency
            stats = get_stats(ids)
            pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
            # Subtle: if there are no more merges available, the key will
            # result in an inf for every single pair, and the min will be
            # just the first pair in the list, arbitrarily
            # we can detect this terminating case by a membership check
            if pair not in self.merges:
                break  # Nothing else can be merged
            # Otherwise, merge the pair
            idx = self.merges[pair]
            ids = merge(ids, pair, idx)
        return ids
