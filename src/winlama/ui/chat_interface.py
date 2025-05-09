"""
Chat interface component for the Ollama UI.
"""
import tkinter as tk
from tkinter import ttk
import logging
import queue
import threading

from ui.base import UIComponent
from core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class ChatInterfaceComponent(UIComponent):
    """
    The chat interface component for the Ollama UI containing the chat display and input area.
    """

    def __init__(self, parent, ollama_client):
        """
        Initialize the chat interface component.

        Args:
            parent: Parent widget
            ollama_client: Instance of OllamaClient
        """
        super().__init__(parent)
        self.ollama_client = ollama_client
        self.current_conversation_context = None
        self.active_stream_id = None
        self.current_stream_insert_mark = None
        self.response_queue = queue.Queue()
        self.current_model = None

        # Create the frame
        self.frame = ttk.Frame(parent, style='TFrame')

        # Create widgets
        self.create_widgets()

        # Start queue checker
        self.check_response_queue()

    def create_widgets(self):
        """Create and configure the widgets in the chat interface."""
        # Frame for chat display and scrollbar
        chat_display_frame = ttk.Frame(self.frame)
        chat_display_frame.pack(
            side='top',
            fill='both',
            expand=True,
            padx=5,
            pady=(0, 5)
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

        # Scrollbar
        scrollbar = ttk.Scrollbar(chat_display_frame, orient='vertical', command=self.chat_display.yview)
        self.chat_display['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side='right', fill='y')
        self.chat_display.pack(side='left', fill='both', expand=True)
        self.setup_chat_tags()

        # Input area
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(side='bottom', fill='x', padx=(5, 0), pady=5)

        self.prompt_input = ttk.Entry(input_frame, width=70, font=("Arial", 11))
        self.prompt_input.pack(side='left', fill='x', expand=True, padx=(5, 0), ipady=5)
        self.prompt_input.bind('<Return>', self.send_message_threaded)

        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message_threaded,
            style='Accent.TButton'
        )
        self.send_button.pack(side='right', padx=(0, 5), pady=5)

    def setup_chat_tags(self):
        """Set up tags for different types of messages in the chat display."""
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
        """
        Display a message in the chat display with an optional tag.

        Args:
            message (str): The message to display
            tag_name (str, optional): The tag to apply to the message
            stream_chunk (bool): Whether this is part of a stream
            is_first_chunk (bool): Whether this is the first chunk of a stream
        """
        if not isinstance(self.chat_display, tk.Text):
            return

        self.chat_display.config(state='normal')

        # Handle first chunk (remove "Thinking..." message)
        if is_first_chunk:
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
                if "model_pending" in tags_at_index:
                    self.chat_display.delete(f"{line_start_index}", f"{line_start_index} +1 line")

            # Insert first chunk
            self.chat_display.insert(tk.END, message, tag_name)
            self.current_stream_insert_mark = self.chat_display.index(f"{tk.END}-1c")

        elif stream_chunk and not is_first_chunk:
            # Continue stream
            self.chat_display.insert(tk.END, message, tag_name)
            self.current_stream_insert_mark = self.chat_display.index(f"{tk.END}-1c")

        else:
            # Normal message
            text_to_insert = message + "\n\n"
            if tag_name:
                self.chat_display.insert(tk.END, text_to_insert, tag_name)
            else:
                self.chat_display.insert(tk.END, text_to_insert)

        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def send_message_threaded(self, event=None):
        """
        Handle sending a message and start a new thread for Ollama communication.
        """
        prompt_text = self.prompt_input.get().strip()
        if not prompt_text:
            return

        if not self.current_model:
            self.display_message("System: Please select a model first.", "system")
            return

        # Display user message
        self.display_message(f"{prompt_text}", "user")
        self.prompt_input.delete(0, tk.END)

        # Disable input while processing
        self.prompt_input.config(state='disabled')
        self.send_button.config(state='disabled')

        # Show thinking message
        self.display_message(f"({self.current_model}): Thinking...", "model_pending")

        # Create and start worker thread
        thread = threading.Thread(
            target=self._send_message_worker,
            args=(self.current_model, prompt_text, self.current_conversation_context),
            daemon=True
        )
        thread.start()

    def _send_message_worker(self, model_name, prompt, context):
        """
        Worker thread function to call Ollama API.

        Args:
            model_name (str): The model to use
            prompt (str): The user's prompt
            context: Conversation context
        """
        is_first_chunk_for_ui = True

        try:
            for chunk_data in self.ollama_client.generate_response_stream(model_name, prompt, context=context):
                if chunk_data.get('error'):
                    self.response_queue.put({
                        'type': 'stream_error',
                        'message': chunk_data['error'],
                        'model_name': model_name
                    })
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
                    })
                    return

        except Exception as e:
            logger.error(f"Unhandled exception in message worker: {e}")
            self.response_queue.put({
                'type': 'stream_error',
                'message': f"Application error: {e}",
                'model_name': model_name
            })

    def check_response_queue(self):
        """
        Periodically check the queue for messages from the worker thread.
        """
        try:
            message_data = self.response_queue.get_nowait()
            msg_type = message_data.get('type')
            model_name = message_data.get('model_name', self.current_model)

            if msg_type == 'stream_chunk':
                self.display_message(
                    message_data['token'],
                    tag_name='model',
                    stream_chunk=True,
                    is_first_chunk=message_data.get('is_first_chunk_for_ui', False)
                )
            elif msg_type == 'stream_done':
                self.current_conversation_context = message_data.get('context')

                # Add newlines after completing a message
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "\n\n")
                self.chat_display.see(tk.END)
                self.chat_display.config(state='disabled')

                # Re-enable input
                self.prompt_input.config(state='normal')
                self.send_button.config(state='normal')
                self.prompt_input.focus_set()

            elif msg_type == 'stream_error':
                # Remove thinking message if present
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

                # Display error
                self.display_message(f"Error from {model_name}: {message_data['message']}", "error")

                # Re-enable input
                self.prompt_input.config(state='normal')
                self.send_button.config(state='normal')
                self.prompt_input.focus_set()

        except queue.Empty:
            pass
        finally:
            # Schedule next check
            self.frame.after(100, self.check_response_queue)

    def set_model(self, model_name):
        """
        Set the current model.

        Args:
            model_name (str): Name of the model to use
        """
        self.current_model = model_name
        self.current_conversation_context = None

        # Clear chat display
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')

    def clear_chat(self):
        """Clear the chat display and reset context."""
        self.current_conversation_context = None

        # Clear chat display
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
