"""
This example demonstrates a scenario where you have a functional class which
carries out a process along with an accompanying interface (impletemented using
PySide2).

The Renamer class utilises recollection.Inference in order to automatically
store any property changes, allowing its state to be retained between sessions.

The choice for putting the recollection code in the Renamer rather than the
UI is a choice of implementation (putting it in the UI would be equally
valid). For this scenario the choice of putting it in the Renamer was to show
how you could easily get state persistent across different interfaces if you 
were to present the same renamer class in different ways based on the intended
user.
"""
from functools import partial

import os
import recollection


# -- We wrap the pyside import in a try except only
# -- because we have no direct dependency on this module
# -- outside of this example.
try:
    from PySide2 import QtWidgets

except ImportError:
    print('You must have PySide2 in order to run this example')


# ------------------------------------------------------------------------------
class FileRenamer(recollection.Inference):
    """
    This is a small renamer class. You can set the properties on the class 
    and call 'run' to invoke a renaming process. 
    
    Any settings you define will automatically be restored the next time
    you instance the object. 
    """
    # --------------------------------------------------------------------------
    def __init__(self):
        super(FileRenamer, self).__init__()

        # -- Input properties
        self.directory = ''
        self.suffix_filter = ''
        self.replace_this = ''
        self.replace_with = ''
        self.skip_readonly = True

        # -- Output properties
        self.time_taken = 0
        self.processed = list()
        self.failed = list()

        # -- This final block of code in the init is all that
        # -- is required to get persistent data serialisation
        # -- working. Because we choose to do this in the pure-code
        # -- class, every UI we make for it will automatically
        # -- benefit from persistent state functionality.
        self.memento.register(
            [
                'directory',
                'suffix_filter',
                'replace_this',
                'replace_with',
                'skip_readonly',
                'time_taken',
                'processed',
                'failed',
            ]
        )

        self.memento.register_serialiser(
            recollection.JsonAppSerialiser,
            'memento/examples/renamer',
            always_serialise=True,
        )
        self.memento.deserialise()

    # --------------------------------------------------------------------------
    def run(self):
        target_list = list()

        # -- Get a list of all the files we think we need
        # -- to operate one
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:

                # -- If we have a suffix test, validate that and skip
                # -- if it does not match
                if self.suffix_filter and self.suffix_filter not in filename:
                    continue

                # -- Check if this has a substring we need to replace, if
                # -- not we skip over it
                if self.replace_this not in filename:
                    continue

                target_list.append(
                    os.path.join(
                        root,
                        filename,
                    )
                )

        # -- Now we can operate on all the files and update the
        # -- log. Because we will be editing properties we have
        # -- asked recollection to watch, we ask it to defer its
        # -- store call until its complete.
        with self.memento.defer():
            # -- Clear the process list
            self.processed = list()
            self.failed = list()

            # -- Get a full path to the file
            for current_path in target_list:

                # -- There are a lot of things that can go wrong
                # -- during a rename, so wrap this in a try
                try:

                    # -- Define our new location
                    new_path = os.path.join(
                        os.path.dirname(current_path),
                        os.path.basename(current_path).replace(
                            self.replace_this,
                            self.replace_with,
                        ),
                    )

                    os.rename(
                        current_path,
                        new_path,
                    )

                    # -- Mark the fact that we processed this file
                    # -- successfully
                    self.processed.append(
                        '%s -> %s' % (
                            current_path,
                            new_path,
                        )
                    )

                except:
                    # -- Something went wrong, so log the fact that we
                    # -- did not rename this file
                    self.failed.append(
                        '%s could not be renamed' % current_path,
                    )


