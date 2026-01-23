from __future__ import annotations
from typing import List, Dict, Any, Tuple, Callable


# Simple Porter stemmer - I found this algorithm online
# didn't want to install nltk package so I wrote a simple version
class PorterStemmer:
    def stem(self, word):
        word = word.lower()

        # step 1a - handle plurals
        if word.endswith('sses'):
            word = word[:-2]
        elif word.endswith('ies'):
            word = word[:-2]
        elif word.endswith('ss'):
            pass  # don't remove anything
        elif word.endswith('s'):
            word = word[:-1]

        # step 1b - handle past tense and gerunds
        if word.endswith('eed'):
            if len(word) > 4:
                word = word[:-1]
        elif word.endswith('ed'):
            if len(word) > 4:
                word = word[:-2]
        elif word.endswith('ing'):
            if len(word) > 5:
                word = word[:-3]

        # step 2 - handle common suffixes
        if word.endswith('ational'):
            word = word[:-5] + 'e'
        elif word.endswith('tion'):
            word = word[:-4] + 't'
        elif word.endswith('ness'):
            word = word[:-4]
        elif word.endswith('ment'):
            word = word[:-4]
        elif word.endswith('able'):
            word = word[:-4]
        elif word.endswith('ible'):
            word = word[:-4]
        elif word.endswith('ful'):
            word = word[:-3]
        elif word.endswith('ous'):
            word = word[:-3]
        elif word.endswith('ive'):
            word = word[:-3]
        elif word.endswith('ly'):
            word = word[:-2]

        return word


# create one stemmer to use everywhere
stemmer = PorterStemmer()


def normalize(token: str) -> str:
    """Remove punctuation and convert to lowercase"""
    # remove apostrophe, comma, dot
    result = token.replace("'", "").replace(",", "").replace(".", "")
    return result.lower()


def stem(token: str) -> str:
    """Normalize and stem a token"""
    normalized = normalize(token)
    return stemmer.stem(normalized)


class Sonnet:
    def __init__(self, sonnet_data: Dict[str, Any]):
        self.title = sonnet_data["title"]
        self.lines = sonnet_data["lines"]

        # extract id from title like "Sonnet 18: ..."
        parts = self.title.split()
        number_str = parts[1].rstrip(":")
        self.id = int(number_str)

    @staticmethod
    def find_spans(text: str, pattern: str):
        """Return [(start, end), ...] for all (possibly overlapping) matches."""
        spans = []
        if not pattern:
            return spans

        for i in range(len(text) - len(pattern) + 1):
            if text[i:i + len(pattern)] == pattern:
                spans.append((i, i + len(pattern)))
        return spans

    def search_for(self: Sonnet, query: str) -> SearchResult:
        title_raw = str(self.title)
        lines_raw = self.lines

        q = query.lower()
        title_spans = self.find_spans(title_raw.lower(), q)

        line_matches = []
        for idx, line_raw in enumerate(lines_raw, start=1):
            spans = self.find_spans(line_raw.lower(), q)
            if spans:
                line_matches.append(LineMatch(idx, line_raw, spans))

        total = len(title_spans) + sum(len(lm.spans) for lm in line_matches)

        return SearchResult(title_raw, title_spans, line_matches, total)


class LineMatch:
    def __init__(self, line_no: int, text: str, spans: List[Tuple[int, int]]):
        self.line_no = line_no
        self.text = text
        self.spans = spans

    def copy(self):
        return LineMatch(self.line_no, self.text, list(self.spans))


class Posting:
    def __init__(self, line_no: int, position: int, token_length: int):
        self.line_no = line_no
        self.position = position
        # NEW: store original token length for correct highlighting
        self.token_length = token_length

    def __repr__(self) -> str:
        return f"{self.line_no}:{self.position}"


