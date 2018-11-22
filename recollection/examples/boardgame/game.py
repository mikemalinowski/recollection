"""
This demonstrates how we can use Memento to store the state of players
'pieces' on a board game. To demonstrate state history we assume on player
is an adult and one player a child - and therefore we want the child to 
be allowed to 'undo' their turn if they are not happy!
"""
import random
import recollection


# ------------------------------------------------------------------------------
def demo():
    """
    This will run a little demo example which prints out information about 
    each turn of a randomised game. 
    
    The dice rolls are random - as are the consequences of the turn. However
    the result will always be the 'child' winning the game due to the game
    being rolled-back (using memento) whenever the child is unhappy with their
    dice roll! 
    
    :return: 
    """
    # -- Start by instancing a game
    game = GameBoard('demo_game')

    # -- Add two players
    parent = game.add_player('Parent')
    child = game.add_player('Child')

    # -- Define this variable simply for readability in later
    # -- logic tests.
    good_outcome = True

    # -- Track our turn count so we can log it as we go
    turn_count = 1

    # -- Start the turn cycle!
    while not game.has_a_winner():

        print('starting turn %s...' % turn_count)

        for player in game.players.values():

            # - Roll the dice for the parent, and inform the game board
            outcome = game.move_player(
                player.name,
                player.roll_the_dice(),
            )

            # -- If the child is unhappy with their turn we must
            # -- revert the game state to what it was before the
            # -- dice roll!
            if player == child and outcome != good_outcome:
                game.state.restore(index=1)
                print('%s is undoing their turn!' % player.name)

        # -- Increment the turn count
        turn_count += 1


# ------------------------------------------------------------------------------
class GameBoard(object):
    """
    This is our gameboard object which tracks player progress throughout
    their game. We track position on the board and lives. Our win state
    for this demo is simply whoever survives!
    """
    def __init__(self, name_of_game):

        # - Store the name of the game
        self.name_of_game = name_of_game

        # -- We will use these variables to track
        # -- player progress
        self.players = dict()
        self.player_positions = dict()
        self.player_lives = dict()

        # -- Define our memento stack, allowing us to store state
        # -- and retrieve history
        self.state = recollection.Memento(self)

        # -- Define what we want to store from our game board
        self.state.register('player_lives')
        self.state.register('player_positions')
        self.state.register('name_of_game')

        # -- Define a serialiser - so that we can put the game
        # -- away and come back to it later if we want!
        self.state.register_serialiser(
            recollection.JsonAppSerialiser,
            'examples/boardgame/%s' % name_of_game
        )

        # -- Store the state as the zero state
        self.state.store()

    # --------------------------------------------------------------------------
    def add_player(self, name):
        """
        Adds a new player to the game, intialises the internal tracking
        variables etc
        """
        self.players[name] = Player(name)
        self.player_positions[name] = 0
        self.player_lives[name] = 5

        return self.players[name]

    # --------------------------------------------------------------------------
    def move_player(self, player_name, squares_to_move):
        """
        Moves the player by the given number, then prints a consequence
        and returns True if the consquence was positive and false if the
        consquence was negative.

        Crucially we store the state on ever roll - so if we need
        to go back, we can do.
        """
        self.player_positions[player_name] += squares_to_move

        # -- Randomly pick a consquence!
        result = random.randrange(0, 4)
        outcome = True

        if result < 2:
            # -- No consequnce
            pass

        elif result == 3:
            print('\t%s has been bitten by a snake!' % player_name)
            self.player_lives[player_name] -= 1
            outcome = False

        elif result == 4:
            print('\t%s has fallen down a rabbit hole!' % player_name)
            self.player_lives[player_name] -= 1
            outcome = False

        # -- Store the state after the move
        self.state.store()

        return outcome

    # --------------------------------------------------------------------------
    def has_a_winner(self):
        """
        Checks whether any players are dead and should be removed as well as 
        checking for a win state.
        """
        player_names = [name for name in self.players.keys()]

        for player_name in player_names:

            if self.player_lives[player_name] <= 0:
                self.players.pop(player_name)
                self.player_lives.pop(player_name)
                self.player_positions.pop(player_name)
                print('\t\t%s is out the game!' % player_name)

            else:
                print(
                    '\t\t%s has %s lives left!' % (
                        player_name,
                        self.player_lives[player_name],
                    )
                )

        if len(self.players) == 1:
            print('%s has won!' % list(self.players.values())[0].name)
            return True

        return False


# ------------------------------------------------------------------------------
class Player(object):
    """
    This class represents a player
    """

    # --------------------------------------------------------------------------
    def __init__(self, name):
        self.name = name

    # --------------------------------------------------------------------------
    def roll_the_dice(self):
        roll = random.randrange(1, 6)

        print(
            '\t%s has rolled %s' % (
                self.name,
                roll,
            )
        )

        return roll


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    demo()
