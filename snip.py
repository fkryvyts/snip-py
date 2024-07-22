import gi
import os

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk, GLib

class PreviewEditor(Gtk.DrawingArea):
    def __init__(self, preview):
        super().__init__()
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)

        self.cleanup()
        self.preview = preview
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        self.connect("button-press-event", self.on_button_press_event)
        self.connect("motion-notify-event", self.on_motion_notify_event)
        self.connect("button-release-event", self.on_button_release_event)
        self.connect("draw", self.on_draw)

    def on_button_press_event(self, widget, event):
        if event.button == Gdk.BUTTON_PRIMARY:
            self.start_x = event.x
            self.start_y = event.y
            self.end_x = event.x
            self.end_y = event.y
            self.started = True
    
    def on_motion_notify_event(self, widget, event):
        if self.started:
            self.end_x = event.x
            self.end_y = event.y
            self.queue_draw()

    def on_button_release_event(self, widget, event):
        if self.started:
            cropped_pixbuf = self.pixbuf.new_subpixbuf(min(self.start_x, self.end_x), min(self.start_y, self.end_y), abs(self.end_x - self.start_x), abs(self.end_y - self.start_y))
            self.clipboard.set_image(cropped_pixbuf)
            print("copied to clipboard")
            # cropped_pixbuf.savev("/path/to/screenshot.png","png", (), ())

            self.cleanup()
            self.preview.hide()

    def cleanup(self):
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.pixbuf = None
        self.started = False

    def set_preview(self, pb):
        self.pixbuf = pb

    def on_draw(self, widget, context):
        if self.pixbuf != None:
            Gdk.cairo_set_source_pixbuf(context, self.pixbuf, 0, 0)
            context.paint()
        
        if self.started:
            context.set_source_rgba(0.11, 0.11, 0.11, 0.5)
            context.rectangle(min(self.start_x, self.end_x), min(self.start_y, self.end_y), abs(self.end_x - self.start_x), abs(self.end_y - self.start_y))
            context.fill()

class PreviewWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Preview")

        self.set_default_size(800, 800)
        self.fullscreen()

        self.editor = PreviewEditor(self)
        self.add(self.editor)

        self.connect("key-press-event", self.on_key_press_event)

    def set_preview(self, pb):
        self.editor.set_preview(pb)

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.editor.cleanup()
            self.hide()

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Snipping tool")

        self.preview = PreviewWindow()
        self.preview.connect("hide", self.on_preview_hide)

        self.set_default_size(100, 50)
        self.set_icon_from_file(get_resource_path("icon.png"))
        
        self.connect("destroy", Gtk.main_quit)

        button_take_screenshot = Gtk.Button(label="Take screenshot")
        button_take_screenshot.connect("clicked", self.on_take_screenshot)

        grid = Gtk.Grid()
        grid.attach(button_take_screenshot, 0, 1, 1, 1)
        self.add(grid)

    def on_take_screenshot(self, widget):
        self.prev_pos = self.get_position()
        self.hide()
        GLib.timeout_add(200, self.show_preview)

    def show_preview(self):
        root_win = Gdk.get_default_root_window()
        h = root_win.get_height()
        w = root_win.get_width()

        pb = Gdk.pixbuf_get_from_window(root_win, 0, 0, w, h)
        if (pb != None):
            self.preview.set_preview(pb)
            self.preview.show_all()

    def on_preview_hide(self, widget):
        self.show_all()

        (x, y) = self.prev_pos
        self.move(x, y)

def get_resource_path(rel_path):
    dir_of_py_file = os.path.dirname(__file__)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    return abs_path_to_resource

win = MainWindow()
win.show_all()

Gtk.main()
