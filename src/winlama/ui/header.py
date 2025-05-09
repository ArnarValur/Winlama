"""
Header component for the Ollama UI.
"""
import tkinter as tk
from tkinter import ttk
import logging

from ui.base import UIComponent

logger = logging.getLogger(__name__)

class HeaderComponent(UIComponent):
    """
    The header component containing model selection and related UI elements.
    """

    def __init__(self, parent, on_model_selected_callback):
        """
        Initialize the header component.

        Args:
            parent: Parent widget
            on_model_selected_callback: Callback function for when a model is selected
        """
        super().__init__(parent)
        self.selected_model = tk.StringVar()
        self.current_chat_model_display = tk.StringVar()
        self.on_model_selected_callback = on_model_selected_callback

        # Create the frame
        self.frame = ttk.Frame(parent, height=50, style='TFrame')
        self.frame.pack_propagate(False)

        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        """Create and configure the widgets in the header."""
        label = ttk.Label(self.frame, text="Select Model:", font=("Arial", 10))
        label.pack(side='left', padx=(10, 5), pady=10)

        self.model_combobox = ttk.Combobox(
            self.frame,
            textvariable=self.selected_model,
            state='readonly',
            font=("Arial", 10),
            width=30
        )
        self.model_combobox.pack(side='left', padx=5, pady=10)
        self.model_combobox.bind('<<ComboboxSelected>>', self._on_model_selected)

        # Label showing what model is active
        self.active_model_label = ttk.Label(
            self.frame,
            textvariable=self.current_chat_model_display,
            font=("Arial", 12, 'italic'),
            anchor='w',
            justify='left'
        )
        self.active_model_label.pack(side='left', padx=10, pady=10)

    def _on_model_selected(self, event=None):
        """
        Internal handler for when a model is selected from the combobox.
        """
        current_selection = self.selected_model.get()
        logger.debug(f"Model selected in UI: {current_selection}")

        if current_selection and not current_selection.startswith("["):
            self.current_chat_model_display.set(f"Chatting with: {current_selection}")
        else:
            self.current_chat_model_display.set(current_selection or "[No model selected]")

        # Call the provided callback
        if self.on_model_selected_callback:
            self.on_model_selected_callback(current_selection)

    def update_model_list(self, model_names, default_selection=None):
        """
        Update the list of available models in the combobox.

        Args:
            model_names (list): List of model names
            default_selection (str, optional): Model to select by default
        """
        if model_names:
            self.model_combobox['values'] = model_names
            if default_selection and default_selection in model_names:
                self.model_combobox.set(default_selection)
            else:
                self.model_combobox.set(model_names[0])
            self._on_model_selected()
        else:
            self.model_combobox['values'] = []
            self.model_combobox.set("[No models found]")
            self.selected_model.set("[No models found]")
            self._on_model_selected()

    def set_error_state(self, error_message):
        """
        Set the UI to an error state.

        Args:
            error_message (str): Error message to display
        """
        self.model_combobox['values'] = []
        self.model_combobox.set(error_message)
        self.selected_model.set(error_message)
        self._on_model_selected()

    def get_selected_model(self):
        """Get the currently selected model name."""
        return self.selected_model.get()
