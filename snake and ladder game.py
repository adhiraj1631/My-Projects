import pygame
import sys
import random
import math
import pyttsx3  # Import the text-to-speech library

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
BOARD_SIZE = 700
CELL_SIZE = BOARD_SIZE // 10
DICE_SIZE = 100
PLAYER_SIZE = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
PURPLE = (128, 0, 128)
SNAKE_GREEN = (0, 100, 0)  # Dark green for snakes
YELLOW = (255, 255, 0)
GOLDEN = (218, 165, 32)  # Golden Colour

BOARD_COLORS = [RED, BLUE, GREEN, YELLOW, WHITE]

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()


class Board:
    def __init__(self, screen):
        self.screen = screen
        self.margin = (WINDOW_HEIGHT - BOARD_SIZE) // 2
        self.board_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
        self.font = pygame.font.Font(None, 36)
        self.start_font = pygame.font.Font(None, 48)  # Font for "Start"
        self.crown_image = pygame.image.load("crown.webp")  # Load the golden crown image (replace with your image)
        self.crown_image = pygame.transform.scale(self.crown_image, (CELL_SIZE, CELL_SIZE))  # Scale down the image

        # Load Board Image
        self.board_image = pygame.image.load("board_image.jpg")  # Replace "board.png" with your board image file
        self.board_image = pygame.transform.scale(self.board_image, (BOARD_SIZE, BOARD_SIZE))

        # Define snakes and ladders (more!)
        self.snakes = {
            17: 7,
            54: 34,
            62: 19,
            64: 60,
            87: 36,
            93: 73,
            95: 75,
            98: 78
        }

        self.ladders = {
            1: 38,
            4: 14,
            9: 31,
            21: 42,
            28: 84,
            51: 67,
            72: 91,
            80: 99
        }

        self.board_numbers = self.create_board_numbers()

    def create_board_numbers(self):
        numbers = []
        num = 1
        for row in range(10):
            row_numbers = []
            if row % 2 == 0:
                for col in range(10):
                    row_numbers.append(num + col)  # Normal order for even rows
            else:
                for col in range(10):
                    row_numbers.append(num + 9 - col)  # Reverse order for odd rows
            numbers.append(row_numbers)
            num += 10

        return numbers

    def get_cell_center(self, number):
        row = (number - 1) // 10  # Correct row calculation
        col = (number - 1) % 10 if row % 2 == 0 else 9 - (number - 1) % 10  # Correct column calculation
        x = col * CELL_SIZE + CELL_SIZE // 2
        y = (9 - row) * CELL_SIZE + CELL_SIZE // 2  # Y axis now inverted
        return (x, y)

    def get_row_col(self, number):
        row = (number - 1) // 10
        col = (number - 1) % 10 if row % 2 == 0 else 9 - (number - 1) % 10
        return row, col

    def draw_background(self, winner=None):  # Add winner as argument
        # Draw the board image
        self.board_surface.blit(self.board_image, (0, 0))
        # Add the Golden Crown at the 100 position for only the winner
        for row in range(10):
            for col in range(10):
                x = col * CELL_SIZE
                y = (9 - row) * CELL_SIZE
                number = self.board_numbers[row][col]
                # Add the Golden Crown at the 100 position for only the winner
                if number == 100 and winner:
                    crown_x = x
                    crown_y = y

                    self.board_surface.blit(self.crown_image, (crown_x, crown_y))

    def draw_snakes(self):
        pass  # Do not draw snakes

    def draw_ladders(self):
        pass  # Do not draw ladders

    def draw(self, winner=None):  # Added winner as arguments
        self.draw_background(winner)  # Pass winner to the background
        self.draw_snakes()  # calling do not draw snkaes
        self.draw_ladders()  # callling do not draw ladders
        self.screen.blit(self.board_surface, (self.margin, self.margin))


class Dice:
    def __init__(self, screen):
        self.screen = screen
        self.value = 1
        self.rolling = False
        self.roll_frames = 0
        self.position = (BOARD_SIZE + 150, 300)

    def roll(self):
        self.rolling = True
        self.roll_frames = 20

    def update(self):
        if self.rolling:
            if self.roll_frames > 0:
                self.value = random.randint(1, 6)
                self.roll_frames -= 1
            else:
                self.rolling = False

    def draw(self):
        # Draw dice body
        pygame.draw.rect(self.screen, WHITE,
                         (self.position[0], self.position[1], DICE_SIZE, DICE_SIZE))
        pygame.draw.rect(self.screen, BLACK,
                         (self.position[0], self.position[1], DICE_SIZE, DICE_SIZE), 2)

        # Draw dots based on dice value
        dot_positions = {
            1: [(0.5, 0.5)],
            2: [(0.25, 0.25), (0.75, 0.75)],
            3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
            4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
            5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
            6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75),
                (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)]
        }

        for pos in dot_positions[self.value]:
            x = self.position[0] + pos[0] * DICE_SIZE
            y = self.position[1] + pos[1] * DICE_SIZE
            pygame.draw.circle(self.screen, BLACK, (int(x), int(y)), 5)


