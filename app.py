# full_random_mode_shuffle_mode_verified_final_with_image_edit_reset_progress.py
# Đã cập nhật:
# - Thêm chức năng lọc câu chưa có CodeTopic
# - Thêm chức năng paste hình ảnh vào note từ clipboard (Ctrl+V)
# - Điều chỉnh vị trí các nút điều hướng
# - Giữ nguyên tất cả chức năng hiện có

import pandas as pd
import streamlit as st
import random
import re
import os
import time
from PIL import Image, ImageGrab
import io
import base64
import pyperclip


@st.cache_data(ttl=0)
def load_sheets(path):
    xls = pd.ExcelFile(path)
    return {sheet: xls.parse(sheet).assign(SheetName=sheet) for sheet in xls.sheet_names}


def reload_excel():
    global all_sheets, df_all
    all_sheets = load_sheets(excel_file)
    df_all = pd.concat(
        [df for name, df in all_sheets.items() if "All" in selected_sheets or name in selected_sheets],
        ignore_index=True
    )


def show_progress_in_sidebar(total, current, mode, key_prefix=""):
    """Hiển thị tiến độ trong sidebar"""
    with st.sidebar:
        st.markdown("### 📊 Tiến độ làm đề")
        st.write(f"Câu hiện tại: {current + 1} / {total}")

        jump_to = st.number_input(
            "Nhập số câu muốn chuyển đến:",
            min_value=1,
            max_value=total,
            value=current + 1,
            step=1,
            key=f"{key_prefix}_jump_to"
        )

        if jump_to != current + 1:
            st.session_state[f"{key_prefix}_index"] = jump_to - 1
            st.rerun()


def show_navigation_buttons(total, current, mode, key_prefix=""):
    """Hiển thị các nút điều hướng"""
    cols = st.columns(5)
    with cols[0]:
        if st.button("⏮ Câu đầu", key=f"{key_prefix}_first"):
            st.session_state[f"{key_prefix}_index"] = 0
            st.rerun()
    with cols[1]:
        if st.button("◀️ Lùi lại", key=f"{key_prefix}_prev"):
            st.session_state[f"{key_prefix}_index"] = max(0, current - 1)
            st.rerun()
    with cols[2]:
        if st.button("▶️ Tiếp theo", key=f"{key_prefix}_next"):
            st.session_state[f"{key_prefix}_index"] = min(total - 1, current + 1)
            st.rerun()
    with cols[3]:
        if st.button("⏭ Câu cuối", key=f"{key_prefix}_last"):
            st.session_state[f"{key_prefix}_index"] = total - 1
            st.rerun()
    with cols[4]:
        if mode == "Ngẫu nhiên 1 câu" and st.button('🔀 Random', key=f"{key_prefix}_random"):
            st.session_state[f"{key_prefix}_index"] = random.randint(0, total - 1)
            st.rerun()


def display_note_with_images(note_text, image_folder):
    if not note_text or pd.isna(note_text):
        return ""

    # Split note into lines
    lines = note_text.split('\n')

    for line in lines:
        # Check for image markdown syntax ![alt](path)
        if line.strip().startswith('![') and '](' in line and line.endswith(')'):
            try:
                alt_text = line.split('![')[1].split(']')[0]
                img_path = line.split('](')[1][:-1]
                full_path = os.path.join(image_folder, img_path)

                if os.path.exists(full_path):
                    st.image(full_path, caption=alt_text, use_container_width=True)
                else:
                    st.warning(f"Không tìm thấy hình ảnh: {img_path}")
            except:
                st.write(line)
        else:
            st.write(line)


# --- PHẦN NHẬP ĐƯỜNG DẪN FILE EXCEL ---
st.sidebar.title("Tuỳ chọn")
excel_path = st.sidebar.text_input(
    "📁 Dán đường dẫn file Excel (.xlsx):",
    help="Ví dụ: C:/Users/name/Documents/ngan_hang_cau_hoi.xlsx"
)

# Kiểm tra file hợp lệ
if not excel_path:
    st.warning("⚠️ Vui lòng nhập đường dẫn file Excel.")
    st.stop()

if not excel_path.endswith('.xlsx'):
    st.error("❌ File phải có định dạng .xlsx")
    st.stop()

if not os.path.isfile(excel_path):
    st.error(f"⛔ Không tìm thấy file tại: {excel_path}")
    st.stop()

