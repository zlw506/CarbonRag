import math
from collections import Counter

try:
    from rank_bm25 import BM25Okapi as RankBM25Okapi
except Exception:  # pragma: no cover - environment-specific fallback
    RankBM25Okapi = None


class PythonBM25Okapi:
    def __init__(self, corpus_tokens: list[list[str]], *, k1: float = 1.5, b: float = 0.75) -> None:
        self.corpus_tokens = corpus_tokens
        self.k1 = k1
        self.b = b
        self.document_count = len(corpus_tokens)
        self.document_lengths = [len(document) for document in corpus_tokens]
        self.average_document_length = (
            sum(self.document_lengths) / self.document_count if self.document_count else 0.0
        )
        self.term_frequencies = [Counter(document) for document in corpus_tokens]
        self.document_frequency: Counter[str] = Counter()
        for document in corpus_tokens:
            for token in set(document):
                self.document_frequency[token] += 1

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        if not self.corpus_tokens:
            return []

        scores = [0.0 for _ in self.corpus_tokens]
        for index, term_frequency in enumerate(self.term_frequencies):
            document_length = self.document_lengths[index] or 1
            for token in query_tokens:
                if token not in term_frequency:
                    continue
                document_frequency = self.document_frequency[token]
                inverse_document_frequency = math.log(
                    1 + (self.document_count - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                frequency = term_frequency[token]
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * document_length / max(self.average_document_length, 1.0)
                )
                scores[index] += inverse_document_frequency * (
                    frequency * (self.k1 + 1) / max(denominator, 1e-9)
                )
        return scores


BM25Okapi = RankBM25Okapi or PythonBM25Okapi
