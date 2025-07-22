import subprocess

from gi.repository import GObject, Nautilus

from version import __app_name__


class VideoCleanerExtension(GObject.GObject, Nautilus.MenuProvider):
    def launch_application(self, menu, files):
        # Build list of paths for selected files/folders
        paths = []
        for file in files:
            # Only include files/folders with video extensions or directories
            if file.is_directory() or file.get_name().endswith(
                (".mkv", ".mp4", ".m4v", ".mp4v")
            ):
                paths.append(file.get_location().get_path())

        if not paths:
            return  # nothing to do

        # Build the command to run the application
        # Assuming the application is installed in user's PATH
        cmd = [__app_name__] + paths

        try:
            # Launch asynchronously
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Error launching {__app_name__}: {e}")

    def get_file_items(self, window, files):
        # Provide the menu item only if at least one video file or folder is selected
        if not any(
            f.is_directory() or f.get_name().endswith((".mkv", ".mp4", ".m4v", ".mp4v"))
            for f in files
        ):
            return None

        item = Nautilus.MenuItem(
            name="VideoCleanerExtension::CleanVideo",
            label=f"Clean with {__app_name__}",
            tip="Remove unwanted metadata",
        )
        item.connect("activate", self.launch_application, files)
        return [item]
