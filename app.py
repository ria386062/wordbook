import streamlit as st
import pandas as pd
import os
import random
import time

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 関数定義
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE): 
        return [{"word": "Start", "meaning": "開始", "miss_count": 0}]
    try:
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        return df.to_dict('records')
    except:
        return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# ★ここが新技術: Pythonではなく、ブラウザ(JavaScript)に喋らせるHTMLを作る
def get_browser_speech_html(text, unique_id):
    # エスケープ処理（単語の中に ' があるとJSが壊れるため）
    safe_text = text.replace("'", "\\'")
    
    return f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <script>
            function speak_{unique_id}() {{
                // スマホの読み上げ機能を呼び出す
                const utter = new SpeechSynthesisUtterance('{safe_text}');
                utter.lang = 'en-US'; // 英語設定
                utter.rate = 1.0;     // 速度
                window.speechSynthesis.cancel(); // 前のを止める
                window.speechSynthesis.speak(utter);
            }}
            
            // 画面が開いた瞬間に再生を試みる
            // (少し遅らせることで安定させる)
            setTimeout(speak_{unique_id}, 300);
        </script>
        
        <button onclick="speak_{unique_id}()" style="
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        ">
            🔊 音声を再生 (Speak)
        </button>
    </div>
    """

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Wordbook v17", layout="centered")

# CSS
st.markdown("""
<style>
    .stButton>button {
        height: 3.5em; font-weight: bold; border-radius: 12px; width: 100%;
    }
    .big-word {
        font-size: 42px !important; text-align: center; color: #2c3e50;
        margin: 20px 0 10px 0; font-weight: 800;
    }
    .big-meaning {
        font-size: 28px !important; text-align: center; color: #e74c3c;
        font-weight: bold; padding: 20px; background-color: #fff5f5;
        border-radius: 15px; border: 2px solid #ffcccc; margin-bottom: 20px;
    }
    .step-indicator { text-align: center; color: gray; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("📱 My Wordbook")

if 'vocab_list' not in st.session_state: st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state: st.session_state.study_queue = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'study_mode' not in st.session_state: st.session_state.study_mode = False

# タブ
tab1, tab2 = st.tabs(["📚 学習 (Study)", "✏️ 登録 (Add)"])

# ---------------------------------------------------------
# タブ1: 学習
# ---------------------------------------------------------
with tab1:
    if not st.session_state.study_mode:
        st.info("設定を選んでスタート")
        col1, col2 = st.columns(2)
        with col1:
            filter_mode = st.radio("出題対象", ["すべて", "苦手のみ (Miss≧1)"])
        with col2:
            order_mode = st.radio("出題順", ["番号順", "ランダム"])
        
        if st.button("▶ 学習スタート", type="primary"):
            target_list = st.session_state.vocab_list.copy()
            if filter_mode == "苦手のみ (Miss≧1)":
                target_list = [w for w in target_list if w["miss_count"] >= 1]
            
            if not target_list:
                st.error("単語がありません")
            else:
                if order_mode == "ランダム": random.shuffle(target_list)
                st.session_state.study_queue = target_list
                st.session_state.current_index = 0
                st.session_state.study_mode = True
                st.rerun()

    else:
        queue = st.session_state.study_queue
        idx = st.session_state.current_index
        total = len(queue)
        
        if idx < total:
            data = queue[idx]
            
            st.progress((idx + 1) / total)
            st.markdown(f"<div class='step-indicator'>Card {idx + 1} / {total}</div>", unsafe_allow_html=True)
            
            # 1. 単語表示
            st.markdown(f"<div class='big-word'>{data['word']}</div>", unsafe_allow_html=True)

            # 2. 音声再生 (JavaScript方式)
            # サーバーでファイルを作らず、スマホに直接命令を出します
            # 毎回IDを変えて再実行させる
            unique_id = int(time.time() * 1000)
            html_code = get_browser_speech_html(data['word'], unique_id)
            st.components.v1.html(html_code, height=60)

            st.write("") 

            # 3. 答えの箱
            with st.expander("👁️ 答えを確認する (タップ)", expanded=False):
                st.markdown(f"<div class='big-meaning'>{data['meaning']}</div>", unsafe_allow_html=True)
                if data['miss_count'] > 0:
                    st.markdown(f"<p style='text-align:center; color:red;'>ミス回数: {data['miss_count']}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;'><a href='https://dictionary.cambridge.org/ja/dictionary/english/{data['word']}' target='_blank'>📖 辞書リンク</a></div>", unsafe_allow_html=True)

            st.write("") 

            # 4. 判定ボタン
            col_ok, col_ng = st.columns(2)
            with col_ok:
                if st.button("🙆 正解 (Next)", type="primary"):
                    st.session_state.current_index += 1
                    st.rerun()
            with col_ng:
                if st.button("🙅 不正解 (Miss)"):
                    word_to_update = data['word']
                    for item in st.session_state.vocab_list:
                        if item['word'] == word_to_update:
                            item['miss_count'] += 1
                    save_data(st.session_state.vocab_list)
                    st.session_state.current_index += 1
                    st.rerun()

            st.divider()
            if st.button("メニューに戻る"):
                st.session_state.study_mode = False
                st.rerun()

        else:
            st.success("🎉 学習完了！")
            st.balloons()
            if st.button("メニューへ戻る", type="primary"):
                st.session_state.study_mode = False
                st.rerun()

# ---------------------------------------------------------
# タブ2: 登録
# ---------------------------------------------------------
with tab2:
    st.header("単語登録")
    with st.form("add_form", clear_on_submit=True):
        new_word = st.text_input("英単語")
        new_meaning = st.text_input("意味")
        submitted = st.form_submit_button("追加する", type="primary")
        if submitted:
            if new_word and new_meaning:
                st.session_state.vocab_list.append({"word": new_word, "meaning": new_meaning, "miss_count": 0})
                save_data(st.session_state.vocab_list)
                st.success(f"「{new_word}」を追加しました")
    
    with st.expander("📋 リスト編集"):
        df = pd.DataFrame(st.session_state.vocab_list)
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
        if st.button("変更を保存"):
            new_list = edited_df.to_dict('records')
            new_list = [d for d in new_list if d['word'] and d['meaning']]
            st.session_state.vocab_list = new_list
            save_data(new_list)
            st.success("更新しました")
