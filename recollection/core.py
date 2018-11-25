from . import exceptions
from .constants import log
from .signal import Signal
from .serialiser import SerialiserBase
from contextlib import contextmanager

import six
import copy
import weakref


# ------------------------------------------------------------------------------
class Memento(object):
    """
    The Memento class aims to lower the development overhead of implementing
    storable state as well as offering functionality to step backward to 
    previous states along with state serialisation for persistent state.
    """

    # -- This is a list of recollection objects which should all store
    # -- and restore whenever any other in the sync group does.
    _SYNC_GROUPS = list()

    # --------------------------------------------------------------------------
    def __init__(self, target, max_states=100):

        # -- Define our callback signals to allow other mechanisms
        # -- to hook into recollection events
        self.stored = Signal()
        self.restored = Signal()
        self.registered = Signal()
        self.unregistered = Signal()

        # -- If True, this property will omit any calls
        # -- to store. This is a useful mechanism when wanting
        # -- to defer lots of changes into a single step
        self._defer = False

        # -- Store the object we want to store state
        # -- for
        self._target = weakref.ref(target)

        # -- Define the list which we will store states in
        self._states = list()
        self._max_states = max_states

        # -- Store properties need to read when serialising
        # -- and de-serialising
        self._items_to_record = list()

        # -- Store the registered serialiser (if required)
        self._serialiser = None
        self._serialisation_identifier = None
        self._always_serialise = False

    # --------------------------------------------------------------------------
    def register(self, getter, setter=None, label=None, copy_value=True):
        """
        This registers an attribute/method to call or read whenever the 
        store method is called.
        
        :param getter: This is what should be used to get the value.
        :type getter: If a string, the object the recollection is trying to 
            store state for will be accessed using a 'getattr' call. If
            a method or function the given function will be stored - and
            is expected to be callable with no arguments.
            Alternatively this can be a list, in which case this function
            will be called for each element in the list.
            
        :param setter: If omitted the getter is used for the setter. This 
            is typical for attributes - where we do not need to need to set
            any differently to how we get. However, if you have methods for 
            setting and getting (such as getName, setName) you can define
            the setter here.
        :type setter: str or method
        
        :param label: This allows you to tailor how the values relating
            to this registration are stored. If the getter is a string this
            argument can be omitted, otherwise it should be provided.
        :type label: str
        
        :param copy_value: This is important if you're storing complex object
            types which are mutable. By default we take a copy of all values
            we recieve to ensure they cannot be modified outside of the 
            snapshot. However, if you want to store classes where you 
            specifically do not want them copied and instead want them
            referenced you may set this value to false.
        :type copy_value: bool
        :return: 
        """

        # -- If we're given a list we consider it a list of argument
        # -- sets, so we call this function for each element.
        if isinstance(getter, (list, tuple)):
            for item in getter:
                if isinstance(item, (list, tuple)):
                    self.register(*item)

                else:
                    self.register(item)

            return

        # -- If a setter was not defined we assume we're
        # -- to use the getter for both
        setter = setter or getter
        label = label or getter

        # -- Get a list of existing labels so we can check for dupilcates
        existing_labels = [
            record_.label
            for record_ in self._items_to_record
        ]

        # -- Do a final test to ensure we have everything we need
        if label in existing_labels:
            raise exceptions.RegistrationError(
                '%s is already registered. You must un-register this entry '
                'before re-registering.'
            )

        # -- Create an accessing pair
        item = _ItemToRecord(
            target=self._target,
            label=label,
            getter=getter,
            setter=setter,
            copy_value=copy_value
        )

        # -- Store the entries
        self._items_to_record.append(item)

        # -- Emit the event
        self.registered.emit()

        # -- Log the result
        log.debug(
            'Registered %s : \n\tGetter: %s \n\tSetter: %s' % (
                label,
                getter,
                setter,
            )
        )

    # --------------------------------------------------------------------------
    def unregister(self, label):
        """
        This will unregister an item from recollection. By unregistering an item
        that item will not longer be stored in any subsequent sates. It will
        not remove it from previous states, but it will be ignored data (in that
        unregistered data will never be restored).
        
        :param label:  This should be the label (or name of the attribute)
            to be unregistered
        :type label: str
        :return: 
        """
        # -- To prevent list mutation during iteration
        # -- we get a list of items we need to remove
        items_to_remove = [
            item
            for item in self._items_to_record
            if item.label == label
        ]

        # -- Iterate until all these items are gone
        while items_to_remove:
            item = items_to_remove.pop()

            self._items_to_record.remove(item)

            # -- Emit the event
            self.unregistered.emit()

            # -- Log the removal
            log.debug(str(item))

    # --------------------------------------------------------------------------
    def store(self, serialise=False):
        """
        This will initiate a snapshot of the targets values, calling or 
        retrieving values from any of the registered attributes or methods.
        
        :param serialise: If true a serialisation (to persistent data) will
            be performed once the store is complete. If no serialiser is 
            registered this will be be skipped.
        :type serialise: bool 
        """
        if self._defer:
            return

        # -- Given that our target is a weak ref we need to access
        # -- it through a call. If it has already been garbage
        # -- collected we need to raise an exception
        if not self._target():
            raise exceptions.StorageError('Target object is no longer in scope')

        # -- Define the dictionary to which we will store all the
        # -- targets details
        snapshot = dict()

        # -- We specifically store information based on what has been
        # -- registered wtih the recollection object, so we cycle that
        for item in self._items_to_record:
            snapshot[item.label] = item.get()

        # -- Insert the new stored state at the start
        # -- of the list
        self._states.insert(0, snapshot)

        # -- If our max states has been exceeded we start
        # -- removing them
        if self._max_states and len(self._states) > self._max_states:
            self._states.pop()

        # -- If we need to serialise, do so now
        if serialise or self._always_serialise:
            self.serialise()

        # -- Add some debug output
        log.debug('Stored Snapshot for %s' % self._target)

        # -- Emit the event
        self.stored.emit()

        # -- Call the store on any members this is marked as keeping
        # -- in sync step with
        with _SyncGroupPropogation(self) as sync_group:
            for memento in sync_group:
                memento.store(serialise=serialise)

    # --------------------------------------------------------------------------
    def restore(self, index=0):
        """
        This will restore the state of the target object to that of the
        given index. 
        
        An index of 0 is the current state - and therefore will have no 
        impact. An index of 1 will mean the state will go back 1 step. An
        index of 2 will mean the state will go back two steps and so forth.
        
        :param index: The amount of steps to go back by.
        :type index: int 
        """

        with self.defer():
            # -- Access the snapshot from the state stack
            snapshot = self._states[index]

            # -- Cycle over all the items we have been told to record
            for item in self._items_to_record:
                item.set(snapshot[item.label])

            # -- Log the removal
            log.debug(
                'Restored State [%s] to : %s' % (
                    index,
                    snapshot,
                )
            )

            # -- Call the store on any members this is marked as keeping
            # -- in sync step with
            with _SyncGroupPropogation(self) as sync_group:
                for memento in sync_group:
                    memento.restore(index=index)

        # -- Emit the event
        self.restored.emit()

    # --------------------------------------------------------------------------
    @contextmanager
    def defer(self, serialise=False):
        """
        This allows the deferring of stores for the duration of the context
        after which a store is called.
        
        :param serialise: Whether to serialise once the context finishes
        
        :return: None
        """
        self._defer = True
        yield None
        self._defer = False
        self.store(serialise=serialise)

    # --------------------------------------------------------------------------
    @contextmanager
    def omit(self):
        """
        This allows changes to be made without any storing occuring even
        though decorated functions or registered properties may be altered.

        :return: None
        """
        self._defer = True
        yield None
        self._defer = False

    # --------------------------------------------------------------------------
    def register_serialiser(self,
                            serialiser,
                            identifier,
                            always_serialise=False):
        """
        This allows you to register the serialiser you want to utilise.

        :param serialiser: Serialiser type. This does not need to be
            instanced, as all methods on serialisers are static.
        :type serialiser: Type recollection.SerialiserBase

        :param identifier: This is the identifier that should be given
            to the serialiser in order to process the request and store
            the data in the expected way. You should read the documentation
            of the serialiser in question to find the specific expectations.
        :type identifier: str
        
        :param always_serialise: If true, this will always serialise regardless
            of the argument given during the store call.
        :type always_serialise: bool
        
        :return: None
        """
        # -- Validate that the serialiser is indeed a serialiser!
        if not issubclass(serialiser, SerialiserBase):
            raise TypeError(
                '%s is not a subclass of %s' % (
                    serialiser,
                    SerialiserBase,
                )
            )

        # -- Store both the serialiser and the identifer at the
        # -- instance level to make it nice and easy for the
        # -- user to call a serialisation process.
        self._serialiser = serialiser
        self._serialisation_identifier = identifier
        self._always_serialise = always_serialise

        # -- Log the removal
        log.debug(
            'Serialiser Registered : %s' % serialiser.__class__.__name__,
        )

    # --------------------------------------------------------------------------
    def unregister_serialiser(self):
        """
        This will unregister the serialiser. If the serialiser was set to 
        always serialise this option will be set back to False.
        
        :return: None 
        """
        self._serialiser = None
        self._always_serialise = False
        self._serialisation_identifier = ''

    # --------------------------------------------------------------------------
    def labels(self):
        return [
            item.label
            for item in self._items_to_record
        ]

    # --------------------------------------------------------------------------
    def count(self):
        """
        Returns how many states have currently been stored
        :return: 
        """
        return len(self._states)

    # --------------------------------------------------------------------------
    def group(self, other):
        """
        Occasionally you many want to instantiate multiple recollection objects
        but have them all store and restore in lock-step. This can be done
        by grouping recollection objects together. 
        
        :param other: The recollection object you want to put into lock-step  
            with this group.
            NOTE: If the 'other' group is already in lock-step with a third
            group then all three groups will go into lock-step together.
        :type other: memento.Memento 
        """
        # -- Cycle over the sync groups, if we find a sync group
        # -- which contains this recollection we add the other to the
        # -- same group
        for idx in range(len(Memento._SYNC_GROUPS)):
            if self in Memento._SYNC_GROUPS[idx]:
                if other not in Memento._SYNC_GROUPS[idx]:
                    Memento._SYNC_GROUPS[idx].append(other)
                return

        # -- To get here we need to define a new sync group
        Memento._SYNC_GROUPS.append(
            [
                self,
                other,
            ],
        )

        # -- Log the removal
        log.debug(
            '%s added to group along with : %s' % (
                self,
                self.sync_group(),
            )
        )

    # --------------------------------------------------------------------------
    def sync_group(self):
        """
        This will return all the members of the lock-step. If there is no
        grouping the recollection will be returning in its own list/group.
         
        :return: list(mement.Memento, ...) 
        """
        for group in Memento._SYNC_GROUPS:
            if self in group:
                return list(group)

        # -- If there is no group, we consider it to be alone
        # -- in its own group
        return [self]

    # --------------------------------------------------------------------------
    def serialise(self):
        """
        Providing a serialiser has been registered, this will intiate a 
        serialisation process - allowing this recollection's current state to 
        be stored in a persistent way. 
        """
        # -- If we have no serialiser but we are being requested
        # -- to serialise we raise an exception
        if not self._serialiser:
            raise Exception(
                'No serialiser has been defined for this recollection object',
            )

        # -- Ask the registered serialise to serialise our latest
        # -- state
        self._serialiser.serialise(
            self._states[0],
            self._serialisation_identifier,
        )

        # -- Log the removal
        log.debug('Serialised State on %s' % self)

    # --------------------------------------------------------------------------
    def deserialise(self):
        """
        This will initialise the target with the persistently stored
        state (if available). 
        """
        # -- If we have no serialiser but we are being requested
        # -- to serialise we raise an exception
        if not self._serialiser:
            raise Exception(
                'No serialiser has been defined for this recollection object',
            )

        # -- Get the data from the deserialisation process
        deserialisation = self._serialiser.deserialise(
            self._serialisation_identifier,
        )

        # -- Providing that process was successful we add the returned
        # -- state into recollection and restore to it
        if deserialisation:
            self._states.insert(0, deserialisation)
            self.restore(index=0)

        log.debug('Deserialised State to %s' % self)

    # --------------------------------------------------------------------------
    @staticmethod
    def serialise_after(memento_accessor):
        """
        This decorator will initialise a serialisation of the
        data store whenever this function is called. This is the
        equivalent of calling memento.store(serialise=True) at
        the end of the function - but decorating can make it a
        little clearer at-a-glance which functions cause a state
        serialisation

        This should only be applied to instance methods of classes as it
        is always assumed that the first argument is the instance of the
        class.

        In the following example we set up our memento object and define
        a serialiser, but rather than call the memento store from within the
        setter we simply decorate the function. This gives no functional
        difference, but makes it easier to see at a definition level which
        methods will incur a serialisation

        ..code-block:: python
            
            >>> from recollection import Memento, JsonAppSerialiser
            >>>
            >>> class UserPreferencesB(object):
            ...
            ...     def __init__(self):
            ...
            ...         # -- Visual preferences
            ...         self._theme = 'default'
            ...
            ...         # -- Define our memento, which we utilise specifically 
            ...         # -- to store our preferences to a persistent location
            ...         self._store = Memento(self)
            ...
            ...         # -- We will utilise the JSON Appdata serialiser, which
            ...         # -- writes our memento information to the app data 
            ...         # -- system
            ...         # -- location
            ...         self._store.register_serialiser(
            ...             serialiser=JsonAppSerialiser,
            ...             identifier='memento/demos/prefs/UserPreferenceA',
            ...         )
            ...
            ...         # -- Register which properties we want the store to 
            ...         # -- focus on
            ...         self._store.register('_theme')
            ...
            ...         # -- Finally, we deserialise - which will update this 
            ...         # -- class with any previously stored state
            ...         self._store.deserialise()
            ...
            ...     @property
            ...     def theme(self):
            ...         return self._theme
            ...
            ...     @theme.setter
            ...     @Memento.serialise_after('_store')
            ...     def theme(self, theme):
            ...         self._theme = theme

        :param memento_accessor: This is the attribute name on the class
            to access

        :return:
        """

        # ----------------------------------------------------------------------
        def serialise_after_inner(func):

            # ------------------------------------------------------------------
            def inner(*args, **kwargs):

                # -- Call the function
                result = func(*args, **kwargs)

                try:
                    getattr(
                        args[0],
                        memento_accessor,
                    ).store(serialise=True)

                except AttributeError:
                    log.warning(
                        'Could not store state after call to %s' % func,
                    )

                return result

            return inner

        return serialise_after_inner


