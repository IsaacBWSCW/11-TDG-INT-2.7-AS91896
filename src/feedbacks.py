import ctypes
import platform

# Invokes a C++ function from a shared library to compute the feedbacks because python is too slow to do this.
library_path = ""
if platform.system() == "Linux": library_path = "assets/feedbacks/feedbacks.so"
elif platform.system() == "Windows": library_path = "assets/feedbacks/feedbacks.dll"
feedback_library = ctypes.CDLL(library_path)
feedback_library.compute_all_feedbacks.argtypes = [
    ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_int), ctypes.c_size_t
]
feedback_library.compute_all_feedbacks.restype = None
def compute_feedbacks(words: list[str], word_length: int) -> list[list[int]]:
    print("Packing inputs to compute feedbacks.")
    word_count = len(words)

    c_words = (ctypes.c_char_p * word_count)(*[
        ctypes.create_string_buffer(w.encode("utf-8")).value for w in words
    ])

    feedback_matrix = (ctypes.c_int * (word_count * word_count))()

    print("Computing feedbacks.")
    feedback_library.compute_all_feedbacks(c_words, word_count, feedback_matrix, word_length)

    print("Unpacking results from feedbacks compute.")
    result = [
        [feedback_matrix[i * word_count + j] for j in range(word_count)]
        for i in range(word_count)
    ]

    return result