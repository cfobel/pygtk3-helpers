import collections
from gi.repository import Gtk
from delegates import SlaveView


class FileChooserView(SlaveView):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.action = kwargs.pop('action', Gtk.FileChooserAction.OPEN)
        self.confirm_overwrite = kwargs.pop('confirm_overwrite', True)
        file_buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        folder_buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 'Select',
                          Gtk.ResponseType.OK)
        if self.action == Gtk.FileChooserAction.SELECT_FOLDER:
            buttons = folder_buttons
            type_str = 'folder'
        else:
            buttons = file_buttons
            type_str = 'file'
        self.buttons = kwargs.pop('buttons', buttons)
        self.label = kwargs.pop('label', True)
        self.editable = kwargs.pop('editable', True)
        self.filters = kwargs.pop('filters', [{'name': 'Any', 'pattern': '*'}])
        self.title = kwargs.pop('title', 'Please choose a %s' % type_str)
        self.kwargs = kwargs
        self._selected_path = None
        super(FileChooserView, self).__init__(self, *args, **kwargs)

    def create_ui(self):
        self.box = Gtk.Box(spacing=6)

        if self.label:
            if self.editable:
                self.label = Gtk.Entry()
            else:
                self.label = Gtk.Label()
            self.box.pack_start(self.label, True, True, 0)

        button = Gtk.Button('Browse...')
        if self.action == Gtk.FileChooserAction.SELECT_FOLDER:
            callback = self.on_folder_clicked
        else:
            callback = self.on_file_clicked
        button.connect('clicked', callback)
        self.box.pack_start(button, False, False, 0)

        self.widget.pack_start(self.box, False, False, 0)
        self.parent = None
        parent = self.widget.get_parent()
        while parent is not None:
            self.parent = parent
            parent = parent.get_parent()

    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(self.title, self.parent, self.action,
                                       self.buttons)
        dialog.set_do_overwrite_confirmation(self.confirm_overwrite)

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_path = dialog.get_filename()
            self.on_selected(self.selected_path)

        dialog.destroy()

    def on_selected(self, value):
        pass

    def add_filters(self, dialog):
        for f in self.filters:
            filter_text = Gtk.FileFilter()
            filter_text.set_name(f['name'])
            if 'mime_type' in f:
                mime_types = f['mime_type']
                if not isinstance(mime_types, collections.Iterable):
                    mime_types = [mime_types]
                for mime_type in mime_types:
                    filter_text.add_mime_type(mime_type)
            elif 'pattern' in f:
                patterns = f['pattern']
                if not isinstance(patterns, collections.Iterable):
                    patterns = [patterns]
                for pattern in patterns:
                    filter_text.add_pattern(pattern)
            dialog.add_filter(filter_text)

    def on_folder_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(self.title, self.parent,
                                       self.action, self.buttons)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_path = dialog.get_filename()
            self.on_selected(self.selected_path)

        dialog.destroy()

    @property
    def selected_path(self):
        if self.label:
            return self.label.get_text()
        else:
            return self._selected_path

    @selected_path.setter
    def selected_path(self, value):
        if self.label:
            self.label.set_text(value)
        else:
            self._selected_path = value
