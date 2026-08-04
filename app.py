import gradio as gr
import asyncio
import os
import pandas as pd
import tempfile
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("openrouter_api_key")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODELS = {
    "OpenAI (GPT 5.6 Sol)": "openai/gpt-5.6-sol",
    "Anthropic (Claude 4.6 Sonnet)": "anthropic/claude-sonnet-4.6",
    "Google (Gemini 3.1 Pro)": "google/gemini-3.1-pro-preview",
    "Kimi K3": "moonshotai/kimi-k3",
    "DeepSeek V4 Pro": "deepseek/deepseek-v4-pro"
}

async def fetch_response(model_id, prompt):
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7 # 필요에 따라 조절
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"

async def generate_all(prompt):
    print(MODELS.values())
    print(prompt)
    tasks = [fetch_response(model_id, prompt) for model_id in MODELS.values()]
    results = await asyncio.gather(*tasks)
    print(results)
    return results

def export_to_excel(prompt, res1, res2, res3, res4):
    data = {
        "구분": ["사용자 프롬프트"] + list(MODELS.keys()),
        "내용": [prompt, res1, res2, res3, res4]
    }
    df = pd.DataFrame(data)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(temp_file.name, index=False, engine='openpyxl')

    return temp_file.name

with gr.Blocks(title="한문고전번역특수과제연구") as demo:
    gr.Markdown("# 한문 고전번역 특수과제 연구1")
    gr.Markdown("오류 발생 시 1041489@gmail.com 으로 문의주세요.")

    with gr.Row():
        user_input = gr.Textbox(
            label="프롬프트 입력",
            lines=5,
            placeholder="모델들에게 물어볼 질문이나 지시사항을 입력하세요..."
        )

    with gr.Row():
        submit_btn = gr.Button("결과물 생성", variant="primary")
        excel_btn = gr.Button("엑셀로 내보내기", variant="secondary")

    excel_download = gr.File(label="다운로드할 엑셀 파일", visible=False)

    gr.Markdown("### 모델별 출력 결과")

    outputs = []
    with gr.Row():
        for model_name in list(MODELS.keys())[:2]:
            outputs.append(gr.Textbox(label=model_name, lines=15, interactive=False))
    with gr.Row():
        for model_name in list(MODELS.keys())[2:]:
            outputs.append(gr.Textbox(label=model_name, lines=15, interactive=False))

    submit_btn.click(
        fn=generate_all,
        inputs=user_input,
        outputs=outputs
    )

    excel_btn.click(
        fn=export_to_excel,
        inputs=[user_input] + outputs,
        outputs=excel_download
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=excel_download
    )

if __name__ == "__main__":
    demo.launch(share=True, theme=gr.themes.Soft())
