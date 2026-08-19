import gradio as gr
import asyncio
# import os
import pandas as pd
import tempfile
from openai import AsyncOpenAI
# from dotenv import load_dotenv

# load_dotenv()

# OPENROUTER_API_KEY = os.getenv("openrouter_api_key")
OPENROUTER_API_KEY = openrouter_api_key

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODELS = {
    # "OpenAI (GPT 5.6 Luna)": "openai/gpt-5.6-luna",
    "OpenAI (GPT 5.6 Terra)": "openai/gpt-5.6-terra",
    # "OpenAI (GPT 5.6 Sol)": "openai/gpt-5.6-sol",

    "Anthropic (Claude 5 Sonnet)": "anthropic/claude-sonnet-5",
    # "Anthropic (Claude 5 Opus)": "anthropic/claude-opus-5",
    # "Anthropic (Claude 5 Fable)": "anthropic/claude-fable-5",

    "Google (Gemini 3.7 Flash)": "google/gemini-3.7-flash",
    # "Google (Gemini 3.1 Pro)": "google/gemini-3.1-pro-preview",

    # "Moonshot (Kimi K3)": "moonshotai/kimi-k3",
    
    # "DeepSeek V4 Flash": "deepseek/deepseek-v4-flash-0731",
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

async def generate_selected(prompt, selected_models):
    async def get_result(model_name):
        # 사용자가 선택한 모델인 경우에만 API 호출
        if model_name in selected_models:
            res = await fetch_response(MODELS[model_name], prompt)
            return res
        else:
            return "" # 숨김 처리되므로 빈 문자열 반환

    # 기존 UI 텍스트박스 순서와 맞추기 위해 전체 모델 순서대로 task 생성
    tasks = [get_result(model_name) for model_name in MODELS.keys()]
    results = await asyncio.gather(*tasks)
    return results

def export_to_excel(prompt, selected_models, *results):
    data = {
        "구분": ["사용자 프롬프트"],
        "내용": [prompt]
    }
    
    # 선택된 모델의 결과만 엑셀에 추가
    for model_name, res in zip(MODELS.keys(), results):
        if model_name in selected_models:
            data["구분"].append(model_name)
            data["내용"].append(res)
            
    df = pd.DataFrame(data)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(temp_file.name, index=False, engine='openpyxl')

    return temp_file.name

# 체크박스 변경 시 UI 박스 노출 여부 업데이트 함수
def update_visibility(selected_models):
    return [gr.update(visible=(model in selected_models)) for model in MODELS.keys()]

with gr.Blocks(title="한문고전번역특수과제연구", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 한문 고전번역 특수과제 연구1")
    gr.Markdown("오류 발생 시 1041489@gmail.com 으로 문의주세요.")

    with gr.Row():
        user_input = gr.Textbox(
            label="프롬프트 입력",
            lines=5,
            placeholder="모델들에게 물어볼 질문이나 지시사항을 입력하세요..."
        )
        
    with gr.Row():
        model_selection = gr.CheckboxGroup(
            choices=list(MODELS.keys()),
            value=list(MODELS.keys()), # 기본적으로 모든 모델 선택
            label="사용할 모델 선택 (다중 선택 가능)",
        )
        
    with gr.Row():
        btn_all = gr.Button("전체 선택", size="sm")
        btn_none = gr.Button("전체 해제", size="sm")
        btn_low = gr.Button("저비용 모델 선택", size="sm")
        # btn_high = gr.Button("고성능 모델 선택", size="sm")

    with gr.Row():
        submit_btn = gr.Button("결과물 생성", variant="primary")
        excel_btn = gr.Button("엑셀로 내보내기", variant="secondary")

    excel_download = gr.File(label="다운로드할 엑셀 파일", visible=False)

    gr.Markdown("### 모델별 출력 결과")

    outputs = []
    
    # 제조사별로 모델들을 분류하여 각각의 Row로 생성
    providers = {
        "OpenAI": [k for k in MODELS.keys() if "OpenAI" in k],
        "Anthropic": [k for k in MODELS.keys() if "Anthropic" in k],
        "Google": [k for k in MODELS.keys() if "Google" in k],
        # "Moonshot": [k for k in MODELS.keys() if "Kimi" in k],
        "DeepSeek": [k for k in MODELS.keys() if "DeepSeek" in k]
    }

    for provider, models in providers.items():
        with gr.Row():
            for model_name in models:
                box = gr.Textbox(label=model_name, lines=15, interactive=False, visible=True)
                outputs.append(box)

    # 제어 버튼 클릭 시 체크박스 상태 업데이트
    btn_all.click(fn=lambda: list(MODELS.keys()), outputs=model_selection)
    btn_none.click(fn=lambda: [], outputs=model_selection)
    btn_low.click(
        fn=lambda: [
            "OpenAI (GPT 5.6 Luna)", 
            "Anthropic (Claude 5 Sonnet)", 
            "Google (Gemini 3.6 Flash)", 
            "DeepSeek V4 Flash"
        ], 
        outputs=model_selection
    )
    # btn_high.click(
    #     fn=lambda: [
    #         "OpenAI (GPT 5.6 Sol)", 
    #         "Anthropic (Claude 5 Fable)", 
    #         "Google (Gemini 3.1 Pro)", 
    #         "Kimi K3", 
    #         "DeepSeek V4 Pro"
    #     ], 
        # outputs=model_selection
    # )

    # 체크박스 상태가 변경될 때마다 텍스트박스의 노출 여부(visible) 즉시 반영
    model_selection.change(
        fn=update_visibility,
        inputs=model_selection,
        outputs=outputs
    )

    # 생성 버튼 동작
    submit_btn.click(
        fn=generate_selected,
        inputs=[user_input, model_selection],
        outputs=outputs
    )

    # 엑셀 내보내기 버튼 동작 (선택된 모델 상태도 함께 전달)
    excel_btn.click(
        fn=export_to_excel,
        inputs=[user_input, model_selection] + outputs,
        outputs=excel_download
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=excel_download
    )

if __name__ == "__main__":
    demo.launch()
