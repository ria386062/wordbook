import streamlit as st
import pandas as pd
import os
import random
import time
import eng_to_ipa as ipa # 発音記号用

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 関数定義
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE): 
        return [{"word": "Start", "meaning": "開始", "miss_count": 0}]
    try:
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        # データクリーニング: nanを0に
        df['miss_count'] = pd.to_numeric(df['miss_count'], errors='coerce').fillna(0).astype(int)
        return df.to_dict('records')
    except:
        return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# ★改良版: 高音質ボイス指定機能付き
def get_browser_speech_html(text, unique_id):
    safe_text = text.replace("'", "\\'").replace('"', '\\"')
    return f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <script>
            function speak_{unique_id}() {{
                // 1. まず利用可能な声を全部リストアップする
                let voices = window.speechSynthesis.getVoices();
                
                // 2. 声がロードされていない場合(iOSなど)のための待機処理
                if (voices.length === 0) {{
                    window.speechSynthesis.onvoiceschanged = function() {{
                        voices = window.speechSynthesis.getVoices();
                        doSpeak_{unique_id}(voices);
                    }};
                }} else {{
                    doSpeak_{unique_id}(voices);
                }}
            }}

            function doSpeak_{unique_id}(voices) {{
                const utter = new SpeechSynthesisUtterance('{safe_text}');
                utter.lang = 'en-US';
                utter.rate = 1.0; 
                utter.pitch = 1.0;

                // ★ここが新機能: より良い声を探すロジック
                // "Samantha"(iOSの高音質版) や "Google US"(Android) を優先的に探す
                const bestVoice = voices.find(v => 
                    (v.lang === 'en-US' && (v.name.includes('Samantha') || v.name.includes('Premium') || v.name.includes('Enhanced'))) 
                    || (v.lang === 'en-US' && v.name.includes('Google'))
                );
                
                // 見つかったらセットする
                if (bestVoice) {{
                    utter.voice = bestVoice;
                    console.log("Selected voice: " + bestVoice.name);
                }}

                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utter);
            }}
            
            // 画面が開いたら実行
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

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Wordbook v22", layout="centered")

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
        margin-bottom: 15px; font-family: sans-serif;
    }
    .step-indicator { text-align: center; color: gray; margin-bottom: 5px; }
    .answer-box {
        text-align: center; background-color: #f0f2f6;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    .meaning-text { font-size: 26px; color: #e74c3c; font-weight: bold; }
    .miss-text { color: red; font-size: 14px; margin-top: 5px; }
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
            
            # 発音記号
            try:
                ipa_text = ipa.convert(data['word'])
                st.markdown(f"<div class='phonetic'>/{ipa_text}/</div>", unsafe_allow_html=True)
            except:
                pass 

            # 2. 音声再生 (高音質指定)
            unique_id = int(time.time() * 1000)
            html_code = get_browser_speech_html(data['word'], unique_id)
            st.components.v1.html(html_code, height=70)

            # 3. 答えの箱 (強制リセット)
            label_suffix = " " * (idx % 2) 
            expander_label = f"👁️ 答えを確認する (タップ){label_suffix}"
            
            with st.expander(expander_label, expanded=False):
                st.markdown(f"""
                <div class="answer-box">
                    <div class="meaning-text">{data['meaning']}</div>
                    <div class="miss-text">過去のミス: {data['miss_count']}回</div>
                    <br>
                    <a href="https://dictionary.cambridge.org/ja/dictionary/english/{data['word']}" target="_blank">📖 辞書で見る</a>
                </div>
                """, unsafe_allow_html=True)

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
            for d in new_list:
                if pd.isna(d['miss_count']) or d['miss_count'] == '':
                    d['miss_count'] = 0
            
            new_list = [d for d in new_list if d['word'] and d['meaning']]
            st.session_state.vocab_list = new_list
            save_data(new_list)
            st.success("更新しました")