class Index:
    def __init__(self, sonnets: list[Sonnet]):
        self.sonnets = {sonnet.id: sonnet for sonnet in sonnets}
        self.dictionary = {}

        for sonnet in sonnets:
            # index the title - line_no is None for title
            title_tokens = self.tokenize(sonnet.title)
            for token, position in title_tokens:
                # NEW: stem the token but keep original length
                stemmed = stem(token)
                self._add_token(sonnet.id, stemmed, None, position, len(token))

            # index each line - line_no starts from 1
            for line_no, line in enumerate(sonnet.lines, start=1):
                line_tokens = self.tokenize(line)
                for token, position in line_tokens:
                    # NEW: stem the token but keep original length
                    stemmed = stem(token)
                    self._add_token(sonnet.id, stemmed, line_no, position, len(token))

    @staticmethod
    def tokenize(text):
        """Split text into tokens with their positions"""
        import re
        tokens = [
            (match.group(), match.start())
            for match in re.finditer(r"\S+", text)
        ]
        return tokens

    def _add_token(self, doc_id: int, token: str, line_no: int | None, position: int, token_length: int):
        """Add token to the inverted index"""
        if token not in self.dictionary:
            self.dictionary[token] = {}

        postings_list = self.dictionary[token]

        if doc_id not in postings_list:
            postings_list[doc_id] = []
        postings_list[doc_id].append(Posting(line_no, position, token_length))

    def search_for(self, token: str) -> dict[int, SearchResult]:
        """Search for a token in the index"""
        results = {}

        # NEW: stem the search token too!
        stemmed_token = stem(token)

        if stemmed_token in self.dictionary:
            postings_list = self.dictionary[stemmed_token]
            for doc_id, postings in postings_list.items():
                for posting in postings:
                    sonnet = self.sonnets[doc_id]

                    if posting.line_no is None:
                        # match in title - use original token length for span
                        title_spans = [(posting.position, posting.position + posting.token_length)]
                        line_matches = []
                    else:
                        # match in line
                        title_spans = []
                        line_text = sonnet.lines[posting.line_no - 1]
                        # use original token length for span
                        span = (posting.position, posting.position + posting.token_length)
                        line_matches = [LineMatch(posting.line_no, line_text, [span])]

                    result = SearchResult(sonnet.title, title_spans, line_matches, 1)

                    if doc_id not in results:
                        results[doc_id] = result
                    else:
                        results[doc_id] = results[doc_id].combine_with(result)

        return results


class Searcher:
    def __init__(self, sonnets: List[Sonnet]):
        self.index = Index(sonnets)

    def search(self, query: str, search_mode: str) -> List[SearchResult]:
        """Search for multi-word query"""
        words = query.split()

        combined_results = {}

        for word in words:
            # search_for will stem the word internally
            results = self.index.search_for(word)

            if not combined_results:
                # first word
                combined_results = results
            else:
                if search_mode == "AND":
                    # only keep sonnets that have ALL words
                    new_combined = {}
                    for doc_id in combined_results:
                        if doc_id in results:
                            new_combined[doc_id] = combined_results[doc_id].combine_with(results[doc_id])
                    combined_results = new_combined
                elif search_mode == "OR":
                    # keep sonnets that have ANY word
                    for doc_id, result in results.items():
                        if doc_id in combined_results:
                            combined_results[doc_id] = combined_results[doc_id].combine_with(result)
                        else:
                            combined_results[doc_id] = result

        results = list(combined_results.values())
        return sorted(results, key=lambda sr: sr.title)


class SearchResult:
    def __init__(self, title: str, title_spans: List[Tuple[int, int]], line_matches: List[LineMatch],
                 matches: int) -> None:
        self.title = title
        self.title_spans = title_spans
        self.line_matches = line_matches
        self.matches = matches

    def copy(self):
        return SearchResult(self.title, list(self.title_spans), [lm.copy() for lm in self.line_matches], self.matches)

    @staticmethod
    def ansi_highlight(text: str, spans, highlight_mode) -> str:
        """Return text with ANSI highlight escape codes"""
        if not spans:
            return text

        spans = sorted(spans)
        merged = []

        # merge overlapping spans
        current_start, current_end = spans[0]
        for s, e in spans[1:]:
            if s <= current_end:
                current_end = max(current_end, e)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = s, e
        merged.append((current_start, current_end))

        ansi_sequence = "\033[43m\033[30m" if highlight_mode == "DEFAULT" else "\033[1;92m"

        out = []
        i = 0
        for s, e in merged:
            out.append(text[i:s])
            out.append(ansi_sequence)
            out.append(text[s:e])
            out.append("\033[0m")
            i = e
        out.append(text[i:])
        return "".join(out)

    def print(self, idx, highlight_mode: str | None, total_docs):
        title_line = (
            self.ansi_highlight(self.title, self.title_spans, highlight_mode)
            if highlight_mode
            else self.title
        )
        print(f"\n[{idx}/{total_docs}] {title_line}")
        for lm in self.line_matches:
            line_out = (
                self.ansi_highlight(lm.text, lm.spans, highlight_mode)
                if highlight_mode
                else lm.text
            )
            print(f"  [{lm.line_no:2}] {line_out}")

    def combine_with(self: SearchResult, other: SearchResult) -> SearchResult:
        """Combine two search results"""

        combined = self.copy()

        combined.matches = self.matches + other.matches
        combined.title_spans = sorted(self.title_spans + other.title_spans)

        lines_by_no = {lm.line_no: lm.copy() for lm in self.line_matches}
        for lm in other.line_matches:
            ln = lm.line_no
            if ln in lines_by_no:
                lines_by_no[ln].spans = lines_by_no[ln].spans + lm.spans
            else:
                lines_by_no[ln] = lm.copy()

        combined.line_matches = sorted(lines_by_no.values(), key=lambda x: x.line_no)

        return combined