# Thiết lập đường dẫn
excel_file = excel_path
image_folder = os.path.join(os.path.dirname(excel_file), "images")

# Kiểm tra thư mục hình ảnh
if not os.path.exists(image_folder):
    st.sidebar.warning(f"⚠️ Không tìm thấy thư mục hình ảnh tại: {image_folder}")
    os.makedirs(image_folder, exist_ok=True)

# Load dữ liệu từ file Excel
try:
    all_sheets = load_sheets(excel_file)
except Exception as e:
    st.error(f"❌ Lỗi khi đọc file Excel: {str(e)}")
    st.stop()

# --- PHẦN CHỌN LỌC VÀ HIỂN THỊ ---
sheet_options = ['All'] + list(all_sheets.keys())
selected_sheets = st.sidebar.multiselect("Chọn slide:", sheet_options, default=["All"])

if not selected_sheets:
    st.warning("⚠️ Chưa chọn sheet.")
    st.stop()

if st.sidebar.button("🔄 Tải lại file Excel"):
    reload_excel()
    st.rerun()

selected_df = pd.concat([df for name, df in all_sheets.items() if "All" in selected_sheets or name in selected_sheets])

# Thêm option "Chưa có CodeTopic" vào bộ lọc
available_topics = selected_df["CodeTopic"].dropna().unique().tolist()
topic_options = ['All', 'Chưa có CodeTopic'] + sorted(available_topics)
selected_topics = st.sidebar.multiselect("Chọn CodeTopic:", topic_options, default=["All"])

search_term = st.sidebar.text_input("Tìm từ khoá trong Original:").strip()
search_question = st.sidebar.text_input("Tìm trong nội dung câu hỏi:").strip()
search_note = st.sidebar.text_input("Tìm trong ghi chú:").strip()
mode = st.sidebar.selectbox("Chế độ hiển thị câu hỏi:", [
    "Ngẫu nhiên 1 câu",
    "Tăng dần theo Original",
    "Giảm dần theo Original",
    "Toàn bộ không sắp xếp",
    "Theo thứ tự trong file Excel",
    "Xáo trộn đề - 1 câu"
], index=1)

st.session_state.setdefault("show_note", False)
st.session_state.show_note = st.sidebar.checkbox("📝 Hiện ghi chú", value=st.session_state.show_note)

df_all = pd.concat(
    [df for name, df in all_sheets.items() if "All" in selected_sheets or name in selected_sheets],
    ignore_index=True
)

# Xử lý bộ lọc CodeTopic với option "Chưa có CodeTopic"
if "All" in selected_topics:
    df = df_all
elif "Chưa có CodeTopic" in selected_topics:
    # Lấy các câu chưa có CodeTopic
    df_no_topic = df_all[df_all["CodeTopic"].isna()]
    # Lấy các câu có CodeTopic nếu có chọn thêm các topic khác
    other_topics = [t for t in selected_topics if t != "Chưa có CodeTopic"]
    if other_topics:
        df_with_topic = df_all[df_all["CodeTopic"].isin(other_topics)]
        df = pd.concat([df_no_topic, df_with_topic])
    else:
        df = df_no_topic
else:
    df = df_all[df_all["CodeTopic"].isin(selected_topics)]

# Áp dụng các bộ lọc khác
if search_term:
    df = df[df['Original'].astype(str).str.contains(search_term, case=False, na=False)]
if search_question:
    df = df[df['Question'].astype(str).str.contains(search_question, case=False, na=False)]
if search_note:
    df = df[df['Note'].astype(str).str.contains(search_note, case=False, na=False)]

# Xử lý reset index khi filter thay đổi
current_filter = (tuple(selected_sheets), tuple(selected_topics), search_term, search_question, search_note, mode)
if st.session_state.get("last_filter_hash") != hash(current_filter):
    for key in list(st.session_state.keys()):
        if key.endswith("_show_answer") or key.endswith("_edit_mode") or key.endswith("_last") or key.endswith(
                "_edit_answer"):
            del st.session_state[key]

    # Reset index cho tất cả các mode khi filter thay đổi
    if mode == "Xáo trộn đề - 1 câu":
        st.session_state.shuffled_index = 0
    elif mode == "Ngẫu nhiên 1 câu":
        st.session_state.random_index = 0
    elif mode in ["Tăng dần theo Original", "Giảm dần theo Original"]:
        st.session_state.sorted_index = 0
    elif mode == "Theo thứ tự trong file Excel":
        st.session_state.excel_index = 0

    st.session_state.last_filter_hash = hash(current_filter)

