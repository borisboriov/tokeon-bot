import gradio as gr

from app.rag import RAGPipeline

_rag: RAGPipeline | None = None


def _get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag


def _sources_md(hits: list[dict]) -> str:
    if not hits:
        return ""
    lines = ["**Источники:**"]
    for h in hits:
        m = h["metadata"]
        title = m.get("title", "")[:60]
        source = m.get("source_file", "")
        score = h["score"]
        lines.append(f"- {title} `{source}` (релевантность: {score:.2f})")
    return "\n".join(lines)


def chat(message: str, history: list[tuple[str, str]]) -> tuple[str, list[tuple[str, str]]]:
    if not message.strip():
        return "", history

    rag = _get_rag()
    # Pass history (without source annotations) to RAG
    clean_history = [(u, a.split("\n\n**Источники:**")[0]) for u, a in history]
    answer, hits = rag.answer(message, history=clean_history)
    sources = _sources_md(hits)
    full_reply = f"{answer}\n\n{sources}" if sources else answer

    history = history + [(message, full_reply)]
    return "", history


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Токеон — помощник", theme=gr.themes.Soft()) as demo:
        gr.Markdown("## Токеон — служба поддержки\nЗадайте вопрос о платформе, ЦФА или документах.")

        chatbot = gr.Chatbot(label="Диалог", height=500)
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Введите вопрос...",
                show_label=False,
                scale=9,
                container=False,
            )
            send_btn = gr.Button("Отправить", scale=1, variant="primary")

        clear_btn = gr.Button("Очистить диалог", variant="secondary")

        send_btn.click(chat, inputs=[msg, chatbot], outputs=[msg, chatbot])
        msg.submit(chat, inputs=[msg, chatbot], outputs=[msg, chatbot])
        clear_btn.click(lambda: ([], ), outputs=[chatbot])

    return demo
