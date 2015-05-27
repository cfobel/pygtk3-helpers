import os

from gi.repository import Gtk
from path_helpers import path
from ipython_helpers.notebook import SessionManager
from ..delegates import SlaveView
from .dialog import yesno, add_filters


class NotebookManagerView(SlaveView):
    def __init__(self, notebook_dir=None):
        super(NotebookManagerView, self).__init__()
        if notebook_dir is None:
            notebook_dir = os.getcwd()
        self.notebook_dir = path(notebook_dir).abspath()
        self.notebook_manager = SessionManager()

    def create_ui(self):
        box = Gtk.Box(spacing=6)
        box.set_orientation(Gtk.Orientation.HORIZONTAL)

        new_button = Gtk.Button('New...')
        open_button = Gtk.Button('Open...')
        new_button.connect('clicked', self.on_new)
        open_button.connect('clicked', self.on_open)
        new_button.show()
        open_button.show()

        box.pack_end(new_button, False, False, 0)
        box.pack_end(open_button, False, False, 0)
        self.widget.pack_start(box, False, False, 0)

        self.parent = None
        parent = self.widget.get_parent()
        while parent is not None:
            self.parent = parent
            parent = parent.get_parent()

    def on_open(self, button):
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                   Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog = Gtk.FileChooserDialog("Open notebook", self.parent,
                                       Gtk.FileChooserAction.OPEN, buttons)
        add_filters(dialog, [{'name': 'IPython notebook (*.ipynb)',
                              'pattern': '*.ipynb'}])
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_path = dialog.get_filename()
            self.notebook_manager.open(selected_path)
        dialog.destroy()

    def on_new(self, button):
        '''
        Copy selected notebook template to notebook directory.

        ## Notes ##

         - An exception is raised if the parent of the selected file is the
           notebook directory.
         - If notebook with same name already exists in notebook directory,
           offer is made to overwrite (the new copy of the file is renamed with
           a count if overwrite is not selected).
        '''
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                   Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog = Gtk.FileChooserDialog("Select notebook template", self.parent,
                                       Gtk.FileChooserAction.OPEN, buttons)
        add_filters(dialog, [{'name': 'IPython notebook (*.ipynb)',
                              'pattern': '*.ipynb'}])
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_path = path(dialog.get_filename())
            output_path = self.notebook_dir.joinpath(selected_path.name)

            overwrite = False
            if output_path.isfile():
                response = yesno('%s already exists. Overwrite?' % output_path.name,
                                 'Overwrite?')
                if response == Gtk.ResponseType.YES:
                    overwrite = True
                else:
                    counter = 1
                    renamed_path = output_path
                    while renamed_path.isfile():
                        new_name = '%s (%d)%s' % (output_path.namebase, counter,
                                                  output_path.ext)
                        renamed_path = output_path.parent.joinpath(new_name)
                        counter += 1
                    output_path = renamed_path
            self.notebook_manager.launch_from_template(selected_path,
                                                       overwrite=overwrite,
                                                       output_name=output_path.name,
                                                       notebook_dir=self.notebook_dir)
        dialog.destroy()