if df.empty:
    st.warning("Không có câu hỏi phù hợp.")
    st.stop()

# Kiểm tra nếu mode thay đổi
if st.session_state.get("last_mode") != mode:
    # Reset index cho mode mới
    if mode == "Xáo trộn đề - 1 câu":
        st.session_state.shuffled_index = 0
    elif mode == "Ngẫu nhiên 1 câu":
        st.session_state.random_index = 0
    elif mode in ["Tăng dần theo Original", "Giảm dần theo Original"]:
        st.session_state.sorted_index = 0
    elif mode == "Theo thứ tự trong file Excel":
        st.session_state.excel_index = 0

# --- XỬ LÝ CÁC CHẾ ĐỘ HIỂN THỊ ---
if mode == "Xáo trộn đề - 1 câu":
    filter_hash = hash((tuple(selected_sheets), tuple(selected_topics), search_term, search_question, search_note))
    if st.session_state.get("shuffled_filter_hash") != filter_hash or "shuffled_questions" not in st.session_state:
        st.session_state.shuffled_questions = df.sample(frac=1, random_state=random.randint(0, 99999)).to_dict(
            orient="records")
        st.session_state.shuffled_index = 0
        st.session_state.shuffled_filter_hash = filter_hash
        st.session_state.original_shuffled_order = [q['Original'] for q in st.session_state.shuffled_questions]

    questions = [st.session_state.shuffled_questions[st.session_state.shuffled_index]]
    show_progress_in_sidebar(len(st.session_state.shuffled_questions), st.session_state.shuffled_index, mode,
                             "shuffled")

elif mode == "Ngẫu nhiên 1 câu":
    if "random_index" not in st.session_state:
        st.session_state.random_index = 0
    df_sorted = df
    questions = [df_sorted.iloc[st.session_state.random_index].to_dict()]
    show_progress_in_sidebar(len(df_sorted), st.session_state.random_index, mode, "random")

elif mode in ["Tăng dần theo Original", "Giảm dần theo Original"]:
    ascending = mode == "Tăng dần theo Original"
    df_sorted = df.sort_values(by='Original', ascending=ascending).reset_index(drop=True)
    if "sorted_index" not in st.session_state:
        st.session_state.sorted_index = 0
    questions = [df_sorted.iloc[st.session_state.sorted_index].to_dict()]
    show_progress_in_sidebar(len(df_sorted), st.session_state.sorted_index, mode, "sorted")

elif mode == "Theo thứ tự trong file Excel":
    df_sorted = df.reset_index(drop=True)
    if "excel_index" not in st.session_state:
        st.session_state.excel_index = 0
    questions = [df_sorted.iloc[st.session_state.excel_index].to_dict()]
    show_progress_in_sidebar(len(df_sorted), st.session_state.excel_index, mode, "excel")

else:  # Toàn bộ không sắp xếp
    df_sorted = df.reset_index(drop=True)
    questions = df_sorted.to_dict(orient='records')

# --- HIỂN THỊ CÂU HỎI VÀ CÁC CHỨC NĂNG CHỈNH SỬA ---
st.session_state.last_mode = mode
st.title("Luyện đề trắc nghiệm")

