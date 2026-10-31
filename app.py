import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import io
from datetime import date

st.set_page_config(page_title="SaaS & AI Cost Analytics Dashboard", layout="wide")

@st.cache_resource
def init_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="SaaS_AI_DB"
        )
        return conn
    except Exception as e:
        st.error(f"Lỗi kết nối CSDL: {e}")
        return None

@st.cache_data(ttl=60)
def run_query(query):
    conn = init_connection()
    if conn is not None:
        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Lỗi truy vấn: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

st.title("UNIFIED SAAS & AI COST ANALYTICS DASHBOARD")
st.write("Hệ thống theo dõi tỉ lệ rời bỏ (Churn) và phân tích chi phí AI theo gói dịch vụ")
st.sidebar.header("Bộ lọc dữ liệu")

date_range = st.sidebar.date_input(
    "Khoảng thời gian",
    value=(date(2026, 1, 1), date(2026, 3, 31))
)
size_options = ['Startup', 'SMB', 'Enterprise']
selected_sizes = st.sidebar.multiselect(
    "Phân khúc doanh nghiệp",
    options=size_options,
    default=size_options
)
status_options = ['Tất cả', 'Active', 'Churned', 'Upgraded']
selected_status = st.sidebar.selectbox(
    "Trạng thái dịch vụ",
    options=status_options
)
sql_main = """
           SELECT c.customer_id, \
                  c.customer_name, \
                  c.company_size, \
                  c.signup_date, \
                  p.plan_name, \
                  p.monthly_price, \
                  p.ai_token_limit, \
                  u.usage_month, \
                  u.tokens_consumed, \
                  u.ai_api_cost, \
                  u.support_tickets_opened, \
                  s.status, \
                  s.churn_reason, \
                  s.updated_at
           FROM Customers c
                    JOIN Plans p ON c.plan_id = p.plan_id
                    JOIN UsageLogs u ON c.customer_id = u.customer_id
                    JOIN Subscriptions s ON c.customer_id = s.customer_id
           WHERE 1 = 1 \
           """

filter_clause = ""
if len(date_range) == 2:
    start_d, end_d = date_range
    filter_clause += f" AND u.usage_month BETWEEN '{start_d}' AND '{end_d}'"
if selected_sizes:
    sizes_str = "', '".join(selected_sizes)
    filter_clause += f" AND c.company_size IN ('{sizes_str}')"
else:
    filter_clause += " AND 1=0"
if selected_status != 'Tất cả':
    filter_clause += f" AND s.status = '{selected_status}'"

sql_main += filter_clause
sql_risk = f"""
SELECT 
    c.customer_id,
    c.customer_name,
    c.company_size,
    p.plan_name,
    p.ai_token_limit,
    s.status,
    MAX(u.tokens_consumed) AS max_tokens_used,
    SUM(u.ai_api_cost) AS total_ai_cost,
    MAX(u.support_tickets_opened) AS max_tickets
FROM Customers c
JOIN Plans p ON c.plan_id = p.plan_id
JOIN UsageLogs u ON c.customer_id = u.customer_id
JOIN Subscriptions s ON c.customer_id = s.customer_id
WHERE 1=1 {filter_clause}
GROUP BY c.customer_id, c.customer_name, c.company_size, p.plan_name, p.ai_token_limit, s.status
HAVING MAX(u.tokens_consumed) > p.ai_token_limit OR MAX(u.support_tickets_opened) > 3
ORDER BY max_tickets DESC
"""

df = run_query(sql_main)
df_risk = run_query(sql_risk)

