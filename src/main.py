import os.path
import h5py
import pygame
import numpy
from words import all_words
from stuff import LetterCheck, LetterCheckPattern, WordListProcessor
from feedbacks import compute_feedbacks

# Define global variables
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

# Draw the wordle grid to the screen.
def draw_wordle(screen: pygame.surface.Surface):
    cell_padding = 0.05 # Fraction of the cell size that is used as the distance between cells
    size_x = screen_width // 2
    start_x = screen_width // 8
    start_y = screen_height // 2
    cell_size = size_x / word_length
    cell_padding_pixels = cell_size * cell_padding
    size_x += cell_padding_pixels * word_length - cell_padding_pixels
    size_y = (cell_size + cell_padding_pixels) * guesses - cell_padding_pixels

    font_size = int(cell_size * 0.75)
    font = pygame.font.SysFont(None, font_size, True)

    color_border = (58, 58, 60) # Color for the border
    color_correct = (83, 141, 78) # Color for correct letter
    color_valid = (181, 159, 59) # Color for valid letter
    color_invalid = color_border # Color for invalid letter is the same as the border

    surface = pygame.surface.Surface((size_x, size_y)) # Create a surface for the wordle grid

    # Loop over all rows and columns
    for row in range(guesses):
        for col in range(word_length):
            # Calculate the position for the letter
            x = col * (cell_size + cell_padding_pixels)
            y = row * (cell_size + cell_padding_pixels)
            rect = pygame.rect.Rect(x,y, cell_size, cell_size) # Create a rectangle for that letter

            letter_check = row_patterns[row].letters[col] # Get the letter check for the row and col of the current letter
            if letter_check.type == LetterCheck.INVALID:
                # If invalid draw solid invalid color
                pygame.draw.rect(surface, color_invalid, rect)
            elif letter_check.type == LetterCheck.VALID:
                # If valid draw solid valid color
                pygame.draw.rect(surface, color_valid, rect)
            elif letter_check.type == LetterCheck.CORRECT:
                # If correct draw solid correct color
                pygame.draw.rect(surface, color_correct, rect)
            elif letter_check.type == LetterCheck.NONE:
                # If no letter then just draw the border using border color
                pygame.draw.rect(surface, color_border, rect, width=2, border_radius=2)

            # Draw the letter for the current row and column
            char = rows[row][col] if col < len(rows[row]) else ""
            if char != "_" and char != " ":
                text_surf = font.render(char, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=rect.center)
                surface.blit(text_surf, text_rect)

    # Get surface rectangle for the wordle grid and draw it to the main screen with the middle left set to the origin
    surface_rect = surface.get_rect(midleft=(start_x, start_y))
    screen.blit(surface, surface_rect)

