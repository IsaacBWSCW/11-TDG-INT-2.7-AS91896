import collections
import math
from itertools import product

# Single letter check
class LetterCheck:
    NONE = -1
    INVALID = 0
    VALID = 1
    CORRECT = 2
    def __init__(self, type_: float):
        self.type: float = type_

# Full pattern of letter checks
class LetterCheckPattern:
    def __init__(self, letters: list[LetterCheck]):
        self.letters: list[LetterCheck] = letters

all_possible_letter_check_patterns: list[LetterCheckPattern] = [
    LetterCheckPattern([LetterCheck(type_=state_val) for state_val in state])
    for state in product(range(3), repeat=5)
] # Computes all possible patterns

# Class to contain word list, feedbacks, word length and member functions to entropy math on
class WordListProcessor:
    def __init__(self, words: list[str], feedbacks: list[list[int]]):
        self.word_length = len(words[0])
        self.words: list[str] = words
        self.feedbacks: list[list[int]] = feedbacks

    # Get all matches for a word and pattern
    def get_matches(self, letter_check_pattern: LetterCheckPattern, word: str) -> list[str]:
        # Count the number of valid or correct letters in the pattern
        required_counts = collections.Counter()
        for i, letter_check in enumerate(letter_check_pattern.letters):
            if letter_check.type == LetterCheck.VALID or letter_check.type == LetterCheck.CORRECT:
                required_counts[word[i]] += 1

        matches: list[str] = []

        # Loop over all words
        for candidate in self.words:
            valid: bool = True

            # Count the number of times a letter occurs in the candidate
            candidate_counts = collections.Counter(candidate)

            # Track the number of times a letter is seen
            seen_counts = collections.Counter()
            for i in range(self.word_length):
                # Loop over each letter in the word
                letter = word[i]
                candidate_letter = candidate[i]

                if letter_check_pattern.letters[i].type == LetterCheck.INVALID:
                    # If pattern is invalid make sure there aren't any more of this letter left in the candidate
                    if candidate_counts[letter] > required_counts.get(letter, 0):
                        valid = False
                        break
                elif letter_check_pattern.letters[i].type == LetterCheck.VALID:
                    # If valid check that the candidate doesn't have the current letter in the same location and that the candidate has at least one instance of the letter
                    if letter == candidate_letter or candidate_counts[letter] == 0:
                        valid = False
                        break
                    seen_counts[letter] += 1
                elif letter_check_pattern.letters[i].type == LetterCheck.CORRECT:
                    # Check that the candidate letter matches the current letter
                    if letter != candidate_letter:
                        valid = False
                        break
                    seen_counts[letter] += 1
            if not valid: continue # If not valid move to the next candidate

            for letter, count in required_counts.items():
                # Make sure the candidate has at least the required number of letter instances
                if candidate_counts[letter] < count:
                    valid = False
                    break

            if valid: # If valid then add the candidate to the list of matches
                matches.append(candidate)

        return matches

    # Compute average expected information gained for word if used as a guess
    def expected_information(self, word: str) -> float:
        exp_info: float = 0

        word_index = self.words.index(word) # Find the index of the word in the list of words

        # For each word find the corresponding pattern for it and the input word and increment the counter for that pattern by one
        counts = collections.Counter()
        for i in range(len(self.words)):
            feedback_id = self.feedbacks[word_index][i]
            counts[feedback_id] += 1

        # Loop over all possible patterns and calculate their probabilities
        for i in range(len(all_possible_letter_check_patterns)):
            if counts[i] == 0: continue
            p = float(counts[i]) / float(len(self.words))
            exp_info += p * -math.log2(p)

        return exp_info