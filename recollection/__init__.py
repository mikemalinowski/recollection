# Copyright (c) 2018 Michael Malinowski
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""
Recollection is a state recalling system. It allows for state of objects
to be snap-shotted exposing functionality to then 'rollback' to any
previously stored state.

Memento gives two distinctly different exposures of this mechanism. If 
performance is not the most critical concern and your focus is on code
simplicity then the inheritence approach is possibly your best option
providing you have ownership of the classes which need historical state.

This example shows how to setup a class using memento inheritence to 
automatically handle state storing. As you can see from the example, there
is no need to explicitely ask memento to store at any time as it is handled
entirely for you :

    ..code-block:: python
        
    >>> import recollection
    >>> 
    >>> # -- Inference is the Memento class designed specifically
    >>> # -- for inheritence situations.
    >>> class Foo(recollection.Inference):
    ... 
    ...     def __init__(self):
    ...         super(Foo, self).__init__()
    ... 
    ...         # -- Demonstrate a private attribute with getter
    ...         # -- and setter methods
    ...         self._letter = 1
    ... 
    ...         # -- Demonstrate public attributes which should be
    ...         # -- stored whenever they are changed
    ...         self.number = 10
    ... 
    ...         # -- Because we're inheriting from the Inference class, any
    ...         # -- registered properties will automatically trigger a
    ...         # -- state store whenever they are changed.
    ...         self.memento.register('number')
    ... 
    ...     # -- Declare that this is a memento getter
    ...     @recollection.infer.get('foobar')
    ...     def letter(self):
    ...         return self._letter
    ... 
    ...     # -- Declare this as a memento setter, using the same
    ...     # -- label as the getter. Whenever setHeight is called
    ...     # -- it will automatically store the state change.
    ...     @recollection.infer.store('foobar')
    ...     def setLetter(self, value):
    ...         self._letter = value
    >>> 
    >>> # -- Instance our object
    >>> foo = Foo()
    >>> 
    >>> # -- Update our variable using our accessor - which will automatically
    >>> # -- incur a state store
    >>> for letter in ['a', 'b', 'c', 'd', 'e']:
    ...     foo.setLetter(letter)
    >>> 
    >>> # -- Demonstrate that the current state is 'e'
    >>> print(foo.letter())  # -- Prints 'e'
    >>> 
    >>> # -- Roll back one setp and demonstrate that the property
    >>> # -- now evaluates to 'd'
    >>> foo.memento.restore(1)
    >>> print(foo.letter())  # -- Prints 'd'
    >>> 
    >>> # -- Here we demonstrate directly changing properties
    >>> # -- which are registered
    >>> foo.number = 5
    >>> foo.number = 99
    >>> print(foo.number == 99)
    >>> 
    >>> # -- Now restore back one step
    >>> foo.memento.restore(1)
    >>> print(foo.number == 5)

However, we do not always have the luxury of changing class inheritence
or you may specifically want to keep the memento state management out
of your actual inheeritence hierachy. The following examples all demonstrate
how this can be achieved.

In this example we have a class with two properties. We the instance
a Memento class targeting our foo instance. Each time we call the
store method within Memento we are taking a snapshot of the values
returned by the registered properties/functions

..code-block:: python

    >>> import recollection
    >>>
    >>>
    >>> class Foo(object):
    ...     def __init__(self):
    ...         self.name = 'bar'
    ...         self.i = 0
    >>>
    >>> # -- Instance our object
    >>> foo = Foo()
    >>>
    >>> # -- Instance a memento object pointing at foo
    >>> stack = recollection.Memento(foo)
    >>> stack.register('i')
    >>>
    >>> # -- Start changing some values on foo, and
    >>> # -- ask our stack to store those changes
    >>> for i in range(11):
    ...     foo.i = i
    ...
    ...     # -- Ask the memento object to store the state
    ...     stack.store()
    >>>
    >>> # -- Printing i, shows us 10
    >>> print(foo.i)
    >>>
    >>> # -- But lets say we roll back to the state 5 versions
    >>> # -- ago
    >>> stack.restore(5)
    >>>
    >>> # -- Now we can see i is at the version it was when
    >>> # -- it was stored 5 versions back
    >>> print(foo.i)

It also allows multiple Memento objects to be put into a lock-step,
such that whenever one memento object is storing or restoring then
all other memento objects in that sync group will also store or
restore.

..code-block:: python

    >>> import recollection
    >>>
    >>>
    >>> class Foo(object):
    ...     def __init__(self):
    ...         self.name = 'bar'
    ...         self.i = 0
    >>>
    >>> # -- This time we instance two completely seperate
    >>> # -- foo objects
    >>> foo_a = Foo()
    >>> foo_b = Foo()
    >>>
    >>> # -- Instance a memento stack for each
    >>> stack_a = recollection.Memento(foo_a)
    >>> stack_b = recollection.Memento(foo_b)
    >>>
    >>> stack_a.register(['name', 'i'])
    >>> stack_b.register(['name', 'i'])
    >>>
    >>> # -- Now we will put our stacks into a state of lock-step
    >>> # -- which means whenever one of them is stored or restored
    >>> # -- all others in the lock-step group will have the same
    >>> # -- action performed
    >>> stack_a.group(stack_b)
    >>>
    >>> # -- Increment some values on both objects
    >>> for i in range(11):
    ...     foo_a.i = i
    ...     foo_b.i = i
    ...
    ...     # -- Trigger a store on only one stack
    ...     stack_a.store()
    >>>
    >>> # -- We can see that both A and B have a value of 10
    >>> print(foo_a.i == 10 and foo_b.i == 10)
    >>>
    >>> # -- Now we rollback - knowing that this action will occur
    >>> # -- across all grouped memento objects
    >>> stack_a.restore(5)
    >>>
    >>> # -- Now we can see i is at the version it was when
    >>> # -- it was stored 5 versions back
    >>> print(foo_b.i)
    >>> print(foo_a.i == 5 and foo_b.i == 5)

