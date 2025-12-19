import streamlit as st
import pandas as pd
from gtts import gTTS
import os
import tempfile
import random
import base64

DATA_FILE = "my_wordbook.csv"

# --- データ読み込み・保存 ---
def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        return df.to_dict('records')
    except: return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# --- 音声自動再生の魔法の関数 ---
def autoplay_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            # バイナリデータを読み込んでBase64エンコード
            with open(fp.name, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                
                # HTMLの<audio autoplay>タグを埋め込む
                md = f"""
                    <audio autoplay>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                    """
                st.markdown(md, unsafe_allow_html=True)
    except:
        pass

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
    
    with st.expander("📝 単語を追加"):
        new_word = st.text_input("単語")
        new_meaning = st.text_input("意味")
        if st.button("追加"):
            if new_word and new_meaning:
                st.session_state.vocab_list.append({"word": new_word, "meaning": new_meaning, "miss_count": 0})
                save_data(st.session_state.vocab_list)
                st.success(f"Added: {new_word}")

    st.divider()
    filter_mode = st.radio("出題対象", ["すべて", "苦手のみ (Miss≧1)"])
    order_mode = st.radio("順番", ["番号順", "ランダム"])
    
    if st.button("▶ 学習スタート / リセット", type="primary"):
        target_list = st.session_state.vocab_list.copy()
        if filter_mode == "苦手のみ (Miss≧1)":
            target_list = [w for w in target_list if w["miss_count"] >= 1]
        
        if not target_list:
            st.error("No words found!")
        else:
            if order_mode == "ランダム": random.shuffle(target_list)
            st.session_state.study_queue = target_list
            st.session_state.current_index = 0
            st.session_state.show_answer = False
            st.session_state.study_mode = True
            st.rerun()

    # データ一覧
    if st.checkbox("データ一覧を表示"):
        st.dataframe(pd.DataFrame(st.session_state.vocab_list))

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
            <h1 style="color:#2c3e50; font-size: 40px;">{data['word']}</h1>
        </div>
        """, unsafe_allow_html=True)

        # ★自動再生（答えを見ていない＝問題が出た瞬間に再生）
        # ※ブラウザの設定によっては初回再生のみブロックされることがあります
        if not st.session_state.show_answer:
            autoplay_audio(data['word'])

        # ミスバッジ
        if data['miss_count'] > 0:
            st.markdown(f"<div style='text-align:right; color:red;'><b>⚠️ Miss: {data['miss_count']}</b></div>", unsafe_allow_html=True)

        st.markdown("---")

        # 操作エリア
        if not st.session_state.show_answer:
            # 答えを見るボタン（大きく押しやすく）
            if st.button("答えを見る (Show Answer)", use_container_width=True, type="primary"):
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
                if st.button("🙆 分かる (Next)", use_container_width=True):
                    st.session_state.current_index += 1
                    st.session_state.show_answer = False
                    st.rerun()
            with col2:
                if st.button("🙅 分からない (Miss)", use_container_width=True):
                    # ミス回数更新
                    word_to_update = data['word']
                    for item in st.session_state.vocab_list:
                        if item['word'] == word_to_update:
                            item['miss_count'] += 1
                    save_data(st.session_state.vocab_list)
                    
                    st.session_state.current_index += 1
                    st.session_state.show_answer = False
                    st.rerun()
            
            # 辞書リンク
            st.markdown(f"[🌍 Cambridge Dictionaryで確認](https://dictionary.cambridge.org/ja/dictionary/english/{data['word']})")

    else:
        st.balloons()
        st.success("🎉 学習完了！お疲れ様でした！")
        if st.button("トップに戻る"):
            st.session_state.study_mode = False
            st.rerun()

else:
    st.info("👈 左のメニューから学習を開始してください")
