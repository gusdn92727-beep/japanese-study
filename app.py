import streamlit as st
from google import genai
from PIL import Image
from gtts import gTTS
import io

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="효주와 현우의 일본어 공부 도우미",
    page_icon="🇯🇵",
    layout="centered"
)

# 2. 비밀번호 보안 기능
ACCESS_PASSWORD = "0487"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 효주와 현우의 일본어 공부 도우미")
    pwd_input = st.text_input("접속 비밀번호를 입력하세요", type="password")
    if st.button("접속하기", use_container_width=True):
        if pwd_input == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# 세션 상태 초기화 (단어장 / 오답노트 / 채팅 기록)
if "vocab_list" not in st.session_state:
    st.session_state.vocab_list = []
if "wrong_notes" not in st.session_state:
    st.session_state.wrong_notes = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. Gemini API 설정
MY_API_KEY = "AQ.Ab8RN6KvkSApFltbjfoBGzd1S5KAd4dWJiR0PwWAbe7Zarz7iA"

# 사이드바: 현우 님의 학습 레벨 설정
st.sidebar.title("⚙️ 학습 설정")
st.sidebar.info("💡 **효주 님이 현우 님을 가르쳐주는 커플 학습 모드**")
user_level = st.sidebar.selectbox(
    "현우 님의 현재 일본어 레벨",
    ["입문/초급 (N5~N4)", "중급 (N3)", "상급 (N2~N1)"],
    index=0
)

st.title("🇯🇵 효주와 현우의 맞춤형 일본어 교실")
st.caption(f"현우 님 목표 레벨: **{user_level}** | 효주 님의 튜터링 가이드 탑재")

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 문장/이미지 분석", 
    "👩‍🏫 효주 님의 퀴즈 출제", 
    "💬 AI 대화 연습", 
    "⭐ 구분된 단어장", 
    "❌ 오답노트"
])

# ----- TAB 1: 문장 및 이미지 분석 (선생님 가이드 포함) -----
with tab1:
    sub_tab1, sub_tab2 = st.tabs(["📝 텍스트 입력", "📷 사진 업로드/촬영"])
    
    selected_text = ""
    uploaded_image = None

    with sub_tab1:
        selected_text = st.text_area("분석할 일본어 또는 한국어 문장/단어를 입력하세요", height=120)

    with sub_tab2:
        uploaded_image = st.file_uploader("이미지를 업로드하거나 카메라로 찍으세요", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="업로드된 이미지", use_column_width=True)

    prompt_instruction = f"""
    당신은 일본어를 잘하는 여자친구(효주)가 일본어를 배우는 남자친구(현우)를 가르쳐줄 때 돕는 스마트한 조교입니다.
    현우의 현재 일본어 수준은 [{user_level}]입니다.

    [중요 표기 규칙]
    - HTML 태그(예: <ruby>, <rt> 등)를 절대로 사용하지 마세요.
    - 한자의 읽는 법(후리가나)은 반드시 한자 뒤에 괄호를 사용하여 '한자(히라가나)' 형태로 표기하세요.

    1. **입력 내용이 한국어인 경우:**
       - [{user_level}] 수준에 어울리는 자연스러운 일본어로 번역해 주세요.
       - 번역된 일본어 한자는 '한자(히라가나)'와 [한글 발음]을 표기해 주세요.
       - 주요 단어와 문법을 설명해 주세요.

    2. **입력 내용이 일본어(텍스트 또는 이미지)인 경우:**
       - [원문 및 읽는 법]: 한자(히라가나) 형태와 [한글 발음] 표시
       - [단어 및 JLPT 난이도 분석]: 주요 단어 추출, 한자 음/훈독, JLPT 급수 표기, 뜻 풀이
       - [핵심 문법 포인트]: 주요 문법 요소 설명
       - [활용 예문]: 쉬운 예문 2개 (한글 번역 포함)

    3. **[👩‍🏫 효주 님을 위한 가르치기 팁]:**
       - 효주가 현우에게 이 단어나 문법을 설명해 줄 때 도움이 될 만한 포인트(예: 한국인이 자주 틀리는 발음, 실생활 뉘앙스 차이, 쉽게 기억하는 팁)를 2~3줄로 다정하게 적어주세요.
    """

    if st.button("✨ 상세 분석하기", type="primary", use_container_width=True):
        if not MY_API_KEY:
            st.error("API 키를 확인해 주세요!")
        else:
            with st.spinner("AI 조교가 단어와 문법, 가르치기 팁을 분석 중입니다..."):
                try:
                    client = genai.Client(api_key=MY_API_KEY)
                    
                    if uploaded_image is not None:
                        img = Image.open(uploaded_image)
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[prompt_instruction, img]
                        )
                    elif selected_text.strip():
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=f"{prompt_instruction}\n\n[분석할 텍스트]:\n{selected_text}"
                        )
                    else:
                        st.warning("분석할 텍스트를 입력하거나 이미지를 올려주세요.")
                        st.stop()

                    st.markdown("---")
                    st.markdown(response.text, unsafe_allow_html=True)

                    # 음성 듣기
                    if selected_text.strip():
                        st.markdown("### 🔊 음성 듣기")
                        tts = gTTS(text=selected_text, lang='ja')
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        st.audio(fp, format='audio/mp3')

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