for i, q in enumerate(questions):
    oid = str(q['Original'])
    sheet = q.get('SheetName', selected_sheets[0] if selected_sheets else '')
    row_id = f"{sheet}_{oid}_{i}"

    st.markdown(f"### @ {oid}")
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        st.markdown(f"📂 **CodeTopic:** <span style='color:limegreen'>{q.get('CodeTopic', '')}</span>",
                    unsafe_allow_html=True)
    with col2:
        if st.button("Sửa đề", key=row_id + '_edit_original_btn'):
            st.session_state[row_id + '_edit_original'] = True
    with col3:
        if st.button("Sửa Topic", key=row_id + '_edit_topic_btn'):
            st.session_state[row_id + '_edit_topic'] = True
    with col4:
        if st.button("Sửa câu hỏi", key=row_id + '_edit_ques_btn'):
            st.session_state[row_id + '_edit_question'] = True
    with col5:
        if st.button("Sửa hình", key=row_id + '_edit_image_btn'):
            st.session_state[row_id + '_edit_image'] = True

    # ========== CHỈNH SỬA ORIGINAL ==========
    if st.session_state.get(row_id + '_edit_original'):
        new_original = st.text_input("Nhập Original mới:", value=str(q.get('Original', '')), key=row_id + '_original')
        if st.button(f"💾 Lưu Original ({oid})"):
            old_original = q['Original']
            idx = df_all[df_all['Original'] == old_original].index
            if not idx.empty:
                df_all.loc[idx[0], 'Original'] = new_original
                for df_sheet in all_sheets.values():
                    if old_original in df_sheet['Original'].values:
                        df_sheet.loc[df_sheet['Original'] == old_original, 'Original'] = new_original

                if mode == "Xáo trộn đề - 1 câu":
                    for item in st.session_state.shuffled_questions:
                        if item['Original'] == old_original:
                            item['Original'] = new_original
                elif mode != "Toàn bộ không sắp xếp":
                    df_sorted.loc[df_sorted['Original'] == old_original, 'Original'] = new_original

                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                    for sn, df_sheet in all_sheets.items():
                        df_sheet.to_excel(writer, sheet_name=sn, index=False)

                st.session_state[row_id + '_edit_original'] = False
                st.success("Đã cập nhật Original.")
                st.rerun()

    # ========== CHỈNH SỬA CODETOPIC ==========
    if st.session_state.get(row_id + '_edit_topic'):
        new_code = st.text_input("Nhập CodeTopic mới:", value=q.get('CodeTopic') or "", key=row_id + '_codetopic')
        if st.button(f"💾 Lưu CodeTopic ({oid})"):
            idx = df_all[df_all['Original'] == q['Original']].index
            if not idx.empty:
                df_all.loc[idx[0], 'CodeTopic'] = new_code
                for df_sheet in all_sheets.values():
                    if q['Original'] in df_sheet['Original'].values:
                        df_sheet.loc[df_sheet['Original'] == q['Original'], 'CodeTopic'] = new_code

                if mode == "Xáo trộn đề - 1 câu":
                    for item in st.session_state.shuffled_questions:
                        if item['Original'] == q['Original']:
                            item['CodeTopic'] = new_code
                elif mode != "Toàn bộ không sắp xếp":
                    df_sorted.loc[df_sorted['Original'] == q['Original'], 'CodeTopic'] = new_code

                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                    for sn, df_sheet in all_sheets.items():
                        df_sheet.to_excel(writer, sheet_name=sn, index=False)

                st.session_state[row_id + '_edit_topic'] = False
                st.success("Đã cập nhật CodeTopic.")
                st.rerun()

    # ========== CHỈNH SỬA CÂU HỎI ==========
    question_text = q['Question']
    pattern_question_only = r"(?s)(.*?)(?:\s+A\.\s+(.*?))?(?:\s+B\.\s+(.*?))?(?:\s+C\.\s+(.*?))?(?:\s+D\.\s+(.*?))?(?:\s+E\.\s+(.*?))?$"
    match_question = re.match(pattern_question_only, question_text)
    question_display = match_question.group(1).strip() if match_question else question_text

    if st.session_state.get(row_id + '_edit_question'):
        new_question = st.text_area("Chỉnh sửa câu hỏi:", value=q['Question'], height=200,
                                    key=row_id + '_question_edit')
        if st.button(f"💾 Lưu câu hỏi ({oid})"):
            idx = df_all[df_all['Original'] == q['Original']].index
            if not idx.empty:
                df_all.loc[idx[0], 'Question'] = new_question
                for df_sheet in all_sheets.values():
                    if q['Original'] in df_sheet['Original'].values:
                        df_sheet.loc[df_sheet['Original'] == q['Original'], 'Question'] = new_question

                if mode == "Xáo trộn đề - 1 câu":
                    for item in st.session_state.shuffled_questions:
                        if item['Original'] == q['Original']:
                            item['Question'] = new_question
                elif mode != "Toàn bộ không sắp xếp":
                    df_sorted.loc[df_sorted['Original'] == q['Original'], 'Question'] = new_question

                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                    for sn, df_sheet in all_sheets.items():
                        df_sheet.to_excel(writer, sheet_name=sn, index=False)

                st.session_state[row_id + '_edit_question'] = False
                st.success("Đã cập nhật câu hỏi.")
                st.rerun()
    else:
        st.markdown(f"<div style='text-align: justify'>{question_display}</div>", unsafe_allow_html=True)

    # ========== HIỂN THỊ HÌNH ẢNH ==========
    if pd.notna(q.get('Hình')):
        try:
            img_path = os.path.join(image_folder, str(q['Hình']).strip())
            if os.path.isfile(img_path):
                st.markdown("<div style='text-align: center; margin: 20px 0;'>", unsafe_allow_html=True)
                st.image(img_path, use_container_width=True, clamp=True)
                st.markdown("</div>", unsafe_allow_html=True)
        except:
            pass

    # ========== CHỈNH SỬA HÌNH ẢNH ==========
    if st.session_state.get(row_id + '_edit_image'):
        new_image = st.text_input("Nhập tên file hình mới:", value=str(q.get('Hình', '')), key=row_id + '_image_edit')
        if st.button(f"💾 Lưu hình ảnh ({oid})"):
            idx = df_all[df_all['Original'] == q['Original']].index
            if not idx.empty:
                df_all.loc[idx[0], 'Hình'] = new_image if new_image else None
                for df_sheet in all_sheets.values():
                    if q['Original'] in df_sheet['Original'].values:
                        df_sheet.loc[df_sheet['Original'] == q['Original'], 'Hình'] = new_image if new_image else None

                if mode == "Xáo trộn đề - 1 câu":
                    for item in st.session_state.shuffled_questions:
                        if item['Original'] == q['Original']:
                            item['Hình'] = new_image if new_image else None
                elif mode != "Toàn bộ không sắp xếp":
                    df_sorted.loc[df_sorted['Original'] == q['Original'], 'Hình'] = new_image if new_image else None

                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                    for sn, df_sheet in all_sheets.items():
                        df_sheet.to_excel(writer, sheet_name=sn, index=False)

                st.session_state[row_id + '_edit_image'] = False
                st.success("Đã cập nhật hình ảnh.")
                st.rerun()

    # ========== PHẦN ĐÁP ÁN ==========
    if match_question:
        options = [(label, f"{label}. {match_question.group(i + 2).strip()}")
                   for i, label in enumerate(['A', 'B', 'C', 'D', 'E'])
                   if match_question.group(i + 2) is not None and match_question.group(i + 2).strip() != ""]

        # HIỂN THỊ CÁC ĐÁP ÁN TRƯỚC
        if options:
            labels = [l for l, _ in options]
            current_selected = st.radio("Chọn đáp án", labels, format_func=dict(options).get, key=row_id + '_select')

            if row_id + '_select_last' in st.session_state:
                if st.session_state[row_id + '_select_last'] != current_selected:
                    st.session_state[row_id + '_show_answer'] = False
            st.session_state[row_id + '_select_last'] = current_selected

        # NÚT KIỂM TRA VÀ CHỈNH SỬA ĐÁP ÁN
        col_check, col_edit = st.columns([1, 1])
        with col_check:
            if st.button("Kiểm tra đáp án", key=row_id + '_check_answer'):
                st.session_state[row_id + '_show_answer'] = True
        with col_edit:
            if st.button("Chỉnh sửa đáp án", key=row_id + '_edit_answer_btn'):
                st.session_state[row_id + '_edit_answer'] = True

        # KIỂM TRA ĐÁP ÁN
        if st.session_state.get(row_id + '_show_answer'):
            correct = str(q['Anwser']) if pd.notna(q['Anwser']) else ""
            if correct == "":
                st.info("Câu này vẫn chưa có đáp án.")
            elif correct not in ['A', 'B', 'C', 'D', 'E']:
                st.info(f"Đáp án tham khảo: {correct}")
            elif options and current_selected == correct:
                st.success(f"Đã chọn đúng đáp án: {correct}")
            elif options:
                st.warning(f"Chọn sai rùi, chọn lại đi.")
            else:
                st.info(f"Đáp án đúng là: {correct}")

        # CHỈNH SỬA ĐÁP ÁN
        if st.session_state.get(row_id + '_edit_answer'):
            new_ans = st.text_input("Nhập đáp án đúng (có thể ngoài A-E):",
                                    value=str(q['Anwser']) if pd.notna(q['Anwser']) else "",
                                    key=row_id + '_new_answer')
            if st.button(f"💾 Lưu đáp án ({oid})"):
                idx = df_all[df_all['Original'] == q['Original']].index
                if not idx.empty:
                    df_all.loc[idx[0], 'Anwser'] = new_ans
                    for df_sheet in all_sheets.values():
                        if q['Original'] in df_sheet['Original'].values:
                            df_sheet.loc[df_sheet['Original'] == q['Original'], 'Anwser'] = new_ans

                    if mode == "Xáo trộn đề - 1 câu":
                        for item in st.session_state.shuffled_questions:
                            if item['Original'] == q['Original']:
                                item['Anwser'] = new_ans
                    elif mode != "Toàn bộ không sắp xếp":
                        df_sorted.loc[df_sorted['Original'] == q['Original'], 'Anwser'] = new_ans

                    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                        for sn, df_sheet in all_sheets.items():
                            df_sheet.to_excel(writer, sheet_name=sn, index=False)

                    st.session_state[row_id + '_edit_answer'] = False
                    st.success("Đã cập nhật đáp án.")
                    st.rerun()
    else:
        # TRƯỜNG HỢP KHÔNG CÓ ĐÁP ÁN DẠNG A, B, C...
        st.warning("Không tìm thấy đáp án dạng A, B, C... trong câu hỏi này")

        col_check, col_edit = st.columns([1, 1])
        with col_check:
            if st.button("Kiểm tra đáp án", key=row_id + '_check_answer'):
                st.session_state[row_id + '_show_answer'] = True
        with col_edit:
            if st.button("Chỉnh sửa đáp án", key=row_id + '_edit_answer_btn'):
                st.session_state[row_id + '_edit_answer'] = True

        if st.session_state.get(row_id + '_show_answer'):
            correct = str(q['Anwser']) if pd.notna(q['Anwser']) else ""
            if correct == "":
                st.info("Câu này vẫn chưa có đáp án.")
            else:
                st.info(f"Đáp án tham khảo: {correct}")

        if st.session_state.get(row_id + '_edit_answer'):
            new_ans = st.text_input("Nhập đáp án đúng:",
                                    value=str(q['Anwser']) if pd.notna(q['Anwser']) else "",
                                    key=row_id + '_new_answer')
            if st.button(f"💾 Lưu đáp án ({oid})"):
                idx = df_all[df_all['Original'] == q['Original']].index
                if not idx.empty:
                    df_all.loc[idx[0], 'Anwser'] = new_ans
                    for df_sheet in all_sheets.values():
                        if q['Original'] in df_sheet['Original'].values:
                            df_sheet.loc[df_sheet['Original'] == q['Original'], 'Anwser'] = new_ans

                    if mode == "Xáo trộn đề - 1 câu":
                        for item in st.session_state.shuffled_questions:
                            if item['Original'] == q['Original']:
                                item['Anwser'] = new_ans
                    elif mode != "Toàn bộ không sắp xếp":
                        df_sorted.loc[df_sorted['Original'] == q['Original'], 'Anwser'] = new_ans

                    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                        for sn, df_sheet in all_sheets.items():
                            df_sheet.to_excel(writer, sheet_name=sn, index=False)

                    st.session_state[row_id + '_edit_answer'] = False
                    st.success("Đã cập nhật đáp án.")
                    st.rerun()

    # ... (phần code trước giữ nguyên)

    # ========== NÚT ĐIỀU HƯỚNG ==========
    if mode != "Toàn bộ không sắp xếp":
        if mode == "Xáo trộn đề - 1 câu":
            show_navigation_buttons(len(st.session_state.shuffled_questions), st.session_state.shuffled_index, mode,
                                    "shuffled")
        elif mode == "Ngẫu nhiên 1 câu":
            show_navigation_buttons(len(df), st.session_state.random_index, mode, "random")
        elif mode in ["Tăng dần theo Original", "Giảm dần theo Original"]:
            show_navigation_buttons(len(df_sorted), st.session_state.sorted_index, mode, "sorted")
        elif mode == "Theo thứ tự trong file Excel":
            show_navigation_buttons(len(df_sorted), st.session_state.excel_index, mode, "excel")

    # ========== NÚT HIỂN THỊ GHI CHÚ ==========
    st.button("📝 Hiện/Giấu ghi chú", key=f"{row_id}_toggle_note",
              on_click=lambda: st.session_state.update(show_note=not st.session_state.show_note))

    # ========== PHẦN GHI CHÚ ==========
    if st.session_state.show_note:
        # Hiển thị ghi chú hiện tại với nút chỉnh sửa
        st.markdown("#### 📝 Ghi chú hiện tại")
        display_note_with_images(q.get('Note'), image_folder)

        # Nút chỉnh sửa ghi chú
        if st.button("✏️ Chỉnh sửa ghi chú", key=f"{row_id}_edit_note_btn"):
            st.session_state[f"{row_id}_edit_note"] = True

        # ... (phần còn lại giữ nguyên)

        # Phần chỉnh sửa ghi chú (chỉ hiện khi bấm nút)
        if st.session_state.get(f"{row_id}_edit_note"):
            st.markdown("#### ✏️ Chỉnh sửa ghi chú")

            # Tabs for note editing
            tab_text, tab_image = st.tabs(["📝 Text", "🖼️ Image"])

            with tab_text:
                note_text = st.text_area("Nhập ghi chú:", value=q.get('Note') or "", height=150,
                                         key=f"{row_id}_note_edit")

            with tab_image:
                # Image upload functionality
                uploaded_file = st.file_uploader("Tải lên hình ảnh", type=['png', 'jpg', 'jpeg'],
                                                 key=f"{row_id}_upload")

                # Clipboard paste functionality
                paste_check = st.checkbox("Dán hình ảnh từ clipboard (Ctrl+V)", key=f"{row_id}_paste_check")

                if paste_check:
                    try:
                        # Get image from clipboard
                        img = ImageGrab.grabclipboard()

                        if img is not None:
                            # Display the image
                            st.image(img, caption="Ảnh từ clipboard", use_container_width=True)

                            # Generate filename
                            img_name = f"note_{oid}_{int(time.time())}.png"
                            img_path = os.path.join(image_folder, img_name)

                            # Save image
                            img.save(img_path)

                            # Hiển thị đường dẫn với nút copy
                            st.markdown("### Đường dẫn ảnh")
                            img_ref = f"\n![image]({img_name})"

                            # Tạo column để hiển thị đường dẫn và nút copy
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.code(img_ref, language="markdown")
                            with col2:
                                if st.button("📋 Copy", key=f"{row_id}_copy_btn"):
                                    pyperclip.copy(img_ref)
                                    st.toast("Đã copy vào clipboard!")

                            st.success(f"Ảnh đã được lưu tại: {img_path}")
                            st.info("Vui lòng copy đường dẫn trên và dán vào ô ghi chú")
                        else:
                            st.warning(
                                "Không tìm thấy ảnh trong clipboard. Hãy chụp ảnh màn hình bằng Snipping Tool và nhấn Ctrl+C trước.")
                    except Exception as e:
                        st.error(f"Lỗi khi xử lý ảnh từ clipboard: {str(e)}")
                        st.info("Trên Windows, vui lòng đảm bảo:")
                        st.info("1. Đã chụp ảnh màn hình bằng Snipping Tool")
                        st.info("2. Đã nhấn Ctrl+C để copy ảnh vào clipboard")
                        st.info("3. Đang chạy ứng dụng với quyền administrator nếu cần")

            # Save button
            if st.button(f"💾 Lưu ghi chú {oid}", key=f"{row_id}_save_note"):
                # Handle image saving first
                image_filename = None

                # Check for uploaded file
                if uploaded_file is not None:
                    try:
                        # Create unique filename
                        image_filename = f"note_{oid}_{int(time.time())}.{uploaded_file.type.split('/')[-1]}"
                        img_path = os.path.join(image_folder, image_filename)

                        # Save the image
                        with open(img_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Add image reference to note
                        note_text += f"\n![image]({image_filename})"
                    except Exception as e:
                        st.error(f"Lỗi khi lưu hình ảnh: {str(e)}")

                # Save the note text
                idx = df_all[df_all['Original'] == q['Original']].index
                if not idx.empty:
                    df_all.loc[idx[0], 'Note'] = note_text
                    for df_sheet in all_sheets.values():
                        if q['Original'] in df_sheet['Original'].values:
                            df_sheet.loc[df_sheet['Original'] == q['Original'], 'Note'] = note_text

                    if mode == "Xáo trộn đề - 1 câu":
                        for item in st.session_state.shuffled_questions:
                            if item['Original'] == q['Original']:
                                item['Note'] = note_text
                    elif mode != "Toàn bộ không sắp xếp":
                        df_sorted.loc[df_sorted['Original'] == q['Original'], 'Note'] = note_text

                    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                        for sn, df_sheet in all_sheets.items():
                            df_sheet.to_excel(writer, sheet_name=sn, index=False)

                    st.session_state[f"{row_id}_edit_note"] = False
                    st.success("Đã lưu ghi chú.")
                    st.rerun()