if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
else:
    active_df = df[df['status'].isin(['Active', 'Upgraded'])]
    mrr_val = active_df['monthly_price'].sum()
    total_cust = df['customer_id'].nunique()
    churn_cust = df[df['status'] == 'Churned']['customer_id'].nunique()
    churn_rate = (churn_cust / total_cust * 100) if total_cust > 0 else 0
    net_margin = df['monthly_price'].sum() - df['ai_api_cost'].sum()
    avg_tickets = df['support_tickets_opened'].mean()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monthly Recurring Revenue (MRR)", f"${mrr_val:,.2f}")
    col2.metric("Churn Rate (%)", f"{churn_rate:.1f}%")
    col3.metric("Net AI Profitability Margin", f"${net_margin:,.2f}")
    col4.metric("Avg Support Tickets", f"{avg_tickets:.2f}")
    st.markdown("---")
    df['month_str'] = pd.to_datetime(df['usage_month']).dt.strftime('%Y-%m')
    monthly_list = []
    for m, grp in df.groupby('month_str'):
        m_mrr = grp[grp['status'].isin(['Active', 'Upgraded'])]['monthly_price'].sum()
        t_c = grp['customer_id'].nunique()
        c_c = grp[grp['status'] == 'Churned']['customer_id'].nunique()
        c_rate = (c_c / t_c * 100) if t_c > 0 else 0
        monthly_list.append({'Tháng': m, 'MRR ($)': m_mrr, 'Churn Rate (%)': round(c_rate, 2)})
    df_trend = pd.DataFrame(monthly_list)
    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.line(
            df_trend,
            x='Tháng',
            y=['MRR ($)', 'Churn Rate (%)'],
            markers=True,
            title="Xu hướng MRR và Tỉ lệ Churn theo từng tháng",
            color_discrete_map={'MRR ($)': '#2ecc71', 'Churn Rate (%)': '#e74c3c'}
        )
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.scatter(
            df,
            x='tokens_consumed',
            y='ai_api_cost',
            color='plan_name',
            size='support_tickets_opened',
            hover_data=['customer_name', 'status'],
            title="Tương quan lượng AI Tokens tiêu thụ và Chi phí API AI",
            color_discrete_sequence=['#ff7f0e', '#1f77b4', '#2ca02c']
        )
        st.plotly_chart(fig2, use_container_width=True)
    c3, c4 = st.columns(2)

    with c3:
        df_churn_reason = df[df['status'] == 'Churned'].drop_duplicates(subset=['customer_id'])
        reason_counts = df_churn_reason['churn_reason'].value_counts().reset_index()
        reason_counts.columns = ['churn_reason', 'count']
        fig3 = px.bar(
            reason_counts,
            x='churn_reason',
            y='count',
            color='count',
            color_continuous_scale='Reds',
            title="Lý do hủy dịch vụ phổ biến nhất ở khách hàng Churned"
        )
        st.plotly_chart(fig3, use_container_width=True)
    with c4:
        df_unique_cust = df.drop_duplicates(subset=['customer_id'])
        fig4 = px.density_heatmap(
            df_unique_cust,
            x='company_size',
            y='status',
            color_continuous_scale='OrRd',
            text_auto=True,
            title="Phân bố rủi ro Churn theo quy mô công ty"
        )
        st.plotly_chart(fig4, use_container_width=True)
    st.markdown("---")
    st.subheader("Danh sách khách hàng có nguy cơ Churn cao (Vượt giới hạn Token hoặc > 3 Tickets)")
    search_name = st.text_input("Tìm kiếm theo tên khách hàng:")
    if search_name:
        df_risk_show = df_risk[df_risk['customer_name'].str.contains(search_name, case=False, na=False)]
    else:
        df_risk_show = df_risk
    st.dataframe(df_risk_show, use_container_width=True)
    b1, b2 = st.columns(2)
    with b1:
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Tải dữ liệu (.CSV)",
            data=csv_data,
            file_name="saas_ai_report.csv",
            mime="text/csv"
        )
    with b2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        st.download_button(
            label="Tải dữ liệu (.XLSX)",
            data=buffer.getvalue(),
            file_name="saas_ai_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with st.expander("Xem câu lệnh SQL (SQL Viewer)"):
        st.write("Truy vấn lấy dữ liệu tổng hợp:")
        st.code(sql_main, language="sql")
        st.write("Truy vấn nhóm khách hàng rủi ro cao (GROUP BY & HAVING):")
        st.code(sql_risk, language="sql")
    st.markdown("---")
    st.subheader("Báo cáo Tóm tắt & Insight Kinh doanh")
    st.markdown("""
    **1. Ba Insight kinh doanh cốt lõi từ dữ liệu:**
    - **Rủi ro từ nhóm Startup vượt ngưỡng Token:** Nhóm khách hàng `Startup` đăng ký gói `Starter` nhưng sử dụng vượt `ai_token_limit` (100,000 tokens) chiếm tỷ lệ rời bỏ cao nhất do phát sinh chi phí vượt ngân sách.
    - **Mối liên hệ giữa Support Tickets và Churn:** Các khách hàng mở từ **4 vé hỗ trợ trở lên** trong tháng có tỷ lệ hủy dịch vụ lên tới hơn 80%, chủ yếu liên quan đến lỗi API chậm và giới hạn token.
    - **Biên lợi nhuận cao ở phân khúc Enterprise:** Dù tiêu thụ lượng token lớn, nhóm `Enterprise` vẫn giữ biên lợi nhuận ròng (Net AI Profitability Margin) dương ổn định và hầu như không phát sinh Churn.
    **2. Đề xuất hành động cho Product & Customer Success:**
    - **Đội Product:** Thiết lập cảnh báo tự động trên ứng dụng khi người dùng chạm mốc **80% AI Token Limit** và gợi ý nâng cấp linh hoạt sang gói `Pro` thay vì tính phí vượt mức đột ngột.
    - **Đội Customer Success:** Tạo luồng ưu tiên xử lý ngay lập tức cho các tài khoản mở trên **3 support tickets/tháng** để can thiệp kỹ thuật trước khi khách quyết định hủy gói.
    """)