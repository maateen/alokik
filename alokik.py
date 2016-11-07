import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from Engine import process_now

class FileChooserWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Alokik")
        self.set_default_size(800, 400)
        self.set_resizable(True)
        self.set_border_width(0)
        self.get_focus()
        self.set_position(Gtk.WindowPosition.CENTER)

        button = Gtk.Button("Choose Folder")
        button.connect("clicked", self.on_folder_clicked)
        self.add(button)

    def on_folder_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a folder", self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder_path = dialog.get_filename()
            print(folder_path)
            process_now(folder_path, '882E')
            print("Completed")
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def show_info_message(self):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK,
                                   "Info")
        dialog.format_secondary_text(self.text)
        dialog.run()
        print("Info dialog closed")

        dialog.destroy()

    def show_error_message(self):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.CANCEL,
                                   "Error")
        dialog.format_secondary_text(self.text)
        dialog.run()
        print("Error dialog closed")

        dialog.destroy()

win = FileChooserWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.process_now()