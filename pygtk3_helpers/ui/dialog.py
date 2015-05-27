import collections
from gi.repository import Gtk


def add_filters(dialog, filters):
    for f in filters:
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


def yesno(message, title=None):
    if title is None:
        title = message
        message = None

    dialog = Gtk.Dialog(title, None, 0,
                        (Gtk.STOCK_NO, Gtk.ResponseType.NO,
                         Gtk.STOCK_YES, Gtk.ResponseType.YES))

    if message is not None:
        label = Gtk.Label(message)
        box = dialog.get_content_area()
        hbox = Gtk.HBox()
        hbox.pack_start(label, False, False, 10)
        box.pack_start(hbox, False, False, 10)
        box.show_all()
    dialog.set_size_request(150, 50)

    response = dialog.run()
    dialog.destroy()
    return response
