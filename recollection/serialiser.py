import abc
import six


# ------------------------------------------------------------------------------
@six.add_metaclass(abc.ABCMeta)
class SerialiserBase(object):
    """
    A serialiser is responsible for serialising the state of a momento
    object in such a way that it can easily be restored from the state
    of persistence.

    Note: Different serialisers have different levels of support for
    different datatypes. Therefore please read the docstrings of the
    serialisers when deciding which serialiser you want to utilise.
    """

    # --------------------------------------------------------------------------
    @staticmethod
    @abc.abstractmethod
    def serialise(data, identifier):
        """
        Attempts to serialise the given memento using the identifier
        variable to determine where the serialisation artifact should
        be stored.

        :param data: This is a dictionary snapshot from a memento stack
        :type data: dict

        :param identifier: This is very dependent on the requirements of
            each individual serialiser. This could be a filepath, a url,
            a name etc.
        :type identifier: str

        :return: True if the serialisation was successful
        """
        pass

    # --------------------------------------------------------------------------
    @staticmethod
    @abc.abstractmethod
    def deserialise(identifier):
        """
        Sets the state of the memento object based on the serialised data

        :param identifier: This is very dependent on the requirements of
            each individual serialiser. This could be a filepath, a url,
            a name etc.
        :type identifier: str

        :return: Dictionary which can be inserted into a memento stack
        """
        pass

    # --------------------------------------------------------------------------
    @staticmethod
    @abc.abstractmethod
    def locator(identifier):
        """
        With the given identifier this should return the resolved location
        of the data

        :param identifier: This is very dependent on the requirements of
            each individual serialiser. This could be a filepath, a url,
            a name etc.
        :type identifier: str

        :return: str
        """
        pass
