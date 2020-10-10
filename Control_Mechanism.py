from NARSMemory import *
import InputBuffer
import arcade
import threading


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height):
        super().__init__(width, height)


        self.drawX = 100

        # Sprite Lists
        self.concept_list = None
        self.edge_list = None

        arcade.set_background_color(arcade.color.BLACK)

    def draw_new_concept(self):
        # Set up your game here
        new_concept = arcade.SpriteCircle(10, arcade.color.WHITE)
        new_concept.center_x = self.drawX
        new_concept.center_y = 100

        self.drawX += 20

        self.concept_list.append(new_concept)
        pass

    def draw_new_edge(self):
        # Set up your game here
        self.edge_list.append()
        pass

    def setup(self):
        # Set up your game here
        self.concept_list = arcade.SpriteList()
        self.edge_list = arcade.SpriteList()
        pass

    def on_draw(self):
        """ Render the screen. """
        arcade.start_render()
        # Your drawing code goes here

        # Draw all the sprites.
        self.concept_list.draw()
        self.edge_list.draw()

    def update(self, delta_time):
        """ All the logic to move, and the game logic goes here. """
        pass


memory = None

def main():
    global memory

    t = threading.Thread(target=get_user_input, name="arcade thread")
    t.daemon = True
    t.start()

    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    memory = Memory(game)
    game.setup()
    arcade.run()


def get_user_input():
    userinput = ""
    while userinput != "exit":
        userinput = input("")
        InputBuffer.add_input(userinput, memory)


if __name__ == "__main__":
    main()