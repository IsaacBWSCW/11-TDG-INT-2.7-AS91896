import collections
import math
from itertools import product

class LetterCheck:
    NONE = -1
    INVALID = 0
    VALID = 1
    CORRECT = 2
    def __init__(self, type_: float):
        self.type: float = type_

class LetterCheckPattern:
    def __init__(self, letters: list[LetterCheck]):
        self.letters: list[LetterCheck] = letters

all_possible_letter_check_patterns: list[LetterCheckPattern] = [
    LetterCheckPattern([LetterCheck(type_=state_val) for state_val in state])
    for state in product(range(3), repeat=5)
]

class WordListProcessor:
    def __init__(self, words: list[str], feedbacks: list[list[int]] = []):
        self.word_length = len(words[0])
        self.words: list[str] = words
        self.feedbacks: list[list[int]] = feedbacks

    def get_matches(self, letter_check_pattern: LetterCheckPattern, word: str) -> list[str]:
        required_counts = collections.Counter()
        for i, letter_check in enumerate(letter_check_pattern.letters):
            if letter_check.type == LetterCheck.VALID or letter_check.type == LetterCheck.CORRECT:
                required_counts[word[i]] += 1

        matches: list[str] = []

        for candidate in self.words:
            if len(candidate) != self.word_length: continue

            valid: bool = True

            candidate_counts = collections.Counter(candidate)

            seen_counts = collections.Counter()
            for i in range(self.word_length):
                letter = word[i]
                candidate_letter = candidate[i]

                if letter_check_pattern.letters[i].type == LetterCheck.INVALID:
                    if candidate_counts[letter] > required_counts.get(letter, 0):
                        valid = False
                        break
                elif letter_check_pattern.letters[i].type == LetterCheck.VALID:
                    if letter == candidate_letter or candidate_counts[letter] == 0:
                        valid = False
                        break
                    seen_counts[letter] += 1
                elif letter_check_pattern.letters[i].type == LetterCheck.CORRECT:
                    if letter != candidate_letter:
                        valid = False
                        break
                    seen_counts[letter] += 1
            if not valid: continue

            for letter, count in required_counts.items():
                if candidate_counts[letter] < count:
                    valid = False
                    break

            if valid:
                matches.append(candidate)

        return matches

    def expected_information(self, word: str) -> float:
        exp_info: float = 0

        word_index = self.words.index(word)

        counts = collections.Counter()
        for i in range(len(self.words)):
            feedback_id = self.feedbacks[word_index][i]
            counts[feedback_id] += 1

        for i in range(len(all_possible_letter_check_patterns)):
            if counts[i] == 0: continue
            p = float(counts[i]) / float(len(self.words))
            exp_info += p * -math.log2(p)

        return exp_info

    def best_guess(self) -> tuple[str, float]:
        max_exp_info: float = -1
        max_exp_info_word: str = ""

        for word in self.words:
            exp_info = self.expected_information(word)
            if exp_info > max_exp_info:
                max_exp_info = exp_info
                max_exp_info_word = word

        return max_exp_info_word, max_exp_info