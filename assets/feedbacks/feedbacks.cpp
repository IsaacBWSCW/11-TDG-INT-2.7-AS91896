#include <cstring>
#include <vector>
#include <array>
#include <string>

extern "C" {
    void compute_all_feedbacks(char** words, size_t word_count, int* feedback_matrix, size_t word_length) {
        std::vector<std::string> wordList(word_count);
        for (size_t i = 0; i < word_count; ++i) {
            wordList[i] = std::string(words[i]);
        }

        for (size_t g = 0; g < word_count; ++g) {
            const std::string& guess = wordList[g];
            // printf("Calculating feedbacks for guess: %s.\n", guess.c_str());
            for (size_t c = 0; c < word_count; ++c) {
                const std::string& candidate = wordList[c];
                std::array<int, 26> letterCounts = {0};

                for (size_t i = 0; i < word_length; ++i) {
                    ++letterCounts[candidate[i] - 'a'];
                }

                std::vector<int> feedback(word_length, 0); // 0: INVALID, 1: VALID, 2: CORRECT

                // First pass: CORRECT
                for (size_t i = 0; i < word_length; ++i) {
                    if (guess[i] == candidate[i]) {
                        feedback[i] = 2; // CORRECT
                        --letterCounts[guess[i] - 'a'];
                    }
                }

                // Second pass: VALID
                for (size_t i = 0; i < word_length; ++i) {
                    if (feedback[i] == 0 && letterCounts[guess[i] - 'a'] > 0) {
                        feedback[i] = 1; // VALID
                        --letterCounts[guess[i] - 'a'];
                    }
                }

                // Encode feedback as base-3 integer
                int id = 0;
                for (size_t i = 0; i < word_length; ++i) {
                    id = id * 3 + feedback[i];
                }

                feedback_matrix[g * word_count + c] = id;
            }
        }
    }
}
