"""
This demo attempts to show how we can user Inference within Memento 
to make setting up states trivial. It also shows how we might have 
an object with lots of inter-twining properties, and therefore is a
good example of where we can reliably roll-back at an object level.

It also shows using a mix of getters and setters in a more pracical
example.
"""
import math
import recollection


# ------------------------------------------------------------------------------
def demo():

    # -- Instance a pin
    pin = Pin()

    # -- Move the pin multiple times
    pin.move_to([1, 1], 1)
    pin.move_to([2, 2], 2)

    # -- Print our interim details so we can compare later
    print('Interim Destination : %s' % pin.position())
    print('\tDistance Moved : %s' % pin.distance_moved)
    print('\tTime Moving : %s' % pin.time_travelled)

    # -- Do a final move
    pin.move_to([10, 10], 1)

    # -- Print the current position and distance moved
    print('\nEnd Destination : %s' % pin.position())
    print('\tDistance Moved : %s' % pin.distance_moved)
    print('\tTime Moving : %s' % pin.time_travelled)

    # -- Now lets do one roll-back
    pin.memento.restore(1)

    # -- Print the fact that we have done one restore
    # -- step but all values are correctly rolled back
    # -- together
    print('\nRolled Back Destination : %s' % pin.position())
    print('\tDistance Moved : %s' % pin.distance_moved)
    print('\tTime Moving : %s' % pin.time_travelled)


# ------------------------------------------------------------------------------
class Pin(recollection.Inference):

    def __init__(self):
        super(Pin, self).__init__()

        # -- Public Properties
        self.distance_moved = 0
        self.time_travelled = 0

        # -- Private/Complex Properies
        self._current_position = [0, 0]

        self.memento.register(
            [
                'distance_moved',
                'time_travelled',
            ]
        )

    # --------------------------------------------------------------------------
    @recollection.infer.get('position')
    def position(self):
        return self._current_position

    # --------------------------------------------------------------------------
    @recollection.infer.store('position')
    def move_to(self, position, speed=1):

        # -- Because this method is already decorated, it will store
        # -- state on exit. Therefore we want to tell memento not
        # -- to store any per-property changes which means we get all
        # -- the changes in a single step
        with self.memento.omit():

            # -- Calculate the distance travelled
            travel_distance = self._distance(
                self._current_position,
                position,
            )

            # -- Set the distance travelled, calcualte the time
            # -- travelled based on the speed and update the position.
            # -- This is a good example of multiple properties being
            # -- closely coupled which are important to keep in step
            # -- with one-another should we want to 'undo' our move.
            self.distance_moved += travel_distance
            self.time_travelled += travel_distance / float(speed)
            self._current_position = position

    # --------------------------------------------------------------------------
    @classmethod
    def _distance(cls, p1, p2):
        distance = math.sqrt(
            math.pow(p2[0] - p1[0], 2) + math.pow(p2[1] - p1[1], 2),
        )

        return distance


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    demo()
