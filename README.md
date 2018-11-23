# Recollection Overview
Recollection is a state recalling system. It allows for state of objects
to be snap-shotted exposing functionality to then 'rollback' to any
previously stored state.

Recollection gives two distinctly different exposures of this mechanism. If 
performance is not the most critical concern and your focus is on code
simplicity then the inheritence approach is possibly your best option
providing you have ownership of the classes which need historical state.

__Note: This is currently pre-release__

## Installation
You can install this using pip:
```commandline
pip install recollection
```

Alternatively you can get the source from:
https://github.com/mikemalinowski/recollection

## Recollection Inheritence (Inference)

This example shows how to setup a class using inheritence to 
automatically handle state storing. As you can see from the example, there
is no need to explicitly ask recollection to store at any time as it is handled
entirely for you. This example specifically shows attribute storing :

```python
import recollection

# -- Inference is the recollection class designed specifically
# -- for inheritance situations.
class Foo(recollection.Inference):

    def __init__(self):
        super(Foo, self).__init__()

        self.number = 10

        # -- Register 'number' as a property to monitor
        self.memento.register('number')


# -- Instance our object
foo = Foo()

# -- Here we demonstrate directly changing properties
# -- which are registered
foo.number = 5
foo.number = 99
print(foo.number == 99)

# -- Now restore back one step
foo.recollection.restore(1)
print(foo.number == 5)
```

Whilst this example shows how decorators can be utilised to store method
getters and setters:

```python
import recollection

# -- Inference is the recollection class designed specifically
# -- for inheritence situations.
class Foo(recollection.Inference):

    def __init__(self):
        super(Foo, self).__init__()
        self._number = 10

    # -- Declare that this is a recollection getter
    @recollection.infer.get('number')
    def number(self):
        return self._number

    # -- Declare this as a recollection setter
    @recollection.infer.store('number')
    def set_number(self, value):
        self._number = value

# -- Instance our object
foo = Foo()

# -- Update our variable using our accessor 
for number in range(10):
    foo.set_number(number)

# -- Demonstrate that the current state is 'e'
print(foo.number())  # -- Prints 9

# -- Roll back one step in the memento history
foo.recollection.restore(1)
print(foo.number())  # -- Prints 8

```

## Memento Stack
However, we do not always have the luxury of changing class inheritance
or you may specifically want to keep the recollection state management out
of your actual inheritance hierarchy. The following examples all demonstrate
how this can be achieved.

In this example we have a class with two properties. We the instance
a Memento class targeting our foo instance. Each time we call the
store method within Memento we are taking a snapshot of the values
returned by the registered properties/functions

```python
import recollection


class Foo(object):
    def __init__(self):
        self.number = 0

# -- Instance our object
foo = Foo()

# -- Instance a memento object pointing at foo
memento = recollection.Memento(foo)
memento.register('number')

# -- Start changing some values on foo, and
# -- ask our stack to store those changes
for number in range(11):
    foo.number = number

    # -- Ask the memento object to store the state
    memento.store()

# -- Printing i, shows us 10
print(foo.number)

# -- But lets say we roll back to the state 5 versions
# -- ago
memento.restore(5)

# -- Now we can see i is at the version it was when
# -- it was stored 5 versions back
print(foo.number)
```
### Lock-Stepped Storage

It also allows multiple Memento objects to be put into a lock-step,
such that whenever one memento object is storing or restoring then
all other memento objects in that sync group will also store or
restore.

```python
import recollection


class Foo(object):
    def __init__(self):
        self.number = 0

# -- This time we instance two completely seperate
# -- foo objects
foo_a = Foo()
foo_b = Foo()

# -- Instance a memento stack for each
memento_a = recollection.Memento(foo_a)
memento_b = recollection.Memento(foo_b)

memento_a.register('number')
memento_b.register('number')

# -- Now we will put our stacks into a state of lock-step
# -- which means whenever one of them is stored or restored
# -- all others in the lock-step group will have the same
# -- action performed
memento_a.group(memento_b)

# -- Increment some values on both objects
for i in range(11):
    foo_a.i = i
    foo_b.i = i

    # -- Trigger a store on only one stack
    memento_a.store()

# -- We can see that both A and B have a value of 10
print(foo_a.i == 10 and foo_b.i == 10)

# -- Now we rollback - knowing that this action will occur
# -- across all grouped memento objects
memento_a.restore(5)

# -- Now we can see i is at the version it was when
# -- it was stored 5 versions back
print(foo_a.i == 5 and foo_b.i == 5)
```

### Serialisation
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

```python
class UserPreferences(object):

    def __init__(self):

        # -- Visual preferences
        self._theme = 'default'

        # -- Define our memento, which we utilise specifically to
        # -- store our preferences to a persistent location
        self._memento = recollection.Memento(self)

        # -- We will utilise the JSON Appdata serialiser, which
        # -- writes our memento information to the app data system
        # -- location
        self._memento.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/demos/userprefs/UserPreferenceA',
        )

        # -- Register which properties we want the store to focus on
        self._memento.register(
            label='theme',
            getter=self.get_theme,
            setter=self.set_theme,
        )

        # -- Finally, we deserialise - which will update this class
        # -- with any previously stored state
        self._memento.deserialise()

    # --------------------------------------------------------------
    def get_theme(self):
        return self._theme

    # --------------------------------------------------------------
    def set_theme(self, theme):
        self._theme = theme
        self._memento.store(serialise=True)
```

### Decoration
Equally, if we want to make it a little more obvious at the class level 
which functions are storing we could opt to utilise the Memento decorator,
which stores and serialises:

```python
class UserPreferences(object):

    @recollection.serialise_after('theme')
    def set_theme(self, theme):
        self._theme = theme
```

# Examples
These mechanics are all demonstrated in the example modules, specifically:

### User Preferences Object
This demo shows a user preferences object being interacted
which which works in the same way as the example above, where the
settings are stored as changed come in - allowing the preferences to
be  'undone'.
```python
# -- This demo shows a user preferences object being interacted
# -- which which works in the same way as the example above.
from recollection.examples.userprefs.demo import demo

demo()
```

### Alternate User Preferences Object
This demo is identical to the demo above in terms of output but is 
handled through decorators.
```python
from recollection.examples.userprefs.demo import demo2

demo2()
```
    
### Board Game with roll-back
This demo utilises a 'boardgame' style scenario where
we're given two players and the desire to 'undo' the results
of turns if they are not desirable!
```python
from recollection.examples.boardgame.game import demo

demo()
```

### Pin Movement (Multi-attribute altering)
This demo shows the utilisation of a setter which is actually setting
multiple recorded attributes but wants to have a single restore step.
```python
from recollection.examples.pins.demo import demo

demo()
```


## Testing and Stability

There are currently unittests which cover most of Memento's core, but it is not yet exhaustive.

## Compatability

This has been tested under Python 2.7.13 and Python 3.6.6 on both Ubuntu and Windows.

## Contribute

If you would like to contribute thoughts, ideas, fixes or features please get in touch! mike@twisted.space
