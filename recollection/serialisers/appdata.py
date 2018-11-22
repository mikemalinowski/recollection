from ..serialiser import SerialiserBase

import os
import sys
import json


# ------------------------------------------------------------------------------
# -- OS System wrangling
_APPDATA_ROOT = None
if sys.platform == "win32":
    _APPDATA_ROOT = os.path.join(
        os.environ['APPDATA'],
        'recollection',
    )

elif sys.platform == "linux":
    _APPDATA_ROOT = os.path.join(
        os.path.expanduser('~'),
        'AppData',
        'recollection',
    )

else:
    raise NotImplementedError(
        'Support for %s is not yet implemented' % sys.platform
    )


# ------------------------------------------------------------------------------
class JsonAppSerialiser(SerialiserBase):
    """
    This will serialise the recollection object to a json file and store it in
    an application data location (varies depending on platform). You can
    utilise the identifier as a sub-path to create namespaced serialisation
    objects.

    For instance:
        serialiser.serialise(recollection, 'foo/bar'

    would (on windows) result in:
        %APPDATA%/recollection/foo/bar.json

    """

    # --------------------------------------------------------------------------
    @staticmethod
    def serialise(data, identifier):
        path = JsonAppSerialiser.locator(identifier)

        directory = os.path.dirname(path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as f:
            json.dump(
                data,
                f,
                indent=4,
                sort_keys=True,
            )

    # --------------------------------------------------------------------------
    @staticmethod
    def deserialise(identifier):
        path = JsonAppSerialiser.locator(identifier)

        if not os.path.exists(path):
            return None

        with open(path, 'r') as f:
            return json.load(f)

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
        parts = identifier.split('/')
        parts[-1] = parts[-1] + '.json'
        path = _APPDATA_ROOT

        while parts:
            path = os.path.join(
                path,
                parts.pop(0),
            )

        return path
