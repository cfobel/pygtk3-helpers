# -*- coding: utf-8 -*-

"""
    pygtkhelpers.delegates
    ~~~~~~~~~~~~~~~~~~~~~~

    Delegates, which combine some UI, some signals, some signal handlers, and
    some properties,

    :copyright: 2009-2010 by pygtkhelpers Authors
    :license: LGPL2 or later
"""
import os

import gi
from gi.repository import GObject, Gtk
import pkg_resources


def get_first_builder_window(builder):
    """Get the first toplevel widget in a Gtk.Builder hierarchy.

    This is mostly used for guessing purposes, and an explicit naming is
    always going to be a better situation.
    """
    for obj in builder.get_objects():
        if isinstance(obj, Gtk.Window):
            # first window
            return obj


class BaseDelegate(object):
    """Base delegate functionality.

    This is abstract.

    It uses hand-created, and Gtk.Builder created ui's, and combinations of the
    two, and is responsible for automatically loading ui files from resources,
    and connecting signals.

    Additionally, it is a GObject.GObject subclass, and so can be used with the
    gsignal, and gproperty functions from pygtkhelpers.utils in order to add
    property and signal functionality.

    The abstract elements of this class are:

        1. The way it gets a toplevel widget from a ui file
        2. How it creates a default toplevel widget if one was not found in the
           ui file, or no ui file is specified.
    """

    builder_file = None
    builder_path = None
    toplevel_name = 'main'
    builder_file_patterns = [
        #this should be the default
        'ui/%s.ui',
        'ui/%s',
        # commonly used in applications like for example pida
        'glade/%s.glade',
        'glade/%s',
    ]

    def __init__(self, model=None):
        self._props = {}
        self._toplevel = None
        self.slaves = []
        self.widget = None
        self._model = model
        self._ui_ready = False

    def prepare_ui(self):
        self._load_builder()
        if self._toplevel is None:
            self._toplevel = self.create_default_toplevel()
        self.widget = self._toplevel
        self.create_ui()
        self._connect_signals()
        self._ui_ready = True

    # Public API
    def get_builder_toplevel(self, builder):
        """Get the toplevel widget from a Gtk.Builder file.
        """
        raise NotImplementedError

    def create_default_toplevel(self):
        raise NotImplementedError

    def create_ui(self):
        """Create any UI by hand.

        Override to create additional UI here.

        This can contain any instance initialization, so for example mutation of
        the Gtk.Builder generated UI, or creating the UI in its entirety.
        """

    def model_set(self):
        """This method is called when the model is changed
        """

    def add_slave(self, slave, container_name="widget"):
        """Add a slave delegate
        """
        cont = getattr(self, container_name, None)
        if cont is None:
            raise AttributeError(
                'Container name must be a member of the delegate')
        cont.add(slave.widget)
        self.slaves.append(slave)
        return slave

    def show(self):
        """Call show_all on the toplevel widget"""
        if not self._ui_ready:
            self.prepare_ui()
        self.widget.show_all()

    def hide(self):
        """Call hide on the toplevel widget"""
        self.widget.hide()

    def show_and_run(self):
        """Show the main widget and run the gtk loop"""
        self.show()
        Gtk.main()

    def hide_and_quit(self):
        """Hide the widget and quit the main loop"""
        self.hide()
        Gtk.main_quit()

    def _load_builder(self):
        builder = Gtk.Builder()
        self.__builder = builder
        if self.builder_path:
            if not os.path.exists(self.builder_path):
                raise LookupError(self.__class__, self.builder_path)
            builder.add_from_file(self.builder_path)
        elif self.builder_file:
            #XXX: more sensible selection!!
            data = None
            for type_ in self.__class__.__mro__:
                for pattern in self.builder_file_patterns:
                    file_ = pattern % self.builder_file
                    try:
                        data = pkg_resources.resource_filename(type_
                                                               .__module__,
                                                               file_)
                        break
                    except (IOError, ImportError):
                        continue
                if data:
                    break
            if not data: #XXX: better debugging of the causes?
                raise LookupError(self.__class__, self.builder_file)

            builder.add_from_string(data)
        else:
            return
        self._toplevel = self.get_builder_toplevel(builder)
        for obj in builder.get_objects():
            try:
                obj_name = Gtk.Buildable.get_name(obj)
            except TypeError:
                pass #XXX: maybe warn?
            else:
                setattr(self, obj_name, obj)

    def _connect_signals(self):
        for name in self._get_all_handlers():
            self._connect_signal(name)
        self.__builder.connect_signals(self)

    def _parse_signal_handler(self, name):
        signal_type, widget_signal = name.split('_', 1)
        widget_name, signal_name = widget_signal.split('__')
        return signal_type, widget_name, signal_name

    def _connect_signal(self, name):
        method = getattr(self, name)
        signal_type, widget_name, signal_name = self._parse_signal_handler(name)
        widget = getattr(self, widget_name, None)
        if widget is None:
            raise LookupError('Widget named %s is not available.'%widget_name )
        if signal_type == 'on':
            widget.connect(signal_name, method)
        elif signal_type == 'after':
            widget.connect_after(signal_name, method)

    def _get_all_handlers(self):
        for name in dir(self):
            if ((name.startswith('on_') or
                    name.startswith('after_')) and
                    '__' in  name):
                yield name

    def _get_prop_handler(self, propname, action):
        return getattr(self, '%s_property_%s' % (action, propname), None)

    def set_model(self, model):
        self._model = model
        self.model_set()
        self.emit('model-set')

    def get_model(self):
        return self._model

    model = property(get_model, set_model)

    # Private glib API for simple property handling
    def do_get_property(self, prop):
        call = self._get_prop_handler(prop.name, 'get')
        if call is not None:
            return call()
        else:
            return self._props.get(prop.name, prop.default_value)

    def do_set_property(self, prop, value):
        call = self._get_prop_handler(prop.name, 'set')
        if call is not None:
            call(value)
        else:
            self._props[prop.name] = value


