"""
Main application window for the Winlama application.
"""
import tkinter as tk
from tkinter import ttk
import logging
from ttkthemes import ThemedTk

from core.ollama_client import OllamaClient
from ui.header import HeaderComponent
from ui.sidebar import SidebarComponent
from ui.chat_interface import ChatInterfaceComponent

logger = logging.getLogger(__name__)

class Application:
    """
    Main application class for Winlama.
    Integrates all UI components and coordinates between them.
    """

    def __init__(self):
        """Initialize the application."""
        self.root = ThemedTk(theme="equilux")
        self.root.title("Winlama - Ollama UI")
        self.root.geometry('1000x700')
        self.root.configure(bg='#2c2c2c')

        # Initialize the Ollama client
        self.ollama_client = OllamaClient()

        # Create main frames
        self.setup_main_frames()

        # Create UI components
        self.header = HeaderComponent(self.header_frame, self.on_model_selected)
        self.sidebar = SidebarComponent(self.sidebar_frame, self.root.destroy)
        self.chat_interface = ChatInterfaceComponent(self.chat_interface_frame, self.ollama_client)

        # Pack the component frames to make them visible
        self.header.get_frame().pack(fill='both', expand=True)
        self.sidebar.get_frame().pack(fill='both', expand=True)
        self.chat_interface.get_frame().pack(fill='both', expand=True)

        # Load models
        self.load_ollama_models()

    def setup_main_frames(self):
        """Set up the main layout frames."""
        # Sidebar Frame
        self.sidebar_frame = ttk.Frame(self.root, width=250, style='TFrame')
        self.sidebar_frame.pack(side='left', fill='y', padx=(5, 0), pady=5)
        self.sidebar_frame.pack_propagate(False)

        # Main Content Frame
        self.main_content_frame = ttk.Frame(self.root, style='TFrame')
        self.main_content_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # Header Frame
        self.header_frame = ttk.Frame(self.main_content_frame, height=50, style='TFrame')
        self.header_frame.pack(side='top', fill='x', padx=5, pady=5)
        self.header_frame.pack_propagate(False)

        # Chat Interface Frame
        self.chat_interface_frame = ttk.Frame(self.main_content_frame, style='TFrame')
        self.chat_interface_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

    def load_ollama_models(self):
        """Load Ollama models from the server and update the UI."""
        try:
            model_names = self.ollama_client.get_models()
            logger.info(f"Loaded {len(model_names)} models from Ollama server")
            self.header.update_model_list(model_names)
        except ConnectionError:
            logger.error("Failed to connect to Ollama server")
            self.header.set_error_state("[Connection Error]")
            self.chat_interface.display_message(
                "Could not connect to Ollama server. Please make sure Ollama is running.",
                "error"
            )
        except ValueError as e:
            logger.error(f"Error processing Ollama data: {e}")
            self.header.set_error_state("[Data Error]")
            self.chat_interface.display_message(
                f"Error loading models: {e}",
                "error"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.header.set_error_state("[Unexpected Error]")
            self.chat_interface.display_message(
                f"An unexpected error occurred: {e}",
                "error"
            )

    def on_model_selected(self, model_name):
        """
        Handle model selection from the header component.

        Args:
            model_name (str): Name of the selected model
        """
        logger.info(f"Model selected: {model_name}")

        if model_name and not model_name.startswith("["):
            self.chat_interface.set_model(model_name)
            """self.chat_interface.display_message(
                f"Model changed to {model_name}. Start chatting!",
                "system"
            )"""

    def run(self):
        """Run the application main loop."""
        self.root.mainloop()


