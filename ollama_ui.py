import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk

from ollama_client import OllamaClient

class OllamaApp:
    def __init__(self, root):
        self.model_combobox = None
        self.chat_info_label = None
        self.root = root
        #self.root.set_theme("equilux")
        self.root.title("Ollama UI")
        self.root.geometry('1000x700')
        self.root.configure(bg='#2c2c2c')

        # Instantiate OllamaClient
        self.ollama_client = OllamaClient()
        self.selected_model = tk.StringVar()

        # -- Main Layout Frames --

        # Sidebar Frame Layout
        self.sidebar_frame = ttk.Frame(self.root, width=250, style='TFrame')
        self.sidebar_frame.pack(side='left', fill='y', padx=(5,0), pady=5)
        self.sidebar_frame.pack_propagate(False)

        # Main Content Frame Layout
        self.main_content_frame = ttk.Frame(self.root, style='TFrame')
        self.main_content_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # -- Populate Main Content Frame --
        # Header Frame
        self.header_frame = ttk.Frame(self.main_content_frame, height=50, style='TFrame')
        self.header_frame.pack(side='top', fill='x', padx=5, pady=5)
        self.header_frame.pack_propagate(False)

        # Chat Interface Frame
        self.chat_interface_frame = ttk.Frame(self.main_content_frame, style='TFrame')
        self.chat_interface_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # -- Add Placeholder content --
        self.populate_sidebar()
        self.populate_header()
        self.populate_chat_interface()

        self.load_ollama_models_to_ui()

    def populate_sidebar(self):
        label = ttk.Label(self.sidebar_frame, text="Conversations", font=("Arial", 12))
        label.pack(pady=10, padx=10, anchor='nw')


        # Add a separator with a Close button on the bottom of the sidebar
        button_frame = ttk.Frame(self.sidebar_frame, style='TFrame')
        button_frame.pack(side='bottom', fill='x', padx=5, pady=5)

        separator = ttk.Separator(button_frame, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        button = ttk.Button(
            button_frame,
            text="Close",
            command=self.root.destroy,
            style='TButton',
            width=10,
            cursor="hand2"
        )
        button.pack(side='bottom', padx=5, pady=5)



    def populate_header(self):
        label = ttk.Label(self.header_frame, text="Select Model:", font=("Arial", 10))
        label.pack(side='left', padx=(10,5), pady=10)

        self.model_combobox = ttk.Combobox(
            self.header_frame,
            textvariable=self.selected_model,
            state='readonly',
            font=("Arial", 10),
            width=30
        )
        self.model_combobox.pack(side='left', padx=5, pady=10)
        self.model_combobox.bind('<<ComboboxSelected>>', self.on_model_selected)

    """
    Load Ollama Models to UI
    """
    def load_ollama_models_to_ui(self):
        try:
            model_names = self.ollama_client.get_models()
            print(f"UI: Ollama models: {model_names}")
            if model_names:
                self.model_combobox['values'] = model_names
                if model_names:
                    self.model_combobox.set(model_names[0])
                    self.on_model_selected()
            else:
                self.model_combobox['values'] = []
                self.model_combobox.set("[No models found]")
                self.selected_model.set("[No models found]")

        except ConnectionError :
            print("UI: Ollama server not reachable.")
            self.model_combobox['values'] = []
            self.model_combobox.set("[Connection Error]")
            self.selected_model.set("[Connection Error]")
        except ValueError as e:
            print(f"UI: Error processing Ollama data - {e}")
            self.model_combobox['values'] = []
            self.model_combobox.set("[Data Error]")
            self.selected_model.set("[Data Error]")
        except Exception as e:
            print(f"UI: An unexpected error occurred - {e}")
            self.model_combobox['values'] = []
            self.model_combobox.set("[Unexcepted Error]")
            self.selected_model.set("[Unexcepted Error]")

        self.on_model_selected()

    """
    On Model Selected
    """
    def on_model_selected(self, event=None):
        current_selection = self.selected_model.get()
        print(f"Model selected: {current_selection}")
        if hasattr(self, 'chat_info_label'):
            if current_selection and not current_selection.startswith("["):
                self.chat_info_label.config(
                    text=f"Chatting with: {current_selection}\nChat messages will appear here...")
            else:  # Handle empty or error states
                self.chat_info_label.config(
                    text=f"{current_selection or '[No model selected]'}\nChat messages will appear here...")

    """
    Populate Chat Interface Frame
    """
    def populate_chat_interface(self):
        self.chat_info_label = ttk.Label(
            self.chat_interface_frame,
            text="Chat messages will appear here...",
            justify='left',
            font=("Arial", 12),
        )
        self.chat_info_label.pack(side='top', fill='both', anchor='nw')


if __name__ == "__main__":
    main_window = ThemedTk(theme="equilux")
    app = OllamaApp(main_window)
    main_window.mainloop()