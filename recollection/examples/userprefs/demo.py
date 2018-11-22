import random
import recollection


# ------------------------------------------------------------------------------
def demo():
    """
    This demo creates a preferences class which calls the store on
    the setters for the properties we want to store. It then instances
    a second class to check that the preferences were deserialised
    correctly.

    :return:
    """
    # -- Instance our user prefs
    pref_a = UserPreferencesA()

    # -- Set a preference
    new_theme = random.choice(UserPreferencesA.THEMES)
    pref_a.theme = new_theme

    # -- Now lets create another instance of the same preferences
    # -- and check that the preference was both stored and restored
    pref_a_2 = UserPreferencesA()

    print(
        'User Preferences are : %s, expected was : %s' % (
            pref_a_2.theme,
            new_theme,
        )
    )


# ------------------------------------------------------------------------------
def demo2():
    """
    This demo creates a preferences class which is decorated on the
    setters to perform a serialisation on call. It then instances
    a second class to check that the preferences were deserialised
    correctly.

    :return:
    """
    # -- Instance our user prefs
    pref_a = UserPreferencesB()

    # -- Set a preference
    new_theme = random.choice(UserPreferencesB.THEMES)
    pref_a.theme = new_theme

    # -- Now lets create another instance of the same preferences
    # -- and check that the preference was both stored and restored
    pref_a_2 = UserPreferencesB()

    print(
        'User Preferences are : %s, expected was : %s' % (
            pref_a_2.theme,
            new_theme,
        )
    )


# ------------------------------------------------------------------------------
class UserPreferencesA(object):
    """
    This is some hypothetical user preferences for a piece of
    novel writing software.

    In this particular example we expose our preferences through
    getter and setter methods and ask our memento to store during
    the setting
    """

    THEMES = [
        'Red',
        'Green',
        'Blue',
        'Orange',
        'Tropical',
        'Ice',
        'Fire',
        'Scary',
    ]

    # --------------------------------------------------------------------------
    def __init__(self):

        # -- Visual preferences
        self._theme = 'default'
        self._show_spelling_errors = True

        # -- Save/loading preferences
        self._save_on_close = True
        self._load_last_project = True

        # -- Define our memento, which we utilise specifically to
        # -- store our preferences to a persistent location
        self._store = recollection.Memento(self)

        # -- We will utilise the JSON Appdata serialiser, which
        # -- writes our memento information to the app data system
        # -- location
        self._store.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/demos/userprefs/UserPreferenceA',
        )

        # -- Register which properties we want the store to focus on
        self._store.register(
            [
                '_theme',
                '_save_on_close',
                '_load_last_project',
                '_show_spelling_errors',
            ],
        )

        # -- Finally, we deserialise - which will update this class with
        # -- any previously stored state
        self._store.deserialise()

    # --------------------------------------------------------------------------
    @property
    def theme(self):
        return self._theme

    # --------------------------------------------------------------------------
    @theme.setter
    def theme(self, theme):
        self._theme = theme
        self._store.store(serialise=True)

    # --------------------------------------------------------------------------
    @property
    def show_spelling_errors(self):
        return self._show_spelling_errors

    # --------------------------------------------------------------------------
    @show_spelling_errors.setter
    def show_spelling_errors(self, value):
        self._show_spelling_errors = value
        self._store.store(serialise=True)

    # --------------------------------------------------------------------------
    @property
    def save_on_close(self):
        return self._save_on_close

    # --------------------------------------------------------------------------
    @save_on_close.setter
    def save_on_close(self, value):
        self._save_on_close = value
        self._store.store(serialise=True)

    # --------------------------------------------------------------------------
    @property
    def load_last_project(self):
        return self._load_last_project

    # --------------------------------------------------------------------------
    @load_last_project.setter
    def load_last_project(self, value):
        self._load_last_project = value
        self._store.store(serialise=True)


# ------------------------------------------------------------------------------
class UserPreferencesB(object):
    """
    This is some hypothetical user preferences for a piece of
    novel writing software.

    In this particular example we expose our preferences through
    getter and setter methods and ask our memento to store during
    the setting
    """

    THEMES = [
        'Red',
        'Green',
        'Blue',
        'Orange',
        'Tropical',
        'Ice',
        'Fire',
        'Scary',
    ]

    # --------------------------------------------------------------------------
    def __init__(self):

        # -- Visual preferences
        self._theme = 'default'
        self._show_spelling_errors = True

        # -- Save/loading preferences
        self._save_on_close = True
        self._load_last_project = True

        # -- Define our memento, which we utilise specifically to
        # -- store our preferences to a persistent location
        self._store = recollection.Memento(self)

        # -- We will utilise the JSON Appdata serialiser, which
        # -- writes our memento information to the app data system
        # -- location
        self._store.register_serialiser(
            serialiser=recollection.JsonAppSerialiser,
            identifier='memento/demos/userprefs/UserPreferenceA',
        )

        # -- Register which properties we want the store to focus on
        self._store.register(
            [
                '_theme',
                '_save_on_close',
                '_load_last_project',
                '_show_spelling_errors',
            ],
        )

        # -- Finally, we deserialise - which will update this class with
        # -- any previously stored state
        self._store.deserialise()

    # --------------------------------------------------------------------------
    @property
    def theme(self):
        return self._theme

    # --------------------------------------------------------------------------
    @theme.setter
    @recollection.Memento.serialise_after('_store')
    def theme(self, theme):
        self._theme = theme

    # --------------------------------------------------------------------------
    @property
    def show_spelling_errors(self):
        return self._show_spelling_errors

    # --------------------------------------------------------------------------
    @show_spelling_errors.setter
    @recollection.Memento.serialise_after('_store')
    def show_spelling_errors(self, value):
        self._show_spelling_errors = value

    # --------------------------------------------------------------------------
    @property
    def save_on_close(self):
        return self._save_on_close

    # --------------------------------------------------------------------------
    @save_on_close.setter
    @recollection.Memento.serialise_after('_store')
    def save_on_close(self, value):
        self._save_on_close = value

    # --------------------------------------------------------------------------
    @property
    def load_last_project(self):
        return self._load_last_project

    # --------------------------------------------------------------------------
    @load_last_project.setter
    @recollection.Memento.serialise_after('_store')
    def load_last_project(self, value):
        self._load_last_project = value


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    demo()
    demo2()
