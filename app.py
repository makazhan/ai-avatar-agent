import mimetypes

import gradio as gr

from agent.pipeline import Pipeline
from config import AVATAR_PHOTO_PATH
from voice.tts import generate_speech

pipeline = Pipeline()


def _classify_files(files: list[str]) -> tuple[str | None, str | None]:
    """Separate file paths into the first image and first audio found."""
    image_path = None
    audio_path = None
    for f in files:
        mime = mimetypes.guess_type(f)[0] or ""
        if mime.startswith("image/") and image_path is None:
            image_path = f
        elif mime.startswith("audio/") and audio_path is None:
            audio_path = f
    return image_path, audio_path


async def respond(message, chat_history):
    """Handle multimodal input from MultimodalTextbox."""
    text = message.get("text", "").strip() if message else ""
    files = message.get("files", []) if message else []
    image_path, audio_path = _classify_files(files)

    if not text and not image_path and not audio_path:
        chat_history = chat_history or []
        chat_history.append(
            {"role": "assistant", "content": "Пожалуйста, введите текст, загрузите фото или запишите аудио."}
        )
        return (
            chat_history,
            gr.Image(value=AVATAR_PHOTO_PATH, visible=True),
            gr.Video(value=None, visible=False),
            None,
        )

    response_text, video_url, asr_text = await pipeline.process(
        text=text or None,
        image_path=image_path,
        audio_path=audio_path,
    )

    chat_history = chat_history or []

    # Show what the user sent
    parts = []
    if text:
        parts.append(text)
    if image_path:
        parts.append("[Загружено фото]")
    if audio_path:
        label = f"[Загружено аудио]: {asr_text}" if asr_text else "[Загружено аудио]"
        parts.append(label)
    chat_history.append({"role": "user", "content": " ".join(parts)})
    chat_history.append({"role": "assistant", "content": response_text})

    # Toggle avatar image / video
    video_out = None
    if video_url and "example.com" not in video_url:
        video_out = video_url

    if video_out:
        return (
            chat_history,
            gr.Image(visible=False),
            gr.Video(value=video_out, visible=True),
            None,
        )
    return (
        chat_history,
        gr.Image(value=AVATAR_PHOTO_PATH, visible=True),
        gr.Video(value=None, visible=False),
        None,
    )


def _extract_text(content) -> str:
    """Extract plain text from Gradio message content (may be str or list of dicts)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content)


async def tts_last_response(chat_history):
    """TTS the last assistant message in the chat."""
    for msg in reversed(chat_history or []):
        if msg.get("role") == "assistant":
            text = _extract_text(msg["content"])
            audio_url = await generate_speech(text)
            if audio_url and "example.com" not in audio_url:
                return gr.Audio(value=audio_url, visible=True, autoplay=True)
            break
    return gr.Audio(visible=False)


with gr.Blocks(title="AI Ресторанный Гид Алматы") as demo:
    gr.Markdown(
        "# AI Ресторанный Гид Алматы\n"
        "Мультимодальный ассистент с аватаром. Текст, голос или фото."
    )

    with gr.Row(equal_height=True):
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Диалог",
                height=500,
                placeholder="Спросите о ресторанах Алматы...",
                feedback_options=None,
                buttons=["copy"],
            )
            tts_btn = gr.Button("🔊 Озвучить последний ответ", size="sm")
            multimodal_input = gr.MultimodalTextbox(
                placeholder="Введите сообщение...",
                file_types=["image", "audio"],
                file_count="multiple",
                sources=["upload", "microphone"],
                submit_btn=True,
                elem_id="multimodal-input",
            )

        with gr.Column(scale=2, min_width=300):
            avatar_image = gr.Image(
                value=AVATAR_PHOTO_PATH,
                label="Аватар",
                interactive=False,
                visible=True,
                height=500,
            )
            video_output = gr.Video(
                label="Аватар-ответ",
                visible=False,
                autoplay=True,
                buttons=["download"],
                height=500,
            )

    tts_audio = gr.Audio(visible=False, autoplay=True, label="TTS")

    tts_btn.click(
        tts_last_response,
        inputs=[chatbot],
        outputs=[tts_audio],
        show_progress="hidden",
    )

    multimodal_input.submit(
        respond,
        inputs=[multimodal_input, chatbot],
        outputs=[chatbot, avatar_image, video_output, multimodal_input],
        show_progress_on=[chatbot],
    )

    # Auto-click the submit button when a mic recording is added.
    # The change event fires on every edit, so the JS guard ensures we only
    # trigger a click when files are present (mic just finished recording).
    _auto_submit_mic_js = """
    (v) => {
        if (v && v.files && v.files.length > 0) {
            const btn = document.querySelector('#multimodal-input button[class*="submit"]');
            if (btn) btn.click();
        }
        return v;
    }
    """
    multimodal_input.change(fn=None, inputs=[multimodal_input], js=_auto_submit_mic_js)

if __name__ == "__main__":
    demo.launch()