# ----- TAB 2: 👩‍🏫 효주 님의 퀴즈 출제 -----
with tab2:
    st.subheader("👩‍🏫 현우 맞춤형 퀴즈 생성기")
    st.caption("효주 님이 공부시킬 단어나 문장을 넣으면, 현우 님이 풀어볼 수 있는 재미있는 퀴즈를 자동으로 만들어 드립니다!")

    quiz_input = st.text_input("퀴즈로 만들 일본어 단어나 문장을 입력하세요 (예: 勉強, 友達とご飯を食べます)")
    if st.button("🎲 퀴즈 생성하기"):
        if quiz_input.strip():
            with st.spinner("현우 맞춤 퀴즈를 만드는 중..."):
                try:
                    client = genai.Client(api_key=MY_API_KEY)
                    quiz_prompt = f"""
                    효주가 현우에게 낼 퀴즈를 만들어줘. 현우 수준: [{user_level}].
                    입력된 단어/문장: '{quiz_input}'
                    
                    구성:
                    1. [현우용 문제]: 4지선다 객관식 문제 1개 또는 빈칸 채우기 문제 1개 (정답 표기 금지)
                    2. [정답 및 효주용 해설]: 맨 아래에 접혀진 형태나 구분선 뒤에 정답과 간단한 해설 작성
                    """
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=quiz_prompt
                    )
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
        else:
            st.warning("단어나 문장을 입력해 주세요.")

# ----- TAB 3: AI 대화 연습 -----
with tab3:
    st.subheader("💬 AI 일본어 회화 챗봇")
    st.caption("현우 님과 효주 님 모두 자유롭게 대화해 보세요!")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if chat_input := st.chat_input("일본어로 메시지를 입력하세요..."):
        st.session_state.chat_history.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)

        with st.chat_message("assistant"):
            with st.spinner("답변 작성 중..."):
                try:
                    client = genai.Client(api_key=MY_API_KEY)
                    chat_prompt = f"""
                    너는 친절한 일본어 선생님이야. 사용자의 수준은 [{user_level}]이야.
                    문장의 틀린 부분을 다정하게 교정해주고, 일본어 답변과 한국어 번역을 같이 적어줘.
                    """
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=f"{chat_prompt}\n\n[사용자 메시지]: {chat_input}"
                    )
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# ----- TAB 4: ⭐ 구분된 단어장 (현우 / 효주 / 공동) -----
with tab4:
    st.subheader("⭐ 단어장")
    
    owner = st.radio("소유자 선택", ["👦 현우 단어장", "👩 효주 단어장", "👫 공동 단어장"], horizontal=True)

    with st.form("add_vocab_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_word = st.text_input("단어 (일본어)")
            new_meaning = st.text_input("뜻 (한국어)")
        with col2:
            new_reading = st.text_input("발음/읽는법 (히라가나)")
            new_memo = st.text_input("메모/가르침 팁")
        
        if st.form_submit_button(f"'{owner}'에 단어 추가"):
            if new_word and new_meaning:
                st.session_state.vocab_list.append({
                    "owner": owner, "word": new_word, "reading": new_reading, 
                    "meaning": new_meaning, "memo": new_memo
                })
                st.success(f"[{owner}]에 '{new_word}' 단어가 저장되었습니다!")
                st.rerun()

    st.markdown("---")
    
    # 선택된 소유자의 단어만 필터링해서 보여주기
    filtered_list = [item for item in st.session_state.vocab_list if item.get("owner") == owner]
    
    if not filtered_list:
        st.info(f"[{owner}]에 저장된 단어가 없습니다.")
    else:
        for idx, item in enumerate(st.session_state.vocab_list):
            if item.get("owner") == owner:
                col_a, col_b, col_c = st.columns([3, 4, 1])
                with col_a:
                    st.write(f"**{item['word']}** ({item['reading']})")
                with col_b:
                    st.write(f"{item['meaning']} | *{item['memo']}*")
                with col_c:
                    if st.button("삭제", key=f"del_v_{idx}"):
                        st.session_state.vocab_list.pop(idx)
                        st.rerun()

# ----- TAB 5: ❌ 오답노트 -----
with tab5:
    st.subheader("❌ 오답노트")
    st.caption("현우 님이 자주 헷갈리는 문법이나 표현을 효주 님과 함께 정리해보세요.")
    
    with st.form("add_wrong_form"):
        w_item = st.text_input("틀린 문장/단어")
        w_correct = st.text_input("올바른 표현/해설")
        w_reason = st.text_area("틀린 이유 & 효주 님의 조언")
        
        if st.form_submit_button("오답 노트 추가"):
            if w_item and w_correct:
                st.session_state.wrong_notes.append({
                    "item": w_item, "correct": w_correct, "reason": w_reason
                })
                st.success("오답 노트에 저장되었습니다!")
                st.rerun()

    st.markdown("---")
    if not st.session_state.wrong_notes:
        st.info("기록된 오답이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state.wrong_notes):
            with st.expander(f"📌 {item['item']}"):
                st.write(f"**정답/해설:** {item['correct']}")
                st.write(f"**효주 님의 조언:** {item['reason']}")
                if st.button("복습 완료 (삭제)", key=f"del_w_{idx}"):
                    st.session_state.wrong_notes.pop(idx)
                    st.rerun()
