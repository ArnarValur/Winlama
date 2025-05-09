# ollama_ui.py
import tkinter as tk
from itertools import accumulate
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import threading
import queue

from ollama_client import OllamaClient

class OllamaApp:
    def __init__(self, root):
        """ Initialize the Ollama UI. """

        self.root = root
        self.root.title("Ollama UI")
        self.root.geometry('1000x700')
        #self.root.set_theme("equilux")
        self.root.configure(bg='#2c2c2c')

        # Instantiate OllamaClient
        self.ollama_client = OllamaClient()
        self.selected_model = tk.StringVar()
        self.current_chat_model_display = tk.StringVar()
        self.current_conversation_context = None
        self.active_stream_id = None
        # Thread for queuing messages
        self.response_queue = queue.Queue()

        # Make sure on_model_selected also resets/cancels any active stream if a new model is chosen mid-stream (advanced)

        # -- Initialize UI elements to None for clarity before they are created --
        self.sidebar_frame = None
        self.main_content_frame = None
        self.header_frame = None
        self.chat_interface_frame = None
        self.model_combobox = None
        self.active_model_label = None
        self.chat_display = None
        self.prompt_input = None
        self.send_button = None
        self.current_stream_insert_mark = None

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
        # Check the queue
        self.check_response_queue()

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
        """
        Handle model selection and update the UI accordingly.
        """
        current_selection = self.selected_model.get()
        print(f"Model selected in UI: {current_selection}")
        if current_selection and not current_selection.startswith("["):
            self.current_chat_model_display.set(f"Chatting with: {current_selection}")
        else:
            self.current_chat_model_display.set(current_selection or "[No model selected]")

        self.current_conversation_context = None
        # Clear pending responses
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
            except queue.Empty:
                continue

        if hasattr(self, 'chat_display') and self.chat_display:
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')
        if hasattr(self, 'prompt_input') and self.prompt_input:
            self.prompt_input.config(state='normal')

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
        self.prompt_input.bind('<Return>', self.send_message_threaded)

        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message_threaded, style='Accent.TButton')
        self.send_button.pack(side='right', padx=(0,5), pady=5)

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

            # Error messages: left-aligned
            self.chat_display.tag_configure(
                "error",
                foreground="#FF6B6B",
                font=("Arial", 11, 'bold'),
                justify="left",
                lmargin1=10, lmargin2=10, rmargin=10
            )

    def display_message(self, message, tag_name=None, stream_chunk=False, is_first_chunk=False):
        """ Display a message in the chat display with an optional tag. """
        if not (hasattr(self, 'chat_display') and isinstance(self.chat_display, tk.Text)):
            return

        self.chat_display.config(state='normal')

        # Model response, error or system
        if is_first_chunk:
            thinking_message_start_index = self.chat_display.search(
                "Thinking...",
                tk.END, # Stop index for backwards search (effectively start from the end)
                "1.0",  # Start index for backwards search (effectively search up to the beginning)
                backwards=True,
                nocase=True, # Add this for robustness
                count=tk.IntVar() # Necessary for backwards search
            )

            if thinking_message_start_index: # Check if the string was found
                line_number = thinking_message_start_index.split('.')[0]
                line_start_index = f"{line_number}.0"
                tags_at_index = self.chat_display.tag_names(thinking_message_start_index)
                if "model_pending" in tags_at_index:
                    self.chat_display.delete(f"{line_start_index}", f"{line_start_index} +1 line")

            self.root.update_idletasks()

            # 3. Insert the first chunk (which already includes the "Ollama (model): " prefix from the worker)
            # No extra newlines here yet, just the start of the stream.
            self.chat_display.insert(tk.END, message, tag_name)
            self.current_stream_insert_mark = self.chat_display.index(f"{tk.END}-1c")

        elif stream_chunk and not is_first_chunk:
            self.chat_display.insert(tk.END, message, tag_name)
            self.current_stream_insert_mark = self.chat_display.index(f"{tk.END}-1c")

        else:
            text_to_insert = message + "\n\n"
            if tag_name:
                self.chat_display.insert(tk.END, text_to_insert, tag_name)
            else:
                self.chat_display.insert(tk.END, text_to_insert)

        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def send_message_threaded(self, event=None):
        """
        Handles UI changes and starts a new thread for Ollama communication.
        :param event:
        :return:
        """
        prompt_text = self.prompt_input.get().strip()
        if not prompt_text:
            return

        selected_model_name = self.selected_model.get()
        if not selected_model_name or selected_model_name.startswith("["):
            self.display_message("System: Please select a model first.", "system")
            return

        self.display_message(f"{prompt_text}", "user")
        self.prompt_input.delete(0, tk.END)

        if hasattr(self, 'prompt_input'): self.prompt_input.config(state='disabled')
        if hasattr(self, 'send_button'): self.send_button.config(state='disabled')

        self.display_message(f"({selected_model_name}): Thinking...", "model_pending")
        self.root.update_idletasks()

        # Create and start the worker thread
        thread = threading.Thread(
            target=self._send_message_worker,
            args=(selected_model_name, prompt_text, self.current_conversation_context),
            daemon=True
        )
        thread.start()

    def _send_message_worker(self, model_name, prompt, context):
        """
        This function runs in a separate thread to call Ollama.
        :param model_name:
        :param prompt:
        :param context:
        :return:
        """
        is_first_chunk_for_ui = True
        accumulate_response_for_prefix = ""

        try:
            for chunk_data in self.ollama_client.generate_response_stream(model_name, prompt, context=context):

                if chunk_data.get('error'):
                    self.response_queue.put({'type': 'stream_error', 'message': chunk_data['error'], 'model_name': model_name})
                    return

                token = chunk_data.get('response', '')
                done = chunk_data.get('done', False)

                if token:
                    if is_first_chunk_for_ui:
                        display_token = f"Ollama ({model_name}): {token}"
                    else:
                        display_token = token

                    self.response_queue.put({
                        'type': 'stream_chunk',
                        'token': display_token,
                        'model_name': model_name,
                        'is_first_chunk_for_ui': is_first_chunk_for_ui
                    })
                    if is_first_chunk_for_ui:
                        is_first_chunk_for_ui = False

                if done:
                    final_context = chunk_data.get('context')
                    self.response_queue.put({
                        'type': 'stream_done',
                        'context': final_context,
                        'model_name': model_name
                        # 'full_response_data': chunk_data # Pass more if needed
                    })
                    return

        except Exception as e:
            print(f"UI Worker (_send_message_worker): Unhandled exception - {e}")
            self.response_queue.put({
                'type': 'stream_error',
                'message': f"Application error: {e}",
                'model_name': model_name
            })

        """except ConnectionError as e:
            self.response_queue.put({
                'status': 'error',
                'message': f"System: Connection error - {e}"
            })
        except TimeoutError as e:
            self.response_queue.put({
                'status': 'error',
                'message': f"System: Timeout error - {e}"
            })
        except ValueError as e:
            self.response_queue.put({
                'status': 'error',
                'message': f"System: Ollama error - {e}"
            })
        except Exception as e:
            self.response_queue.put({
                'status': 'error',
                'message': f"System: An unexpected error occurred - {e}"
            })"""

    def check_response_queue(self):
        """
        Periodically check the queue for messages from the worker thread.
        :return:
        """
        try:
            message_data = self.response_queue.get_nowait()
            msg_type = message_data.get('type')
            model_name = message_data.get('model_name', self.selected_model.get())

            if msg_type == 'stream_chunk':
                self.display_message(
                    message_data['token'],
                    tag_name='model',
                    stream_chunk=True,
                    is_first_chunk=message_data.get('is_first_chunk_for_ui', False)
                )
            elif msg_type == 'stream_done':
                self.current_conversation_context = message_data.get('context')
                if hasattr(self, 'chat_display') and self.chat_display:
                    self.chat_display.config(state='normal')
                    self.chat_display.insert(tk.END, "\n\n")
                    self.chat_display.see(tk.END)
                    self.chat_display.config(state='disabled')

                if hasattr(self, 'prompt_input'): self.prompt_input.config(state='normal')
                if hasattr(self, 'send_button'): self.send_button.config(state='normal')
                if hasattr(self, 'prompt_input'): self.prompt_input.focus_set()

            elif msg_type == 'stream_error':
                if hasattr(self, 'chat_display') and self.chat_display:
                    self.chat_display.config(state='normal')
                    thinking_message_start_index = self.chat_display.search(
                        "Thinking...",
                        tk.END,
                        "1.0",
                        backwards=True,
                        nocase=True,
                        count=tk.IntVar()
                    )
                    if thinking_message_start_index:
                        line_number = thinking_message_start_index.split('.')[0]
                        line_start_index = f"{line_number}.0"
                        tags_at_index = self.chat_display.tag_names(thinking_message_start_index)
                        if 'model_pending' in tags_at_index:
                            self.chat_display.delete(f"{line_start_index}", f"{line_start_index} +1 line")
                    self.chat_display.config(state='disabled')

                self.display_message(f"Error from {model_name}: {message_data['message']}", "error")

                if hasattr(self, 'prompt_input'): self.prompt_input.config(state='normal')
                if hasattr(self, 'send_button'): self.send_button.config(state='normal')
                if hasattr(self, 'prompt_input'): self.prompt_input.focus_set()

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_response_queue)


if __name__ == "__main__":
    main_window = ThemedTk(theme="equilux")
    app = OllamaApp(main_window)
    main_window.mainloop()