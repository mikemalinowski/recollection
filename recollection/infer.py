"""
This namespace holds Inference decorators.
"""
from .inference import Inference


# --------------------------------------------------------------------------
def get(label):
    """
    This is an inference decorator which can be used to decorate
    a getter method.

    ..code-block:: python
        
        >>> import recollection
        >>>
        >>> class Foo(recollection.Inference):
        ... 
        ...     def __init__(self):
        ...         super(Foo, self).__init__()
        ... 
        ...         # -- Demonstrate a private attribute with getter
        ...         # -- and setter methods
        ...         self._letter = 1
        ... 
        ...     # -- Declare that this is a memento getter
        ...     @recollection.infer.get('foobar')
        ...     def get_letter(self):
        ...         return self._letter

    :param label: You must specify a label to be used when storing
        this variable. For the registration to be processed there 
        must be a correlating setter defined on the class with the same
        label.
    :type label: str

    :return: 
    """
    def inner_decor(func):
        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        # -- Assign our attributes
        inner.label = label
        inner.is_memento_getter = True
        inner.is_memento_setter = False

        return inner

    return inner_decor


# --------------------------------------------------------------------------
def store(label, copy_value=True, serialise=False):
    """
    This is an inference decorator which can be used to decorate
    a getter method.

    ..code-block:: python
        
        >>> import recollection
        >>> 
        >>> class Foo(recollection.Inference):
        ... 
        ...     def __init__(self):
        ...         super(Foo, self).__init__()
        ... 
        ...         # -- Demonstrate a private attribute with getter
        ...         # -- and setter methods
        ...         self._letter = 1
        ... 
        ...     # -- Declare that this is a memento getter
        ...     @recollection.infer.store('letter', serialise=True)
        ...     def set_letter(self):
        ...         return self._letter
        >>> foo = Foo()
        
    :param label: You must specify a label to be used when storing
        this variable. For the registration to be processed there 
        must be a correlating setter defined on the class with the same
        label.
    :type label: str

    :param copy_value: Default is True, this defines whether the object
        being stored will be copied or referenced. Typically if this is
        likely to be left to True, however if you want a reference to an 
        object to be stored in history rather than copies of the object you
        should set this to False.
    :type copy_value: bool

    :param serialise: If true this will perform a serialisation of the 
        memento object each time the setter is called. This expects a
        serialiser to be registered. The default is False.
    :type serialise: bool

    :return: 
    """

    def inner_decor(func):
        def inner(*args, **kwargs):
            result = func(*args, **kwargs)

            # -- Now store
            if isinstance(args[0], Inference):
                args[0].memento.store(serialise=serialise)

            return result

        # -- Assign our attributes
        inner.label = label
        inner.is_memento_getter = False
        inner.is_memento_setter = True
        inner.copy_value = copy_value

        return inner

    return inner_decor
