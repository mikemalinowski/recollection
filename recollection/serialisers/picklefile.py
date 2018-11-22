from ..serialiser import SerialiserBase

import os

try:
    # noinspection PyPep8Naming
    import cPickle as pickle

except ImportError:
    import pickle


# ------------------------------------------------------------------------------
class PickleSerialiser(SerialiserBase):
    """
    This will serialise the memento object to a json file and store it in
    an application data location (varies depending on platform). You can
    utilise the identifier as a sub-path to create namespaced serialisation
    objects.

    For instance:
        serialiser.serialise(memento, 'foo/bar'

    would (on windows) result in:
        %APPDATA%/memento/foo/bar.json

    """

    # --------------------------------------------------------------------------
    @staticmethod
    def serialise(data, identifier):
        """
        The identifier for this serialiser should be the absolute path
        to the file you want to write to
        
        :param data: dict
        :param identifier: str
         
        :return: 
        """
        directory = os.path.dirname(identifier)

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(identifier, 'wb') as f:
            pickle.dump(
                data,
                f,
            )

    # --------------------------------------------------------------------------
    @staticmethod
    def deserialise(identifier):
        """
        The identifier for this serialiser should be the absolute path
        to the file you want to write to

        :param identifier: str
         
        :return: 
        """
        if not os.path.exists(identifier):
            return None

        with open(identifier, 'rb') as f:
            return pickle.load(f)

    # --------------------------------------------------------------------------
    @staticmethod
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
        return identifier