# ------------------------------------------------------------------------------
class _SyncGroupPropogation(object):
    """
    This is an internal and private class which manages recusion around
    lock-step grouping. This ensures that a sequencial group of recollection's
    will not continually call one-another when performing a lock-step call.
    """

    _ACTIVELY_PROCESSING = list()

    # --------------------------------------------------------------------------
    def __init__(self, memento):
        self._memento = memento
        self._processing_in_context = list()

    # --------------------------------------------------------------------------
    def __enter__(self):

        # -- If our recollection instance is already being processes then
        # -- there is nothing more to do and we return an empty
        # -- list
        if self._memento in _SyncGroupPropogation._ACTIVELY_PROCESSING:
            return list()

        # -- Get a list of members to actively process
        self._processing_in_context = self._memento.sync_group()

        # -- Add in the list of things we need to process, to ensure
        # -- they will not get re-processed
        _SyncGroupPropogation._ACTIVELY_PROCESSING.extend(
            self._processing_in_context
        )

        # -- Return a list of all the recollection's apart from this one
        return [
            memento
            for memento in self._processing_in_context
            if memento != self._memento
        ]

    # --------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_val, exc_tb):
        # -- Now that we are done processing we need to remove any
        # -- instances out of the class list.
        while self._processing_in_context:
            self._ACTIVELY_PROCESSING.remove(
                self._processing_in_context.pop(),
            )


