import random
import string

import idaapi
import ida_hexrays

import InteractiveSystem.config
from InteractiveSystem.ida.handlers import ExplainHandler, RenameHandler, SwapModelHandler
from InteractiveSystem.ida.LMPA import LMPAHandler
from InteractiveSystem.models.base import GPT4_MODEL_NAME, GPT3_MODEL_NAME



_ = InteractiveSystem.config.translate.gettext

# =============================================================================
# Setup the context menu and hotkey in IDA
# =============================================================================

class InteractiveSystemPlugin(idaapi.plugin_t):
    flags = 0
    explain_action_name = "interactiveSystem:explain_function"
    explain_menu_path = "Edit/InteractiveSystem/" + _("Explain function")
    rename_action_name = "interactiveSystem:rename_function"
    rename_menu_path = "Edit/InteractiveSystem/" + _("Rename variables")
    LMPA_action_name = "interactiveSystem:LMPA_function"
    LMPA_menu_path = "Edit/InteractiveSystem/" + _("LMPA")

    # Model selection menu
    select_gpt35_action_name = "interactiveSystem:select_gpt35"
    select_gpt4_action_name = "interactiveSystem:select_gpt4"
    select_gpt35_menu_path = "Edit/InteractiveSystem/" + _("Select model") + f"/{GPT3_MODEL_NAME}"
    select_gpt4_menu_path = "Edit/InteractiveSystem/" + _("Select model") + f"/{GPT4_MODEL_NAME}"

    wanted_name = 'InteractiveSystem'
    wanted_hotkey = ''
    comment = _("Uses {model} to enrich the decompiler's output").format(model=str(InteractiveSystem.config.model))
    help = _("See usage instructions on GitHub")
    menu = None

    # -----------------------------------------------------------------------------

    def init(self):
        # Check whether the decompiler is available
        if not ida_hexrays.init_hexrays_plugin():
            return idaapi.PLUGIN_SKIP

        # Function explaining action
        explain_action = idaapi.action_desc_t(self.explain_action_name,
                                              _('Explain function'),
                                              ExplainHandler(),
                                              "Ctrl+Alt+G",
                                              _('Use {model} to explain the currently selected function').format(
                                                  model=str(InteractiveSystem.config.model)),
                                              201)
        idaapi.register_action(explain_action)
        idaapi.attach_action_to_menu(self.explain_menu_path, self.explain_action_name, idaapi.SETMENU_APP)

        # Variable renaming action
        rename_action = idaapi.action_desc_t(self.rename_action_name,
                                             _('Rename variables'),
                                             RenameHandler(),
                                             "Ctrl+Alt+R",
                                             _("Use {model} to rename this function's variables").format(
                                                 model=str(InteractiveSystem.config.model)),
                                             201)
        idaapi.register_action(rename_action)
        idaapi.attach_action_to_menu(self.rename_menu_path, self.rename_action_name, idaapi.SETMENU_APP)

        # LMPA
        LMPA_action = idaapi.action_desc_t(self.LMPA_action_name,
                                             _('LMPA Renamings'),
                                             LMPAHandler(),
                                             "Ctrl+Alt+L",
                                             _("Use {model} to apply LMPA").format(
                                                 model=str(InteractiveSystem.config.model)),
                                             201)
        idaapi.register_action(LMPA_action)
        idaapi.attach_action_to_menu(self.LMPA_menu_path, self.LMPA_action_name, idaapi.SETMENU_APP)

        self.generate_plugin_select_menu()

        # Register context menu actions
        self.menu = ContextMenuHooks()
        self.menu.hook()

        return idaapi.PLUGIN_KEEP

    # -----------------------------------------------------------------------------

    def generate_plugin_select_menu(self):
        # Delete any possible previous entries
        idaapi.unregister_action(self.select_gpt35_action_name)
        idaapi.unregister_action(self.select_gpt4_action_name)
        idaapi.detach_action_from_menu(self.select_gpt35_menu_path, self.select_gpt35_action_name)
        idaapi.detach_action_from_menu(self.select_gpt4_menu_path, self.select_gpt4_action_name)

        # For some reason, IDA seems to have a bug when replacing actions by new ones with identical names.
        # The old action object appears to be reused, at least partially, leading to unwanted begavior?
        # The best workaround I have found is to generate random names each time.
        self.select_gpt35_action_name = f"interactiveSystem:{''.join(random.choices(string.ascii_lowercase, k=7))}"
        self.select_gpt4_action_name = f"interactiveSystem:{''.join(random.choices(string.ascii_lowercase, k=7))}"

        # Icon #208 is a check mark.
        select_gpt35_action = idaapi.action_desc_t(self.select_gpt35_action_name,
                                                   GPT3_MODEL_NAME,
                                                   None if str(InteractiveSystem.config.model) == GPT3_MODEL_NAME
                                                   else SwapModelHandler(GPT3_MODEL_NAME, self),
                                                   "",
                                                   "",
                                                   208 if str(InteractiveSystem.config.model) == GPT3_MODEL_NAME else 0)

        idaapi.register_action(select_gpt35_action)
        idaapi.attach_action_to_menu(self.select_gpt35_menu_path, self.select_gpt35_action_name, idaapi.SETMENU_APP)

        # Select gpt-4 action
        select_gpt4_action = idaapi.action_desc_t(self.select_gpt4_action_name,
                                                  GPT4_MODEL_NAME,
                                                  None if str(InteractiveSystem.config.model) == GPT4_MODEL_NAME
                                                  else SwapModelHandler(GPT4_MODEL_NAME, self),
                                                  "",
                                                  "",
                                                  208 if str(InteractiveSystem.config.model) == GPT4_MODEL_NAME else 0)
        idaapi.register_action(select_gpt4_action)
        idaapi.attach_action_to_menu(self.select_gpt35_menu_path, self.select_gpt4_action_name, idaapi.SETMENU_APP)

    # -----------------------------------------------------------------------------

    def run(self, arg):
        pass

    # -----------------------------------------------------------------------------

    def term(self):
        idaapi.detach_action_from_menu(self.explain_menu_path, self.explain_action_name)
        idaapi.detach_action_from_menu(self.rename_menu_path, self.rename_action_name)
        idaapi.detach_action_from_menu(self.select_gpt35_menu_path, self.select_gpt35_action_name)
        idaapi.detach_action_from_menu(self.select_gpt4_menu_path, self.select_gpt4_action_name)
        if self.menu:
            self.menu.unhook()
        return

# -----------------------------------------------------------------------------

class ContextMenuHooks(idaapi.UI_Hooks):
    def finish_populating_widget_popup(self, form, popup):
        # Add actions to the context menu of the Pseudocode view
        if idaapi.get_widget_type(form) == idaapi.BWN_PSEUDOCODE:
            idaapi.attach_action_to_popup(form, popup, InteractiveSystemPlugin.explain_action_name, "InteractiveSystem/")
            idaapi.attach_action_to_popup(form, popup, InteractiveSystemPlugin.rename_action_name, "InteractiveSystem/")
