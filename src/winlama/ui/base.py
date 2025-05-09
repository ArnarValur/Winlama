"""
Base classes for UI components.
"""
import tkinter as tk
from tkinter import ttk


class UIComponent:
    """Base class for all UI components."""

    def __init__(self, parent):
        """
        Initialize a UI component.

        Args:
            parent: The parent widget or frame
        """
        self.parent = parent
        self.frame = None

    def create_widgets(self):
        """Create and configure widgets. Should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement create_widgets()")

    def get_frame(self):
        """Get the main frame of this component."""
        return self.frame