# ------------------------------------------------------------------------------
class _ItemToRecord(object):
    """
    This stores all the data required to be able to quickly and efficiently
    call or access data.
    """

    # --------------------------------------------------------------------------
    def __init__(self, target, label, getter, setter, copy_value):

        self.label = label

        self._target = target
        self._getter = getter
        self._setter = setter
        self._copy_value = copy_value

        self._label = self.label or getter

        self._get_is_callable = callable(self._getter)
        self._set_is_callable = callable(self._setter)

        if not isinstance(self.label, six.string_types):
            raise TypeError(
                'When giving a partial or method you must specify a '
                'label as it cannot be dynamically inferred'
            )

    # --------------------------------------------------------------------------
    def __repr__(self):
        return '[Unregistered %s, Getter: %s, Setter: %s]' % (
            self.label,
            self._getter,
            self._setter,
        )

    # --------------------------------------------------------------------------
    def _copy(self, item):
        if self._copy_value:
            return copy.deepcopy(item)
        return item

    # --------------------------------------------------------------------------
    def get(self):
        if self._get_is_callable:
            # -- We use a deepcopy to ensure that we're not storing
            # -- mutable values
            return self._copy(
                self._getter(),
            )

        else:
            # -- We use a deepcopy to ensure that we're not storing
            # -- mutable values
            return self._copy(
                getattr(
                    self._target(),
                    self._getter,
                ),
            )

    # --------------------------------------------------------------------------
    def set(self, *args, **kwargs):
        # -- If it s callable we call the method/function with the
        # -- value in the stored state as the argument
        if self._set_is_callable:
            self._setter(*args, **kwargs)

        # -- The setter is not callable, so we assume its a property
        # -- to be set directly
        else:
            setattr(
                self._target(),
                self.label,
                *args,
                **kwargs
            )
