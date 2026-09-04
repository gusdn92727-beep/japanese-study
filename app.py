import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="이효주와 현우의 일본어 공부 도우미",
    page_icon="🇯🇵",
    layout="centered"
)

# 2. 비밀번호 보안 기능 (둘만 접속 가능)
ACCESS_PASSWORD = "0487"  # 원하는 비밀번호로 변경하세요!

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 이효주와 현우의 일본어 공부 도우미")
    pwd_input = st.text_input("접속 비밀번호를 입력하세요", type="password")
    if st.button("접속하기", use_container_width=True):
        if pwd_input == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# 3. Gemini API 설정
# 아래 큰따옴표 안에 발급받으신 Gemini API 키를 넣으세요!
MY_API_KEY = "AQ.Ab8RN6KvkSApFltbjfoBGzd1S5KAd4dWJiR0PwWAbe7Zarz7iA"

if MY_API_KEY and MY_API_KEY != "여기에_Gemini_API_키를_넣으세요":
    genai.configure(api_key=MY_API_KEY)

st.title("🇯🇵 맞춤형 일본어 학습 도우미")
st.caption("텍스트를 입력하거나 사진을 찍어 단어 및 문법을 분석해보세요.")

# 4. 입력 방식 선택 (텍스트 / 사진)
tab1, tab2 = st.tabs(["📝 텍스트 입력", "📷 사진 업로드/촬영"])

prompt_instruction = """
너는 친절하고 전문적인 일본어 학습 도우미야.
전달받은 일본어 텍스트나 이미지 속 일본어를 분석해서 아래 양식에 맞게 한국어로 정돈해서 출력해 줘.

1. [원문 및 읽는 법]: 한자 위에 후리가나(히라가나 읽기)와 한글 발음 표시
2. [단어 및 JLPT 난이도 분석]: 주요 단어 추출, 한자 음/훈독, JLPT 급수(N1~N5) 표기, 뜻 풀이
3. [핵심 문법 포인트]: 문장에 사용된 주요 문법 요소 및 어조 설명
4. [활용 예문]: 해당 단어나 문법을 활용한 쉬운 예문 2개 (한글 번역 포함)
"""

selected_text = ""
uploaded_image = None

with tab1:
    selected_text = st.text_area("분석할 일본어 문장이나 단어를 입력하세요", height=120)

with tab2:
    uploaded_image = st.file_uploader("이미지를 업로드하거나 카메라로 찍으세요", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image, caption="업로드된 이미지", use_column_width=True)

# 5. 분석 실행
if st.button("✨ 일본어 상세 분석하기", type="primary", use_container_width=True):
    if MY_API_KEY == "여기에_Gemini_API_키를_넣으세요" or not MY_API_KEY:
        st.error("27번째 줄의 MY_API_KEY에 본인의 Gemini API 키를 넣어주세요!")
    else:
        with st.spinner("AI가 일본어 단어와 문법을 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                if uploaded_image is not None:
                    img = Image.open(uploaded_image)
                    response = model.generate_content([prompt_instruction, img])
                elif selected_text.strip():
                    response = model.generate_content(f"{prompt_instruction}\n\n[분석할 텍스트]:\n{selected_text}")
                else:
                    st.warning("분석할 텍스트를 입력하거나 이미지를 올려주세요.")
                    st.stop()

                st.markdown("---")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")