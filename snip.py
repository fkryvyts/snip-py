import gi
import os
import signal

gi.require_version("Gtk", "3.0")
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, Gdk, GLib, AppIndicator3

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

class TrayIcon:
    def __init__(self):
        self.preview = PreviewWindow()
        self.indicator = AppIndicator3.Indicator.new(
            "snip-py",
            "edit-cut-symbolic",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        self.menu = Gtk.Menu()

        self.add_menuitem("Take screenshot", self.take_screenshot)
        self.add_menuitem("Quit", self.quit)

        self.indicator.set_menu(self.menu)

    def add_menuitem(self, label, callback):
        item = Gtk.MenuItem(label=label)
        item.connect("activate", callback)
        item.show()
        self.menu.append(item)

    def take_screenshot(self, source):
        GLib.timeout_add(200, self.show_preview)

    def show_preview(self):
        root_win = Gdk.get_default_root_window()
        h = root_win.get_height()
        w = root_win.get_width()

        pb = Gdk.pixbuf_get_from_window(root_win, 0, 0, w, h)
        if (pb != None):
            self.preview.set_preview(pb)
            self.preview.set_keep_above(True);
            self.preview.show_all()

    def quit(self, source):
        Gtk.main_quit()

def main():
    # Required for the indicator to function properly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    TrayIcon()
    Gtk.main()

if __name__ == "__main__":
    main()