# ------------------------------------------------------------------------------
class FileRenamerUi(QtWidgets.QWidget):
    """
    This is the Ui element of the renamer. The Ui instances the Renamer object
    and then pushes any input from the user onto the renamer itself. 
    
    The Ui element does not store any information itself, instead it has 
    functionality to set its ui state based on the state of the renamer
    properties along with a mechanism to push any ui-triggered values into
    the renamer.
    
    By taking this approach the recollection of data is all handled in the
    Renamer class directly, and therefore exposes the ability to have multiple
    different interfaces aimed at different users without having to reimplement
    the storage mechanisms in each one.
    """
    # --------------------------------------------------------------------------
    def __init__(self, parent=None):
        super(FileRenamerUi, self).__init__(parent=parent)

        # -- Instance the renamer object
        self.renamer = FileRenamer()

        # -- Define our maine layout
        self.setLayout(QtWidgets.QVBoxLayout())

        # -- Create the directory layout
        self.directory_field = QtWidgets.QLineEdit()
        self.browser_button = QtWidgets.QPushButton('...')

        # -- Add the directory-centric widgets into this layout
        directory_layout = QtWidgets.QHBoxLayout()
        directory_layout.addWidget(self.directory_field)
        directory_layout.addWidget(self.browser_button)
        self.layout().addLayout(directory_layout)

        # -- Add the options
        options_group = QtWidgets.QGroupBox('Options')
        options_layout = QtWidgets.QVBoxLayout()
        options_group.setLayout(options_layout)
        self.layout().addWidget(options_group)

        # -- Utilise a private function which will handle the creation
        # -- of the layout and widget (and bind them together)
        layout_a, self.suffix_filter = self._labelled_lineedit('Suffix Filter')
        layout_b, self.replace_this = self._labelled_lineedit('Replace This')
        layout_c, self.with_this = self._labelled_lineedit('With This')

        options_layout.addLayout(layout_a)
        options_layout.addLayout(layout_b)
        options_layout.addLayout(layout_c)

        # -- Add our log output - which will show the results of the
        # -- process runner
        self.log_output = QtWidgets.QListWidget()
        self.layout().addWidget(self.log_output)

        # -- Add the button which will ultimately trigger the
        # -- processing
        self.run_button = QtWidgets.QPushButton('Process')
        self.layout().addWidget(self.run_button)

        # -- Update the Ui based on the renamer state. We do this becase
        # -- the Renamer class is able to utilise recollection to initialise
        # -- its state from its last run
        self.update_ui()

        # -- Ensure we update the ui whenever the renamer
        # -- is dynamically changed
        self.renamer.memento.stored.connect(
            self.update_ui,
        )

        # -- Hook up signals and slots for the buttons
        self.run_button.clicked.connect(self.renamer.run)
        self.browser_button.clicked.connect(self._set_directory)

        # -- Finally we hook up the events on our text fields so
        # -- the renamer object will recieve the users input
        # -- values
        text_propogation_widgets = dict(
            directory=self.directory_field,
            suffix_filter=self.suffix_filter,
            replace_this=self.replace_this,
            replace_with=self.with_this,
        )

        for label, text_widget in text_propogation_widgets.items():
            text_widget.textChanged.connect(
                partial(
                    self._push_change_to_renamer,
                    label,
                )
            )

        # -- Private variable to testing whether we actually need
        # -- to be propogating changes to the Renamer
        self._enable_propogation = True

    # --------------------------------------------------------------------------
    def _push_change_to_renamer(self, label, value):
        """
        This method pushes any text changes over to the renamer 
        object - allowing that object to carry out any recollection
        calls.
        
        :param label: The property name on the renamer to set 
        :param value: The value to set the property to
        
        :return: None 
        """
        setattr(
            self.renamer,
            label,
            value,
        )

    # --------------------------------------------------------------------------
    def _labelled_lineedit(self, label):
        """
        This is a layout setup method which makes it a little easier to 
        create a text field which a label in front of it.
        
        :param label: The text the label should show
         
        :return: QHBoxLayout, QLineEdit 
        """
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(label))
        lineedit = QtWidgets.QLineEdit()
        layout.addWidget(lineedit)

        return layout, lineedit

    # --------------------------------------------------------------------------
    def _set_directory(self, directory=None):
        """
        Triggered whenever the user clicks the '...' button to select a 
        target directory. 
        :param directory: 
        :return: 
        """

        # -- If no directory is given we prompt for one
        if directory is None or directory is False:
            directory = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                'Select directory to search from',
            )

        # -- If we still have no valid directory we exit
        if directory is None:
            return

        self.directory_field.setText(
            directory,
        )

    # --------------------------------------------------------------------------
    def update_ui(self):
        """
        This will read the data from the renamer and update the ui.
        
        :return: 
        """
        try:
            # -- We do not want to push changes back to the renamer
            # -- while we're updating our changes based on the renamers
            # -- current state, therefore we temporarily disable any
            # -- data propagation
            self._enable_propogation = False

            # -- Set our text fields
            self.with_this.setText(self.renamer.replace_with)
            self.replace_this.setText(self.renamer.replace_this)
            self.directory_field.setText(self.renamer.directory)
            self.suffix_filter.setText(self.renamer.suffix_filter)

            # -- Update our output log. Clear any previous results
            # -- then populate it based on the last run.
            self.log_output.clear()
            for success in self.renamer.processed:
                self.log_output.addItem(success)

            for failure in self.renamer.failed:
                self.log_output.addItem(failure)

        finally:
            # -- Now all our changes are complete we can turn data
            # -- propogation back on.
            self._enable_propogation = True


# ------------------------------------------------------------------------------
def demo():

    if not QtWidgets.QApplication.instance():
        QtWidgets.QApplication([])

    q_app = QtWidgets.QApplication.instance()
    widget = FileRenamerUi()
    widget.show()

    q_app.exec_()