class Player:
    def __init__(self, color, is_ai=False, name="Player"):
        self.position = 0  # Start off the board
        self.color = color
        self.is_ai = is_ai
        self.target_pos = None
        self.moving = False
        self.current_x = None
        self.current_y = None
        self.move_queue = []
        self.board = None  # to access board information.
        self.has_rolled_one = False  # player has rolled 1 to start the game
        self.name = name  # Give name of players

    def set_board(self, board):
        self.board = board

    def move_to(self, board, positions):
        self.move_queue = positions
        self.moving = True
        self.start_moving(board)

    def start_moving(self, board):
        if self.move_queue:
            self.target_pos = self.move_queue.pop(0)
            target_center = board.get_cell_center(self.target_pos)
            if self.current_x is None:
                current_center = board.get_cell_center(1)
                self.current_x = current_center[0]
                self.current_y = current_center[1]

    def update(self, board):
        if self.moving:
            target_center = board.get_cell_center(self.target_pos)
            dx = (target_center[0] - self.current_x) / 10
            dy = (target_center[1] - self.current_y) / 10

            self.current_x += dx
            self.current_y += dy

            if abs(self.current_x - target_center[0]) < 2 and abs(self.current_y - target_center[1]) < 2:
                self.position = self.target_pos
                self.current_x = target_center[0]
                self.current_y = target_center[1]
                if self.move_queue:
                    self.start_moving(board)
                else:
                    self.moving = False
                # Check the position of dice to see if it is less than 0
                if self.position <= 0:
                    self.position = 1

    def draw(self, screen, board):
        if self.position == 0:  # Draw off the board initially
            return  # Don't draw
        if self.current_x is None:
            center = board.get_cell_center(self.position)
            self.current_x = center[0]
            self.current_y = center[1]

        pygame.draw.circle(screen, self.color,
                           (int(self.current_x + board.margin),
                            int(self.current_y + board.margin)),
                           PLAYER_SIZE)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake and Ladder Game")

        self.board = Board(self.screen)
        self.dice = Dice(self.screen)
        self.player = Player(BLUE, name="You")  # Player's name
        self.ai_player = Player(RED, is_ai=True, name="AI")  # AI Player's Name
        self.player.set_board(self.board)
        self.ai_player.set_board(self.board)
        self.current_player = self.player
        self.game_state = "WAIT_FOR_ROLL"
        self.font = pygame.font.Font(None, 48)
        self.rolled_this_turn = False  # Track if dice was rolled this turn
        self.consecutive_sixes = 0  # Track if 3 consecutive 6 happened
        self.total_dice_value = 0  # Track how much value the dice holds
        self.last_two_rolls = []  # Track last two dice values for a special condition
        self.winner = None  # winner should be none intitally
        self.announce_turn() #Initial Announce

    def announce_turn(self):
        text = f"{self.current_player.name}'s turn."
        engine.say(text)
        engine.runAndWait()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN and self.game_state == "WAIT_FOR_ROLL" and not self.rolled_this_turn:
                self.roll_dice()
        return True

    def roll_dice(self):
        self.dice.roll()
        self.game_state = "ROLLING"
        self.rolled_this_turn = True

    def update(self):
        self.dice.update()
        self.player.update(self.board)
        self.ai_player.update(self.board)

        if self.game_state == "ROLLING" and not self.dice.rolling:
            self.last_two_rolls.append(self.dice.value)
            if len(self.last_two_rolls) > 2:
                self.last_two_rolls.pop(0)

            if self.dice.value == 6:
                self.consecutive_sixes += 1
                if self.consecutive_sixes < 3:
                    self.total_dice_value += self.dice.value
                    self.game_state = "WAIT_FOR_ROLL"  # gives bonus
                    self.rolled_this_turn = False
                else:
                    self.consecutive_sixes = 0  # three concequtive 6 resets everythng
                    self.total_dice_value = 0  # Reset bonus
                    self.handle_move()
            else:
                self.total_dice_value += self.dice.value
                self.handle_move()

        # Handle AI turn
        if self.current_player.is_ai and self.game_state == "WAIT_FOR_ROLL" and not self.rolled_this_turn:
            if not self.current_player.moving and not self.dice.rolling:
                pygame.time.wait(1000)  # Add delay for AI turn
                self.roll_dice()

    def handle_move(self):
        dice_value = self.total_dice_value
        self.total_dice_value = 0
        self.consecutive_sixes = 0
        self.rolled_this_turn = False
        current_position = self.current_player.position
        move_positions = []

        # Check for game-ending overreach
        needed_to_win = 100 - current_position
        if current_position >= 94 and dice_value > needed_to_win:  # is there any change for overreach
            self.switch_turn()  # If the dice is greater than the required number
            return

        # Winning condition check
        if current_position >= 94:  # checks that the postion is above 94
            needed_to_win = 100 - current_position

            # Check for invalid move condition
            if len(self.last_two_rolls) == 2 and self.dice.value == 3 and self.last_two_rolls[0] == 6 and self.last_two_rolls[1] == 6:
                self.switch_turn()  # changes the turn, because it is an invalid move
                self.last_two_rolls = []  # resets the values of last two rolls
                return  # Don't move

            if dice_value > needed_to_win:
                self.switch_turn()  # Turn changes, no move
                return  # No move
            elif dice_value == needed_to_win:
                next_position = current_position + dice_value
                move_positions.append(next_position)
            else:
                for i in range(dice_value):
                    next_position = current_position + 1
                    if next_position > 100:
                        break
                    move_positions.append(next_position)
                    current_position = next_position
        else:
            if not self.current_player.has_rolled_one:  # Check if the player has rolled a 1 at the beginning
                if dice_value == 1:
                    self.current_player.has_rolled_one = True  # Player can now move
                    move_positions.append(1)  # Moves from 0 to 1 directly
                    self.current_player.position = 1  # Set player position to 1 immediately
                    self.total_dice_value = 0  #
                else:
                    self.switch_turn()
                    return
            else:
                for i in range(dice_value):
                    next_position = current_position + 1
                    if next_position > 100:
                        break
                    move_positions.append(next_position)
                    current_position = next_position

        # Apply snakes and ladders at the final position
        if move_positions:
            final_position = move_positions[-1]
            # NO IMAGE JUST POSITION CHANGE
            if final_position in self.board.snakes:
                final_position = self.board.snakes[final_position]
                move_positions.append(final_position)
            elif final_position in self.board.ladders:
                final_position = self.board.ladders[final_position]
                move_positions.append(final_position)

            self.current_player.move_to(self.board, move_positions)
            self.game_state = "MOVING"
        else:
            self.switch_turn()

    def switch_turn(self):
        self.current_player = self.ai_player if self.current_player == self.player else self.player
        self.game_state = "WAIT_FOR_ROLL"
        self.rolled_this_turn = False  # Reset roll flag for the new turn
        self.last_two_rolls = []  # Reset last two rolls
        self.total_dice_value = 0
        self.announce_turn()  # Announce the turn change

    def check_winner(self):
        if self.player.position >= 100:
            self.winner = self.player
            return "Player Wins!"
        elif self.ai_player.position >= 100:
            self.winner = self.ai_player
            return "AI Wins!"
        return None

    def draw(self):
        winner_player = None
        winner_text = self.check_winner()
        if winner_text:  # if there is a winner
            if "Player" in winner_text:  # Checks in which player's text the Player word appears so that the system can know the winner player is a human or a AI
                winner_player = self.player
            else:
                winner_player = self.ai_player
        self.screen.fill(WHITE)
        self.board.draw(winner=winner_player)  # Passes the winner player as parameter
        self.dice.draw()
        self.player.draw(self.screen, self.board)
        self.ai_player.draw(self.screen, self.board)

        # Draw turn indicator
        turn_text = "Your Turn" if self.current_player == self.player else "AI Turn"
        text = self.font.render(turn_text, True, BLACK)
        self.screen.blit(text, (BOARD_SIZE + 150, 200))

        # Draw winner if game is over
        if winner_text:
            text = self.font.render(winner_text, True, GOLD)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 50))
            self.screen.blit(text, text_rect)

        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            running = self.handle_events()
            self.update()

            if self.game_state == "MOVING" and not self.current_player.moving:
                winner = self.check_winner()
                if not winner:
                    self.switch_turn()

            self.draw()
            clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()