Serialisers can also be registered against memento instances allowing
the stored state of a memento object to be serialised into a persistent
state.

This example shows how we might define a user preferences class, and
within that class we define a memento object to store the preference
state. By registering a serialiser the preferences state will be written
to disk whenever the 'store' is called.

Notice that in this example we're also choosing not to store private
member variables, but instead we're harnessing the public api of the
class as getters and setters.

..code-block:: python

    >>> class UserPreferences(object):
    ...
    ...     def __init__(self):
    ...
    ...         # -- Visual preferences
    ...         self._theme = 'default'
    ...
    ...         # -- Define our memento, which we utilise specifically to
    ...         # -- store our preferences to a persistent location
    ...         self._stack = recollection.Memento(self)
    ...
    ...         # -- We will utilise the JSON Appdata serialiser, which
    ...         # -- writes our memento information to the app data system
    ...         # -- location
    ...         self._stack.register_serialiser(
    ...             serialiser=recollection.JsonAppSerialiser,
    ...             identifier='memento/demos/userprefs/UserPreferenceA',
    ...         )
    ...
    ...         # -- Register which properties we want the store to focus on
    ...         self._stack.register(
    ...             label='theme',
    ...             getter=self.get_theme,
    ...             setter=self.set_theme,
    ...         )
    ...
    ...         # -- Finally, we deserialise - which will update this class
    ...         # -- with any previously stored state
    ...         self._stack.deserialise()
    ...
    ...     # --------------------------------------------------------------
    ...     def get_theme(self):
    ...         return self._theme
    ...
    ...     # --------------------------------------------------------------
    ...     def set_theme(self, theme):
    ...         self._theme = theme
    ...         self._stack.store(serialise=True)

Equally, if we want to make it a little more obvious at the class level 
which functions are storing we could opt to utilise the Memento decorator,
which stores and serialises:

    ..code-block:: python
    
    >>> from recollection import Memento
    >>>
    >>> class UserPreferences(object):
    ...
    ...     @Memento.serialise_after('theme')
    ...     def set_theme(self, theme):
    ...         self._theme = theme

Here we see an example of state being used as a roll-back feature, which
is particularly useful when allowing users to interact with data:

    ..code-block:: python

        >>> import recollection
        >>>
        >>>
        >>> class Foo(object):
        ...
        ...     def __init__(self):
        ...         self._x = 10
        ...         self._y = 20
        ...
        ...         self._stack = recollection.Memento(self)
        ...         self._stack.register(['_x', '_y',])
        ...
        ...         # -- Store the default state
        ...         self._stack.store()
        ...
        ...     def x(self):
        ...         return self._x
        ...
        ...     def setX(self, value):
        ...         self._x = value
        ...         self._stack.store()
        ...
        ...     def y(self):
        ...         return self._x
        ...
        ...     def setY(self, value):
        ...         self._y = value
        ...         self._stack.store()
        ...
        ...     def undo(self):
        ...         self._stack.restore()
        >>>
        >>> # -- Instance our foo object and print the default
        >>> # -- value
        >>> foo = Foo()
        >>> print('Default Value : %s' % foo.x())
        Default Value : 10
        >>>
        >>> # -- Set the value to 200
        >>> foo.setX(200)
        >>> print('Changed Value : %s' % foo.x())
        Changed Value : 200
        >>>
        >>> # -- Undo the last action, and print that we're not back
        >>> # -- to a value the same as the default
        >>> foo.undo()
        >>> print('Back to the default value after undo : %s' % foo.x())
        Back to the default value after undo : 10

These mechanics are demonstrated in the example modules, specifically:

    ..code-block:: python

        >>> # -- This demo shows a user preferences object being interacted
        >>> # -- which which works in the same way as the example above.
        >>> from recollection.examples.userprefs.demo import demo
        >>>
        >>> demo()

    ..code-block:: python

        >>> # -- This demo shows a user preferences object being interacted
        >>> # -- which which works by decorating setter properties
        >>> from recollection.examples.userprefs.demo import demo2
        >>>
        >>> demo2()

    ..code-block:: python

        >>> # -- This demo utilises a 'boardgame' style scenario where
        >>> # -- we're given two players and the desire to 'undo' the results
        >>> # -- of turns if they are not desirable!
        >>> from recollection.examples.boardgame.game import demo
        >>>
        >>> demo()
    
    ..code-block:: python

        >>> # -- This demo utilises a 'boardgame' style scenario where
        >>> # -- we're given two players and the desire to 'undo' the results
        >>> # -- of turns if they are not desirable!
        >>> from recollection.examples.pins.demo import demo
        >>>
        >>> demo()

"""
__author__ = "Michael Malinowski"
__copyright__ = "Copyright (C) 2018 Michael Malinowski"
__license__ = "MIT"
__version__ = "0.9.2"

from .core import (
    Memento,
)

from .inference import (
    Inference,
)

from .serialiser import (
    SerialiserBase,
)

from .serialisers import (
    PickleSerialiser,
    JsonAppSerialiser,
)

from . exceptions import (
    StorageError,
    RegistrationError,
)

from . import infer