# Draw the number of possible answer words at the top of the screen
def draw_possible_words(screen: pygame.surface.Surface):
    font = pygame.font.SysFont(None, 32) # Some random font
    text_color = (255, 255, 255) # White

    # Render text and blit to screen with origin at middle top
    text_surf = font.render(f"Possible words left: {len(word_list_processor.words)}", True, text_color)
    text_rect = text_surf.get_rect(midtop=(screen_width // 2, 10))
    screen.blit(text_surf, text_rect)

# Draw the best guesses on the right of the screen
def draw_best_guesses(screen: pygame.surface.Surface):
    font = pygame.font.Font("assets/Iosevka/Iosevka-ExtraBold.ttc", 24) # Monospace font
    text_color = (255, 255, 255) # White

    y_offset = 25 # Offset for each word on the y axis

    # Loop over all guesses
    for guess, bits in best_guesses:
        text = f"{guess.upper()} : {bits:.2f} bits" # Format text using the word and the bits of information
        # Render text and set origin
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect()
        text_rect.topright = (screen_width, y_offset)

        # Make sure not to render text that is off-screen
        if y_offset + text_rect.height > screen.get_height():
            break

        screen.blit(text_surf, text_rect) # Render text
        y_offset += text_rect.height # Move to next word position

# Recalculate the best guesses and sort them by bits of information
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

# Handle when the user presses enter
def handle_wordle_input():
    global input_pattern, current_col_index, current_row_index, best_guesses

    # If the user hasn't input all letters then don't do anything
    if rows[current_row_index][current_col_index-1] == "_":
        return

    # Switch to inputting the pattern instead of letters
    if not input_pattern:
        current_col_index = 0
        input_pattern = True
        return

    # If the user hasn't input the whole pattern then don't do anything.
    if row_patterns[current_row_index].letters[current_col_index-1].type == LetterCheck.NONE:
        return

    # Calculate all possible matches for the word and pattern out of the list of words
    matches = word_list_processor.get_matches(row_patterns[current_row_index], "".join(rows[current_row_index]).lower())
    word_list_processor.words = matches # Set the list of words to the matches

    update_best_guesses() # Recalculate best guesses

    # Switch back to letter input and reset input location to the start of the word
    input_pattern = False
    current_col_index = 0
    current_row_index += 1

def main():
    global current_col_index, screen_width, screen_height, feedbacks, word_list_processor

    pygame.init() # Init pygame (duh)

    screen = pygame.display.set_mode((screen_width, screen_height), flags=pygame.RESIZABLE) # Set screen size and allow user to resize the screen
    pygame.display.set_caption("Wordle solver") # Set the window title
    icon = pygame.image.load("assets/wordle-icon.png") # Load the icon from assets folder
    pygame.display.set_icon(icon) # Set window icon to the icon asset
    clock = pygame.time.Clock() # Create a clock to limit frame rate

    if True: # This is just to create a scope so that these variables aren't accessible in the whole main function
        font = pygame.font.SysFont(None, 32) # Default system font
        text_color = (255, 255, 255) # White

        # Render loading text
        text_surf = font.render(f"Loading (Check terminal for extra information)", True, text_color)
        text_rect = text_surf.get_rect(midtop=(screen_width // 2, 10))
        screen.blit(text_surf, text_rect)
        pygame.display.flip() # Swap front and back buffer to display loading text

        # Check for precomputed feedback database file
        feedbacks_file_path = "assets/feedbacks/precomputed-feedbacks.h5"
        if os.path.exists(feedbacks_file_path):
            # If exists load it
            print("Loading precomputed feedbacks")
            with h5py.File(feedbacks_file_path, "r") as f:
                arr = f["matrix"][:]
                feedbacks = arr.tolist()
        else:
            # If not exist then invoke shared library to compute it then save to database file
            print("Precomputed feedbacks not found")
            print("Computing feedbacks")
            feedbacks = compute_feedbacks(all_words, word_length)
            print("Saving feedbacks")
            arr = numpy.array(feedbacks, dtype=numpy.int16)
            with h5py.File(feedbacks_file_path, "w") as f:
                f.create_dataset("matrix", data=arr, compression="gzip")

        # Initialize the word list processor
        word_list_processor = WordListProcessor(all_words, feedbacks)

        # Compute the best guesses (this takes forever)
        print("Updating best guess")
        update_best_guesses()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # If the user presses close then stop the loop on next iteration
                running = False
                break

            if event.type == pygame.VIDEORESIZE:
                # If the user resizes the window then update the global variables to match
                screen_width = event.size[0]
                screen_height = event.size[1]

            if event.type == pygame.KEYDOWN:
                # If the user presses a key
                key = pygame.key.name(event.key) # Get key pressed as a string
                if key.isalpha() and len(key) == 1: # Check if the key is a single alphabetical letter
                    if current_col_index < word_length: # If the current column is inside the word
                        if input_pattern: # If inputting validity pattern
                            if key.upper() == "I":
                                # If invalid
                                row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.INVALID
                                current_col_index += 1
                            elif key.upper() == "V":
                                # If valid
                                row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.VALID
                                current_col_index += 1
                            elif key.upper() == "C":
                                # If correct
                                row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.CORRECT
                                current_col_index += 1
                        else:
                            # Else inputting letters so just record the letter as uppercase to the current column
                            rows[current_row_index][current_col_index] = key.upper()
                            current_col_index += 1
                if event.key == pygame.K_BACKSPACE:
                    # If user presses backspace then we delete the last letter or pattern
                    if current_col_index > 0: # Make sure there is something to delete
                        current_col_index -= 1 # Move back one column
                        if input_pattern: # Pattern delete
                            row_patterns[current_row_index].letters[current_col_index].type = LetterCheck.NONE
                        else: # Letter delete
                            rows[current_row_index][current_col_index] = "_"
                if event.key == pygame.K_RETURN:
                    # If user presses enter/return key then we want to handle that using the handle_wordle_input function
                    if current_col_index == word_length: # Check if the current column is at the end of the word
                        if "".join(rows[current_row_index]).lower() in all_words: # Check if the input word is a valid word
                            handle_wordle_input() # Handle the input

        if not running: break # Stop game if not running

        screen.fill((0,0,0)) # Clear screen

        # Render things
        draw_wordle(screen)
        draw_possible_words(screen)
        draw_best_guesses(screen)

        # Swap front and back buffers
        pygame.display.flip()
        clock.tick(24) # Limit to 24 fps

    # Quit pygame after exiting main loop
    pygame.quit()

if __name__ == "__main__":
    main()