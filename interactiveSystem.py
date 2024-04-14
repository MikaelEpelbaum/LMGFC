import InteractiveSystem.config


def PLUGIN_ENTRY():
    InteractiveSystem.config.load_config()  # Loads configuration data from interactiveSystem/config.ini

    # Only import the rest of the code after the translations have been loaded, because the _ function (gettext)
    # needs to have been imported in the namespace first.
    from InteractiveSystem.ida.ui import InteractiveSystemPlugin
    return InteractiveSystemPlugin()
