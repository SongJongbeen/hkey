import gradio as gr
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()

# 1. OpenRouter API 키 설정 (직접 입력하거나 환경변수 사용)
OPENROUTER_API_KEY = os.getenv("openrouter_api_key")

# 비동기 클라이언트 설정
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# 2. 사용할 모델 리스트 (OpenRouter 모델 ID 기준)
MODELS = {
    "OpenAI (GPT 5.5)": "openai/gpt-5.5",
    "Anthropic (Claude 4.6 Sonnet)": "anthropic/claude-sonnet-4.6",
    "Google (Gemini 3.1 Pro)": "google/gemini-3.1-pro-preview",
    "DeepSeek (DeepSeek 3.2)": "deepseek/deepseek-v3.2"
}

# 3. 개별 모델에 요청을 보내는 비동기 함수
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

# 4. Gradio에서 호출될 메인 실행 함수
async def generate_all(prompt):

    # 비동기로 동시에 5개 모델 호출
    tasks = [fetch_response(model_id, prompt) for model_id in MODELS.values()]
    results = await asyncio.gather(*tasks)

    # Gradio의 5개 출력창에 각각 매핑되어 반환됨
    return results

# 5. Gradio UI 구성
with gr.Blocks(title="Multi-LLM Comparator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 고전번역 특수과제 연구")
    gr.Markdown("송혁기")

    with gr.Row():
        user_input = gr.Textbox(
            label="프롬프트 입력", 
            lines=5, 
            placeholder="모델들에게 물어볼 질문이나 지시사항을 입력하세요..."
        )

    with gr.Row():
        submit_btn = gr.Button("동시 생성 ⚡", variant="primary")

    gr.Markdown("### 🤖 모델별 출력 결과")

    # 4개 모델의 출력창을 깔끔하게 배치 (위 2개, 아래 2개)
    outputs = []
    with gr.Row():
        for model_name in list(MODELS.keys())[:2]:
            outputs.append(gr.Textbox(label=model_name, lines=15, interactive=False))
    with gr.Row():
        for model_name in list(MODELS.keys())[2:]:
            outputs.append(gr.Textbox(label=model_name, lines=15, interactive=False))

    # 버튼 클릭 시 이벤트 연결
    submit_btn.click(
        fn=generate_all,
        inputs=user_input,
        outputs=outputs
    )

if __name__ == "__main__":
    # 로컬에서 7860 포트로 실행됨
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860))
    )
