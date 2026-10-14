import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Phần mềm Thống kê SPC (Cp, Cpk)", layout="wide"
)

st.title("📊 Phần mềm Phân tích Năng lực Quá trình (SPC)")
st.write(
    "Nhập dữ liệu đo lường, tính toán Cp, Cpk, xem biểu đồ Histogram, X-bar và xuất báo cáo."
)

# --- KHU VỰC NHẬP LIỆU ---
st.sidebar.header("⚙️ Thông số cài đặt")
usl = st.sidebar.number_input("Giới hạn trên (USL)", value=10.5)
lsl = st.sidebar.number_input("Giới hạn dưới (LSL)", value=9.5)
target = st.sidebar.number_input("Giá trị mục tiêu (Target)", value=10.0)

st.subheader("📝 Nhập dữ liệu đo (Tối đa 300 giá trị)")
input_method = st.radio(
    "Chọn phương thức nhập:", ("Nhập thủ công / Dán dữ liệu", "Tải file Excel")
)

data = []

if input_method == "Nhập thủ công / Dán dữ liệu":
  raw_data = st.text_area(
    "Dán các giá trị đo cách nhau bằng dấu phẩy, khoảng trắng hoặc xuống dòng:",
    value="10.1, 9.9, 10.0, 10.2, 9.8, 10.1, 10.0, 9.9, 10.3, 9.7",
  )
  if raw_data:
    try:
      # Xử lý chuỗi nhập vào thành danh sách số
      import re

      numbers = [
        float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", raw_data)
      ]
      if len(numbers) > 300:
        st.warning("Bạn đã nhập quá 300 giá trị. Hệ thống sẽ lấy 300 giá trị đầu.")
        data = numbers[:300]
      else:
        data = numbers
    except ValueError:
      st.error("Vui lòng chỉ nhập các giá trị số hợp lệ.")
else:
  uploaded_file = st.file_uploader(
    "Tải lên file Excel (.xlsx) chứa cột dữ liệu", type=["xlsx"]
  )
  if uploaded_file is not None:
    df_in = pd.read_excel(uploaded_file)
    col_name = st.selectbox("Chọn cột chứa dữ liệu đo:", df_in.columns)
    data = df_in[col_name].dropna().tolist()[:300]

if len(data) > 0:
  st.success(f"Đã tải thành công {len(data)} mẫu dữ liệu đo.")

  # --- TÍNH TOÁN THỐNG KÊ ---
  arr = np.array(data)
  n = len(arr)
  mean_val = np.mean(arr)
  std_val = np.std(arr, ddof=1)  # Độ lệch chuẩn mẫu
  min_val = np.min(arr)
  max_val = np.max(arr)

  # Tính Cp, Cpk
  cp = (usl - lsl) / (6 * std_val) if std_val > 0 else 0
  cpk_upper = (usl - mean_val) / (3 * std_val) if std_val > 0 else 0
  cpk_lower = (mean_val - lsl) / (3 * std_val) if std_val > 0 else 0
  cpk = min(cpk_upper, cpk_lower)

  # Hiển thị bảng thông số
  st.markdown("### 📈 Kết quả Phân tích Thống kê")
  col1, col2, col3, col4, col5 = st.columns(5)
  col1.metric("Số lượng mẫu (N)", n)
  col2.metric("Trung bình (Mean)", f"{mean_val:.4f}")
  col3.metric("Độ lệch chuẩn (Std)", f"{std_val:.4f}")
  col4.metric("Cp", f"{cp:.3f}")
  col5.metric("Cpk", f"{cpk:.3f}", delta="Đạt yêu cầu" if cpk >= 1.33 else "Cần cải thiện")

  # --- VẼ BIỂU ĐỒ ---
  col_chart1, col_chart2 = st.columns(2)

  with col_chart1:
    st.subheader("Biểu đồ Phân bố (Histogram)")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(arr, bins=10, edgecolor="black", alpha=0.7, color="skyblue")
    ax.axvline(
        usl, color="red", linestyle="--", linewidth=2, label=f"USL ({usl})"
    )
    ax.axvline(
        lsl, color="red", linestyle="--", linewidth=2, label=f"LSL ({lsl})"
    )
    ax.axvline(
        mean_val,
        color="green",
        linestyle="-",
        linewidth=2,
        label=f"Mean ({mean_val:.2f})",
    )
    ax.legend(fontsize=8)
    ax.set_title("Histogram & Giới hạn")
    st.pyplot(fig)

  with col_chart2:
    st.subheader("Biểu đồ Kiểm soát (X-bar Chart)")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(arr, marker="o", linestyle="-", color="b", markersize=4)
    ax2.axhline(mean_val, color="green", linestyle="-", label="Mean")
    ax2.axhline(
        usl, color="red", linestyle="--", label="USL"
    )
    ax2.axhline(
        lsl, color="red", linestyle="--", label="LSL"
    )
    ax2.legend(fontsize=8)
    ax2.set_title("X-bar Chart theo thứ tự đo")
    st.pyplot(fig2)

  # --- XUẤT BÁO CÁO EXCEL ---
  st.markdown("---")
  st.subheader("📥 Xuất Báo cáo")

  def to_excel(df_results):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_results.to_excel(writer, index=False, sheet_name="SPC_Report")
    return output.getvalue()

  report_df = pd.DataFrame({
      "Chỉ tiêu": ["Số mẫu", "Mean", "Std Dev", "Min", "Max", "USL", "LSL", "Cp", "Cpk"],
      "Giá trị": [n, mean_val, std_val, min_val, max_val, usl, lsl, cp, cpk],
  })

  excel_data = to_excel(report_df)
  st.download_button(
      label="Tải xuống Báo cáo Excel",
      data=excel_data,
      file_name="SPC_Report.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )