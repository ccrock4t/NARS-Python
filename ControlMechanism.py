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
        self.concept_sprite_list = None
        self.edge_sprite_list = None

        # Data list
        self.concept_sprite_to_name_list = {}

        #Pending concepts list
        self.pending_concepts_to_draw = []

        arcade.set_background_color(arcade.color.BLACK)

    def pend_new_concept_to_draw(self, name):
        # Set up your game here
        self.pending_concepts_to_draw.append(name)
        pass

    def draw_new_concept(self, name):
        # Set up your game here
        new_concept_sprite = arcade.SpriteCircle(15, arcade.color.WHITE)
        new_concept_sprite.center_x = self.drawX
        new_concept_sprite.center_y = 100

        self.drawX += 50

        self.concept_sprite_list.append(new_concept_sprite)
        self.concept_sprite_to_name_list[new_concept_sprite] = name
        pass

    def draw_new_edge(self):
        # Set up your game here
        self.edge_sprite_list.append()
        pass

    def setup(self):
        # Set up your game here
        self.concept_sprite_list = arcade.SpriteList()
        self.edge_sprite_list = arcade.SpriteList()
        pass

    def on_draw(self):
        """ Render the screen. """
        arcade.start_render()
        # Your drawing code goes here

        # Draw all the sprites.
        self.concept_sprite_list.draw()
        self.edge_sprite_list.draw()

        for concept_sprite in self.concept_sprite_list:
            name = self.concept_sprite_to_name_list[concept_sprite]
            arcade.draw_text(name, concept_sprite.center_x - concept_sprite.width / 2, concept_sprite.center_y, arcade.color.RED)

    def update(self, delta_time):
        """ All the logic to move, and the game logic goes here. """
        if len(self.pending_concepts_to_draw) > 0:
            term = self.pending_concepts_to_draw.pop(0)
            self.draw_new_concept(term)

        pass


memory = None

def main():
    global memory

    t = threading.Thread(target=get_user_input, name="user input thread")
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