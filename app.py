import streamlit as st
import pandas as pd
import os
import random
import time
import eng_to_ipa as ipa # 発音記号用ライブラリ

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 関数定義
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE): 
        return [{"word": "Start", "meaning": "開始", "miss_count": 0}]
    try:
        # nan（空データ）を0に変換して読み込む
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        df['miss_count'] = df['miss_count'].fillna(0).astype(int)
        return df.to_dict('records')
    except:
        return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# ブラウザ読み上げ用HTML
def get_browser_speech_html(text, unique_id):
    safe_text = text.replace("'", "\\'").replace('"', '\\"')
    return f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <script>
            function speak_{unique_id}() {{
                const utter = new SpeechSynthesisUtterance('{safe_text}');
                utter.lang = 'en-US';
                utter.rate = 1.0; 
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utter);
            }}
            setTimeout(speak_{unique_id}, 50);
        </script>
        <button onclick="speak_{unique_id}()" style="
            background-color: #3498db; color: white; border: none;
            padding: 8px 20px; border-radius: 20px; font-size: 14px;
            font-weight: bold; cursor: pointer; margin-top: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        ">
            🔊 音声を再生
        </button>
    </div>
    """

# ★答えの箱用HTML（強制リセット機能付き）
def get_details_html(meaning, word, miss_count, unique_id):
    # unique_id をIDに埋め込むことで、ブラウザに「新しい要素」と認識させる
    return f"""
    <style>
        details {{
            background-color: #f0f2f6; padding: 15px; border-radius: 10px;
            margin-bottom: 20px; border: 1px solid #d1d5db;
        }}
        summary {{
            cursor: pointer; font-weight: bold; font-size: 18px;
            color: #333; text-align: center;
        }}
        .content {{ margin-top: 15px; text-align: center; }}
        .meaning-text {{ font-size: 24px; color: #e74c3c; font-weight: bold; }}
        .miss-text {{ color: red; font-size: 14px; margin-top: 5px; }}
        .dict-link a {{ color: #3498db; text-decoration: none; font-weight: bold; }}
    </style>
    
    <details id="details_{unique_id}">
        <summary>👁️ 答えを確認する (タップ)</summary>
        <div class="content">
            <div class="meaning-text">{meaning}</div>
            <div class="miss-text">過去のミス: {miss_count}回</div>
            <div class="dict-link">
                <br>
                <a href="https://dictionary.cambridge.org/ja/dictionary/english/{word}" target="_blank">📖 辞書で見る</a>
            </div>
        </div>
    </details>
    """

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Wordbook v20", layout="centered")

st.markdown("""
<style>
    .stButton>button {
        height: 3.5em; font-weight: bold; border-radius: 12px; width: 100%;
        font-size: 18px !important;
    }
    .big-word {
        font-size: 42px !important; text-align: center; color: #2c3e50;
        margin: 5px 0; font-weight: 800;
    }
    .phonetic {
        font-size: 20px !important; text-align: center; color: #7f8c8d;
        margin-bottom: 15px; font-family: "Lucida Sans Unicode", "Arial Unicode MS", sans-serif;
    }
    .step-indicator { text-align: center; color: gray; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("📱 My Wordbook")

if 'vocab_list' not in st.session_state: st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state: st.session_state.study_queue = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'study_mode' not in st.session_state: st.session_state.study_mode = False

tab1, tab2 = st.tabs(["📚 学習", "✏️ 登録"])

# ---------------------------------------------------------
# タブ1: 学習
# ---------------------------------------------------------
with tab1:
    if not st.session_state.study_mode:
        st.info("設定を選んでスタート")
        col1, col2 = st.columns(2)
        with col1:
            filter_mode = st.radio("対象", ["すべて", "苦手のみ (Miss≧1)"])
        with col2:
            order_mode = st.radio("順番", ["番号順", "ランダム"])
        
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
            
            # ★新機能: 発音記号表示
            ipa_text = ipa.convert(data['word'])
            # *がついている場合は変換失敗なので隠すなどの処理も可能ですが、一旦そのまま表示
            st.markdown(f"<div class='phonetic'>/{ipa_text}/</div>", unsafe_allow_html=True)

            # 2. 音声再生
            unique_id = int(time.time() * 1000)
            html_code = get_browser_speech_html(data['word'], unique_id)
            st.components.v1.html(html_code, height=70)

            # 3. 答えの箱 (IDを変えて強制リセット)
            details_html = get_details_html(data['meaning'], data['word'], data['miss_count'], unique_id)
            st.markdown(details_html, unsafe_allow_html=True)

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
            # 欠損値対策
            for d in new_list:
                if pd.isna(d['miss_count']) or d['miss_count'] == '':
                    d['miss_count'] = 0
            
            new_list = [d for d in new_list if d['word'] and d['meaning']]
            st.session_state.vocab_list = new_list
            save_data(new_list)
            st.success("更新しました")
