import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk

from ollama_client import OllamaClient

class OllamaApp:
    def __init__(self, root):
        """ Initialize the Ollama UI. """
        self.chat_info_label = None
        self.prompt_input = None
        self.chat_display = None
        self.active_model_label = None
        self.model_combobox = None

        self.root = root
        #self.root.set_theme("equilux")
        self.root.title("Ollama UI")
        self.root.geometry('1000x700')
        self.root.configure(bg='#2c2c2c')

        # Instantiate OllamaClient
        self.ollama_client = OllamaClient()
        self.selected_model = tk.StringVar()
        self.current_chat_model_display = tk.StringVar()

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
        self.populate_chat_interface() # <- this will be updated

        self.load_ollama_models_to_ui()

    def populate_sidebar(self):
        """ Populate the sidebar with a label and a combobox for selecting a model. """

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
        """ Populate the header with a label and a combobox for selecting a model. """

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

        # Label showing what model is active
        self.active_model_label = ttk.Label(
            self.header_frame,
            textvariable=self.current_chat_model_display,
            font=("Arial", 12, 'italic'),
            anchor='w',
            justify='left'
        )
        self.active_model_label.pack(side='left', padx=10, pady=10)

    def load_ollama_models_to_ui(self):
        """ Load Ollama models and update the UI. """

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

    def on_model_selected(self, event=None):
        """ Handle model selection and update the UI accordingly. """

        current_selection = self.selected_model.get()
        print(f"Model selected in UI: {current_selection}")
        if current_selection and not current_selection.startswith("["):
            self.current_chat_model_display.set(f"Chatting with: {current_selection}")
        else:
            self.current_chat_model_display.set(current_selection or "[No model selected]")
        if hasattr(self, 'chat_display'):
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')

    def populate_chat_interface(self):
        """ Populate the chat interface with a chat display and input area. """

        # Frame for chat display and scrollbar
        chat_display_frame = ttk.Frame(self.chat_interface_frame)
        chat_display_frame.pack(
            side='top',
            fill='both',
            expand=True,
            padx=5,
            pady=(0,5)
        )

        self.chat_display = tk.Text(
            chat_display_frame,
            wrap='word',
            state='disabled',
            font=("Arial", 11),
            bg='#222222',
            fg='#E0E0E0',
            padx=5,
            pady=5,
            relief='flat',
            borderwidth=0
        )

        # ttk.Scrollbar
        scrollbar = ttk.Scrollbar(chat_display_frame, orient='vertical', command=self.chat_display.yview)
        self.chat_display['yscrollcommand'] = scrollbar.set

        scrollbar.pack(side='right', fill='y')
        self.chat_display.pack(side='left', fill='both', expand=True)

        self.setup_chat_tags()

        # -- Input Area --
        input_frame = ttk.Frame(self.chat_interface_frame)
        input_frame.pack(side='bottom', fill='x', padx=(5,0), pady=5)

        self.prompt_input = ttk.Entry(input_frame, width=70, font=("Arial", 11))
        self.prompt_input.pack(side='left', fill='x', expand=True, padx=(5,0), ipady=5)
        # Bind Enter key to send_message
        self.prompt_input.bind('<Return>', self.send_message)

        send_button = ttk.Button(input_frame, text="Send", command=self.send_message, style='Accent.TButton')
        send_button.pack(side='right', padx=(0,5), pady=5)

    def setup_chat_tags(self):
        """ Set up tags for different types of messages in the chat display. """

        if hasattr(self, 'chat_display') and self.chat_display:
            # User messages: right-aligned
            self.chat_display.tag_configure(
                "user",
                foreground="#70AEEF",
                font=("Arial", 11, 'bold'),
                justify="right",
                lmargin1=50, lmargin2=50, rmargin=10,
            )

            # Model messages: left-aligned
            self.chat_display.tag_configure(
                "model",
                foreground="#A0D9A1",
                font=("Arial", 11),
                justify="left",
                lmargin1=10, lmargin2=10, rmargin=50
            )

            # Model Pending messages: left-aligned
            self.chat_display.tag_configure(
                "model_pending",
                foreground="#AAAAAA",
                font=("Arial", 11, 'italic'),
                justify="left",
                lmargin1=10, lmargin2=10, rmargin=50
            )

            # System messages: left-aligned
            self.chat_display.tag_configure(
                "system",
                foreground="#FF8C69",
                font=("Arial", 11, 'italic'),
                justify="left",
                lmargin1=10, lmargin2=10, rmargin=10
            )

    def display_message(self, message, tag_name=None):
        """ Display a message in the chat display with an optional tag. """
        if hasattr(self, 'chat_display') and self.chat_display:
            self.chat_display.config(state='normal')
            text_to_insert = message + "\n\n"

            if tag_name:
                self.chat_display.insert(tk.END, text_to_insert, tag_name)
            else:
                self.chat_display.insert(tk.END, text_to_insert)

            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')
        else:
            print("Chat display not initialized. Cannot display message.")

    def send_message(self, event=None):
        """ Send a message to the Ollama server and display the response. """

        prompt_text = self.prompt_input.get().strip()
        if not prompt_text:
            return

        selected_model_name = self.selected_model.get()
        if not selected_model_name or selected_model_name.startswith("["):
            self.display_message("System: Please select a model first.", "system")
            return

        # Display user message
        self.display_message(f"You: {prompt_text}", "user")
        self.prompt_input.delete(0, tk.END)

        # -- Placeholder for Ollama interaction --
        # we will call self.ollama_client.generate_responses() here
        self.display_message(f"Ollama ({selected_model_name}): Thinking...", "model_pending")

        # Simulate a delay and response for now
        # self.root.after(1000, lambda: self.display_message(f"Ollama ({selected_model_name}) response: {prompt_text}", "model_response"))

        # TODO: Call OllamaClient to get actual response and display it.


if __name__ == "__main__":
    main_window = ThemedTk(theme="equilux")
    app = OllamaApp(main_window)
    main_window.mainloop()