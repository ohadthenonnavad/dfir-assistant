"""Gradio chat interface for DFIR Assistant."""

import gradio as gr
from dfir_assistant.config import get_settings


def create_app() -> gr.Blocks:
    """Create and configure the Gradio application.
    
    This is a placeholder that will be expanded in EPIC-103.
    """
    settings = get_settings()
    
    with gr.Blocks(
        title="Windows Internals DFIR Knowledge Assistant",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            """
            # 🔍 Windows Internals DFIR Knowledge Assistant
            
            AI-powered Senior DFIR Analyst assistant for Windows memory forensics
            and incident response.
            
            **Model:** {model}
            """.format(model=settings.model_name)
        )
        
        chatbot = gr.Chatbot(
            label="Chat",
            height=500,
            show_copy_button=True,
        )
        
        msg = gr.Textbox(
            label="Ask a question",
            placeholder="e.g., What is a VAD tree? / I found svchost.exe with no parent - is this suspicious?",
            lines=2,
        )
        
        with gr.Row():
            submit = gr.Button("Submit", variant="primary")
            clear = gr.Button("Clear")
        
        def respond(message: str, history: list) -> tuple[str, list]:
            """Handle user message (placeholder)."""
            # TODO: Implement actual RAG pipeline in EPIC-102
            response = f"[Placeholder] Received query: {message}\n\nFull RAG pipeline not yet implemented."
            history.append((message, response))
            return "", history
        
        submit.click(respond, [msg, chatbot], [msg, chatbot])
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: ([], ""), outputs=[chatbot, msg])
        
        gr.Markdown(
            """
            ---
            ⚠️ **Note:** Always verify commands before execution. This is an AI assistant
            and may occasionally provide incorrect information.
            """
        )
    
    return app
