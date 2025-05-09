"""
Sidebar component for the Ollama UI.
"""
import tkinter as tk
from tkinter import ttk

from ui.base import UIComponent

class SidebarComponent(UIComponent):
    """
    The sidebar component for the Ollama UI containing conversation
    history and related controls.
    """

    def __init__(self, parent, on_close_callback):
        """
        Initialize the sidebar component.

        Args:
            parent: Parent widget
            on_close_callback: Callback function for the close button
        """
        super().__init__(parent)
        self.on_close_callback = on_close_callback

        # Create the frame
        self.frame = ttk.Frame(parent, width=250, style='TFrame')
        self.frame.pack_propagate(False)

        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        """Create and configure the widgets in the sidebar."""
        # Conversations header
        label = ttk.Label(self.frame, text="Conversations", font=("Arial", 12))
        label.pack(pady=10, padx=10, anchor='nw')

        # Conversation list would go here (future enhancement)

        # Bottom frame with separator and close button
        button_frame = ttk.Frame(self.frame, style='TFrame')
        button_frame.pack(side='bottom', fill='x', padx=5, pady=5)

        separator = ttk.Separator(button_frame, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.on_close_callback,
            style='TButton',
            width=10,
            cursor="hand2"
        )
        close_button.pack(side='bottom', padx=5, pady=5)

    def add_conversation(self, name, callback):
        """
        Add a conversation to the sidebar.

        Args:
            name (str): Name of the conversation
            callback: Callback function for when the conversation is selected
        """
        # This is a placeholder for future functionality
        pass
