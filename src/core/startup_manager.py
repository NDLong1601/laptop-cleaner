import winreg

# The "disabled" startup key used by many tools (e.g., Autoruns) to disable without deleting
DISABLED_KEY_SUFFIX = r"Software\Microsoft\Windows\CurrentVersion\Run (Disabled)"

class StartupManager:
    def __init__(self):
        self.run_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        ]

    def get_startup_apps(self):
        """Get list of active startup applications from Registry."""
        apps = []
        for hkey, key_path in self.run_keys:
            try:
                registry_key = winreg.OpenKey(hkey, key_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(registry_key, i)
                        location = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                        apps.append({
                            "name": name,
                            "command": value,
                            "location": location,
                            "key_path": key_path,
                            "hkey": hkey,
                            "status": "Enabled"
                        })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(registry_key)
            except WindowsError:
                pass

        # Also list disabled items so user can re-enable them
        for hkey, _ in self.run_keys:
            disabled_path = DISABLED_KEY_SUFFIX
            try:
                registry_key = winreg.OpenKey(hkey, disabled_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(registry_key, i)
                        location = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                        apps.append({
                            "name": name,
                            "command": value,
                            "location": location,
                            "key_path": disabled_path,
                            "hkey": hkey,
                            "status": "Disabled"
                        })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(registry_key)
            except WindowsError:
                pass  # Key doesn't exist yet, that's fine

        return apps

    def disable_startup_app(self, hkey, key_path, name, command):
        """
        Disable a startup app by moving it from the Run key to a Disabled key.
        This preserves the entry so it can be re-enabled later.
        """
        try:
            # Write to disabled key first
            disabled_key = winreg.CreateKeyEx(hkey, DISABLED_KEY_SUFFIX, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(disabled_key, name, 0, winreg.REG_SZ, command)
            winreg.CloseKey(disabled_key)

            # Then remove from active Run key
            active_key = winreg.OpenKey(hkey, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(active_key, name)
            winreg.CloseKey(active_key)

            return True, f"Disabled '{name}'. It can be re-enabled from this list."
        except WindowsError as e:
            return False, f"Failed: Access Denied or Not Found. Try running as Admin.\nError: {e}"

    def enable_startup_app(self, hkey, disabled_key_path, name, command):
        """
        Re-enable a previously disabled startup app by moving it back to the Run key.
        """
        try:
            # Determine the active Run key path (HKCU or HKLM)
            active_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            # Write back to the active Run key
            active_key = winreg.OpenKey(hkey, active_key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(active_key, name, 0, winreg.REG_SZ, command)
            winreg.CloseKey(active_key)

            # Remove from disabled key
            disabled_key = winreg.OpenKey(hkey, disabled_key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(disabled_key, name)
            winreg.CloseKey(disabled_key)

            return True, f"Re-enabled '{name}'."
        except WindowsError as e:
            return False, f"Failed: Access Denied or Not Found. Try running as Admin.\nError: {e}"
