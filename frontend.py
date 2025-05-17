import gradio as gr
from chat import graph

def chat_interface(user_input, history):
    try:
        response = graph.invoke({"messages": ("user", user_input)}, config={"configurable": {"thread_id": "09042004"}})['messages'][-1].content
        history.append((user_input, response))
        return history, ""
    except Exception as e:
        history.append((user_input, f"[ERROR] {str(e)}"))
        return history, ""


with gr.Blocks() as demo:
    gr.Markdown("# 📬 Gmail Agent Chat")
    
    chatbot = gr.Chatbot(label="Assistant")
    msg = gr.Textbox(placeholder="Ask me to read, search or reply to an email...", show_label=False)
    
    clear_btn = gr.Button("Clear Chat")

    state = gr.State([])

    msg.submit(chat_interface, [msg, state], [chatbot, msg])
    clear_btn.click(lambda: ([], ""), None, [chatbot, msg])


if __name__ == "__main__":
    demo.launch(share=False)