class SlaveView(BaseDelegate):
    """A View that is a slave"""

    def get_builder_toplevel(self, builder):
        """Get the toplevel widget from a Gtk.Builder file.

        The slave view implementation first searches for the widget named as
        self.toplevel_name (which defaults to "main". If this is missing, the
        first toplevel widget is discovered in the Builder file, and it's
        immediate child is used as the toplevel widget for the delegate.
        """
        toplevel = builder.get_object(self.toplevel_name)
        if toplevel is None:
            toplevel = get_first_builder_window(builder).child
        if toplevel is not None:
            #XXX: what to do if a developer
            #     gave the name of a window instead of its child
            toplevel.get_parent().remove(toplevel)
        return toplevel

    def create_default_toplevel(self):
        return Gtk.VBox()

    def show_and_run(self):
        """Show the main widget in a window and run the gtk loop"""
        if not self._ui_ready:
            self.prepare_ui()
        self.display_widget = Gtk.Window()
        self.display_widget.add(self.widget)
        self.display_widget.show()
        self.display_widget.connect('destroy', lambda *args: self.hide_and_quit())
        BaseDelegate.show_and_run(self)


class ToplevelView(BaseDelegate):
    """A View that is a toplevel widget"""

    def get_builder_toplevel(self, builder):
        """Get the toplevel widget from a Gtk.Builder file.

        The main view implementation first searches for the widget named as
        self.toplevel_name (which defaults to "main". If this is missing, or not
        a Gtk.Window, the first toplevel window found in the Gtk.Builder is
        used.
        """
        toplevel = builder.get_object(self.toplevel_name)
        if not GObject.type_is_a(toplevel, Gtk.Window):
            toplevel = None
        if toplevel is None:
            toplevel = get_first_builder_window(builder)
        return toplevel

    def create_default_toplevel(self):
        return Gtk.Window()


class WindowView(ToplevelView):
    """A View that is a Window"""
    def set_title(self, title):
        self.widget.set_title(title)
