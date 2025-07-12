import os.path
import h5py
import pygame
import numpy
from words import all_words
from stuff import LetterCheck, LetterCheckPattern, WordListProcessor
from feedbacks import compute_feedbacks

screen_width, screen_height = 640, 480
word_length: int = 5
guesses: int = 6
rows: list[list[str]] = [
    ["" for _ in range(word_length)] for _ in range(guesses)
]
row_patterns: list[LetterCheckPattern] = [
    LetterCheckPattern([LetterCheck(LetterCheck.NONE) for _ in range(word_length)]) for _ in range(guesses)
]
current_row_index: int = 0
current_col_index: int = 0
input_pattern: bool = False
best_guesses: list[tuple[str, float]] = []
feedbacks: list[list[int]] = []
word_list_processor: WordListProcessor

def draw_wordle(screen: pygame.surface.Surface):
    cell_padding = 0.05
    size_x = screen_width // 2
    start_x = screen_width // 8
    start_y = screen_height // 2
    cell_size = size_x / word_length
    cell_padding_pixels = cell_size * cell_padding
    size_x += cell_padding_pixels * word_length - cell_padding_pixels
    size_y = (cell_size + cell_padding_pixels) * guesses - cell_padding_pixels

    font_size = int(cell_size * 0.75)
    font = pygame.font.SysFont(None, font_size, True)

    color_border = (58, 58, 60)
    color_correct = (83, 141, 78)
    color_valid = (181, 159, 59)
    color_invalid = color_border

    surface = pygame.surface.Surface((size_x, size_y))

    for row in range(guesses):
        for col in range(word_length):
            x = col * (cell_size + cell_padding_pixels)
            y = row * (cell_size + cell_padding_pixels)
            rect = pygame.rect.Rect(x,y, cell_size, cell_size)
            letter_check = row_patterns[row].letters[col]
            if letter_check.type == LetterCheck.INVALID:
                pygame.draw.rect(surface, color_invalid, rect)
            elif letter_check.type == LetterCheck.VALID:
                pygame.draw.rect(surface, color_valid, rect)
            elif letter_check.type == LetterCheck.CORRECT:
                pygame.draw.rect(surface, color_correct, rect)
            elif letter_check.type == LetterCheck.NONE:
                pygame.draw.rect(surface, color_border, rect, width=2, border_radius=2)

            char = rows[row][col] if col < len(rows[row]) else ""
            if char != "_" and char != " ":
                text_surf = font.render(char, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=rect.center)
                surface.blit(text_surf, text_rect)

    surface_rect = surface.get_rect(midleft=(start_x, start_y))
    screen.blit(surface, surface_rect)

def draw_possible_words(screen: pygame.surface.Surface):
    font = pygame.font.SysFont(None, 32)
    text_color = (255, 255, 255)

    text_surf = font.render(f"Possible words left: {len(word_list_processor.words)}", True, text_color)
    text_rect = text_surf.get_rect(midtop=(screen_width // 2, 10))
    screen.blit(text_surf, text_rect)


def draw_best_guesses(screen: pygame.surface.Surface):
    font = pygame.font.Font("assets/Iosevka/Iosevka-ExtraBold.ttc", 24)
    text_color = (255, 255, 255)

    screen_width = screen.get_width()
    y_offset = 25

    for guess, bits in best_guesses:
        text = f"{guess.upper()} : {bits:.2f} bits"
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect()
        text_rect.topright = (screen_width, y_offset)

        if y_offset + text_rect.height > screen.get_height():
            break

        screen.blit(text_surf, text_rect)
        y_offset += text_rect.height

def update_best_guesses():
    global best_guesses

    expected_informations: dict[str, float] = {}

    print("Computing expected information for words.")
    for word in word_list_processor.words:
        expected_informations[word] = word_list_processor.expected_information(word)

    print("Sorting best guesses.")
    best_guesses = sorted(
        expected_informations.items(),
        key=lambda item: item[1],
        reverse=True
    )

def handle_wordle_input():
    global input_pattern, current_col_index, current_row_index, best_guesses

    if rows[current_row_index][current_col_index-1] == "_":
        return

    if not input_pattern:
        current_col_index = 0
        input_pattern = True
        return

    if row_patterns[current_row_index].letters[current_col_index-1].type == LetterCheck.NONE:
        return

    matches = word_list_processor.get_matches(row_patterns[current_row_index], "".join(rows[current_row_index]).lower())
    word_list_processor.words = matches

    update_best_guesses()

    input_pattern = False
    current_col_index = 0
    current_row_index += 1

def main():
    global current_col_index, screen_width, screen_height, feedbacks, word_list_processor

    pygame.init()

    screen = pygame.display.set_mode((screen_width, screen_height), flags=pygame.RESIZABLE)
    pygame.display.set_caption("Wordle solver")
    icon = pygame.image.load("assets/wordle-icon.png")
    pygame.display.set_icon(icon)
    clock = pygame.time.Clock()

    if True:
        font = pygame.font.SysFont(None, 32)
        text_color = (255, 255, 255)

        text_surf = font.render(f"Loading (Check terminal for extra information)", True, text_color)
        text_rect = text_surf.get_rect(midtop=(screen_width // 2, 10))
        screen.blit(text_surf, text_rect)

        pygame.display.flip()

        feedbacks_file_path = "assets/feedbacks/precomputed-feedbacks.h5"
        if os.path.exists(feedbacks_file_path):
            print("Loading precomputed feedbacks")
            with h5py.File(feedbacks_file_path, "r") as f:
                arr = f["matrix"][:]
                feedbacks = arr.tolist()
        else:
            print("Precomputed feedbacks not found")
            print("Computing feedbacks")
            feedbacks = compute_feedbacks(all_words, word_length)
            print("Saving feedbacks")
            arr = numpy.array(feedbacks, dtype=numpy.int16)
            with h5py.File(feedbacks_file_path, "w") as f:
                f.create_dataset("matrix", data=arr, compression="gzip", compression_opts=9)

        word_list_processor = WordListProcessor(all_words, feedbacks)

        print("Updating best guess")
        update_best_guesses()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.VIDEORESIZE:
                screen_width = event.size[0]
                screen_height = event.size[1]

            if event.type == pygame.KEYDOWN:
                key = pygame.key.name(event.key)
                if key.isalpha() and len(key) == 1:
                    if current_col_index < word_length:
                        if input_pattern:
                            if key.upper() == "I":
                                row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.INVALID
                                current_col_index += 1
                            elif key.upper() == "V":
                                row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.VALID
                                current_col_index += 1
                            elif key.upper() == "C":
                                row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.CORRECT
                                current_col_index += 1
                        else:
                            rows[current_row_index][current_col_index] = key.upper()
                            current_col_index += 1
                if event.key == pygame.K_BACKSPACE:
                    if current_col_index > 0:
                        current_col_index -= 1
                        if input_pattern:
                            row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.NONE
                        else:
                            rows[current_row_index][current_col_index] = "_"
                if event.key == pygame.K_RETURN:
                    if current_col_index == word_length:
                        if "".join(rows[current_row_index]).lower() in all_words:
                            handle_wordle_input()

        if not running: break

        screen.fill((0,0,0))

        draw_wordle(screen)
        draw_possible_words(screen)
        draw_best_guesses(screen)

        pygame.display.flip()
        clock.tick(24)

    pygame.quit()

if __name__ == "__main__":
    main()