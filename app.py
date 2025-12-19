import streamlit as st
import pandas as pd
from gtts import gTTS
import os
from io import BytesIO
import random
import base64

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 高速化のための関数 (キャッシュ利用)
# ==========================================

# データ読み込みをキャッシュ（毎回ファイルを開かない）
def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        return df.to_dict('records')
    except: return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# ★重要: 音声生成をキャッシュして高速化
# 同じ単語ならGoogleに通信せず、メモリから即座に返す
@st.cache_data(show_spinner=False)
def get_audio_bytes(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.getvalue()
    except:
        return None

# 自動再生用のHTML生成
def get_autoplay_html(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    return f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Smart Wordbook", layout="centered")
st.title("📱 My Smart Wordbook")

# セッション状態の初期化
if 'vocab_list' not in st.session_state: st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state: st.session_state.study_queue = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'show_answer' not in st.session_state: st.session_state.show_answer = False
if 'study_mode' not in st.session_state: st.session_state.study_mode = False

# --- サイドバー：設定 ---
with st.sidebar:
    st.header("⚙️ Menu")
    
    # ★改善: 入力フォームを使って自動リセット
    with st.expander("📝 単語を追加", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            new_word = st.text_input("単語")
            new_meaning = st.text_input("意味")
            submitted = st.form_submit_button("追加")
            
            if submitted:
                if new_word and new_meaning:
                    st.session_state.vocab_list.append({"word": new_word, "meaning": new_meaning, "miss_count": 0})
                    save_data(st.session_state.vocab_list)
                    st.success(f"Added: {new_word}")
                else:
                    st.warning("単語と意味を入力してください")

    st.divider()
    filter_mode = st.radio("出題対象", ["すべて", "苦手のみ (Miss≧1)"])
    order_mode = st.radio("順番", ["番号順", "ランダム"])
    
    if st.button("▶ 学習スタート / リセット", type="primary", use_container_width=True):
        target_list = st.session_state.vocab_list.copy()
        if filter_mode == "苦手のみ (Miss≧1)":
            target_list = [w for w in target_list if w["miss_count"] >= 1]
        
        if not target_list:
            st.error("単語が見つかりません！")
        else:
            if order_mode == "ランダム": random.shuffle(target_list)
            st.session_state.study_queue = target_list
            st.session_state.current_index = 0
            st.session_state.show_answer = False
            st.session_state.study_mode = True
            st.rerun()

    if st.checkbox("データ一覧を表示"):
        st.dataframe(pd.DataFrame(st.session_state.vocab_list), use_container_width=True)

# --- メインエリア ---
if st.session_state.study_mode and st.session_state.study_queue:
    idx = st.session_state.current_index
    total = len(st.session_state.study_queue)
    
    if idx < total:
        data = st.session_state.study_queue[idx]
        
        # 進捗
        st.caption(f"Question {idx + 1} / {total}")
        st.progress((idx + 1) / total)

        # 単語カード
        st.markdown(f"""
        <div style="background-color:#ffffff; padding:30px; border-radius:15px; text-align:center; border: 2px solid #f0f2f6; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color:#2c3e50; font-size: 40px; margin:0;">{data['word']}</h1>
        </div>
        """, unsafe_allow_html=True)

        # ★改善: 音声データの取得（キャッシュ利用で高速化）
        audio_bytes = get_audio_bytes(data['word'])

        # 1. 自動再生（初回のみ）
        if not st.session_state.show_answer and audio_bytes:
            # HTML埋め込みで自動再生させる
            st.markdown(get_autoplay_html(audio_bytes), unsafe_allow_html=True)
        
        # 2. 手動再生プレイヤー（★ここを追加しました！）
        # これがあれば、いつでも再生ボタンを押して聞き直せます
        if audio_bytes:
            st.audio(audio_bytes, format='audio/mp3')

        # ミスバッジ
        if data['miss_count'] > 0:
            st.markdown(f"<div style='text-align:right; color:red; margin-top:5px;'><b>⚠️ Miss: {data['miss_count']}</b></div>", unsafe_allow_html=True)

        st.markdown("---")

        # 操作エリア
        if not st.session_state.show_answer:
            if st.button("答えを見る", use_container_width=True, type="primary"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            # 答え表示
            st.markdown(f"""
            <div style="text-align:center; margin-bottom:20px;">
                <h2 style="color:#2ecc71;">{data['meaning']}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🙆 分かる", use_container_width=True):
                    st.session_state.current_index += 1
                    st.session_state.show_answer = False
                    st.rerun()
            with col2:
                if st.button("🙅 分からない", use_container_width=True):
                    # ミス回数更新
                    word_to_update = data['word']
                    for item in st.session_state.vocab_list:
                        if item['word'] == word_to_update:
                            item['miss_count'] += 1
                    save_data(st.session_state.vocab_list)
                    
                    st.session_state.current_index += 1
                    st.session_state.show_answer = False
                    st.rerun()
            
            st.markdown(f"[🌍 Cambridge Dictionaryで確認](https://dictionary.cambridge.org/ja/dictionary/english/{data['word']})")

    else:
        st.balloons()
        st.success("🎉 学習完了！お疲れ様でした！")
        if st.button("トップに戻る", type="primary"):
            st.session_state.study_mode = False
            st.rerun()

else:
    st.info("👈 左のメニューから学習を開始してください")
