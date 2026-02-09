import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

# 1. إعدادات الصفحة وتنسيق المظهر
st.set_page_config(page_title="داشبورد الإنتاجية - القناة للسكر", layout="wide")

# تنسيق اللغة العربية (RTL) وتحسين المظهر
st.markdown("""
    <style>
    [data-testid="stSidebar"] { direction: rtl; }
    .main { direction: rtl; text-align: right; }
    div.stMetric { text-align: center; border: 1px solid #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. رابط الملف (تأكد من استخدام الرابط الذي ينتهي بـ download=1)
# ملاحظة: إذا لم يعمل الرابط، يرجى التأكد من صلاحية "Anyone with the link" في SharePoint
URL = "https://canalsugar-my.sharepoint.com/:x:/g/personal/ahmed_abdelnasser_canalsugar_com/EY6iLoxqqv5OndWxQ4iI6oABO9XFqE_vF_vN_vN_vN?download=1"

@st.cache_data(ttl=600) # تحديث البيانات كل 10 دقائق
def load_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_excel(BytesIO(response.content))
            return df
        else:
            st.error(f"خطأ في الوصول للملف: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
        return None

# تحميل البيانات
df_raw = load_data(URL)

if df_raw is not None:
    # --- القائمة الجانبية (Sidebar) ---
    st.sidebar.image("https://canalsugar.com/wp-content/uploads/2019/12/logo.png", width=150) # شعار افتراضي
    st.sidebar.header("🔍 فلاتر البحث")

    # فلتر الإدارة
    all_managements = ["الكل"] + sorted(list(df_raw['الادارة'].unique()))
    selected_management = st.sidebar.selectbox("اختر الإدارة", all_managements)

    # فلتر العروة
    all_erwas = ["الكل"] + sorted(list(df_raw['العروة'].astype(str).unique()))
    selected_erwa = st.sidebar.selectbox("اختر العروة", all_erwas)

    # --- تطبيق الفلاتر ---
    df = df_raw.copy()
    if selected_management != "الكل":
        df = df[df['الادارة'] == selected_management]
    if selected_erwa != "الكل":
        df = df[df['العروة'].astype(str) == selected_erwa]

    # --- العنوان الرئيسي والمؤشرات ---
    st.title("📊 لوحة تحكم إنتاجية بنجر السكر - 2025/2026")
    
    m1, m2, m3 = st.columns(3)
    total_tons = df['الطن المتوقع توريده'].sum()
    total_feddans = df['المساحة'].sum()
    avg_yield = total_tons / total_feddans if total_feddans > 0 else 0
    
    m1.metric("إجمالي الأطنان المتوقعة", f"{total_tons:,.0f} طن")
    m2.metric("إجمالي المساحة", f"{total_feddans:,.0f} فدان")
    m3.metric("متوسط الإنتاجية/فدان", f"{avg_yield:,.2f}")

    st.divider()

    # --- الرسوم البيانية ---
    row1_col1, row1_col2 = st.columns([1.5, 1])

    with row1_col1:
        st.subheader("الأطنان حسب المنطقة (Tons by Area)")
        area_data = df.groupby('المنطقة')['الطن المتوقع توريده'].sum().reset_index()
        fig_area = px.bar(area_data, x='المنطقة', y='ن المتوقع توريده', 
                          color_discrete_sequence=['#5A9E3F'], text_auto='.2s')
        st.plotly_chart(fig_area, use_container_width=True)

    with row1_col2:
        st.subheader("توزيع الأطنان حسب العروة")
        erwa_data = df.groupby('العروة')['الطن المتوقع توريده'].sum().reset_index()
        fig_pie = px.pie(erwa_data, values='الطن المتوقع توريده', names='العروة', 
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Set1)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    row2_col1, row2_col2 = st.columns([1, 1.5])

    with row2_col1:
        st.subheader("إحصائيات الإدارة والمنطقة")
        table_data = df.groupby(['الادارة', 'المنطقة']).agg({
            'ن المتوقع توريده': 'sum',
            'المساحة': 'sum'
        }).reset_index()
        table_data['Average'] = (table_data['الطن المتوقع توريده'] / table_data['المساحة']).round(1)
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    with row2_col2:
        st.subheader("أعلى المهندسين إنتاجية (Tons by Engineer)")
        eng_data = df.groupby('اسم المهندس')['الطن المتوقع توريده'].sum().sort_values(ascending=True).reset_index().tail(15)
        fig_eng = px.bar(eng_data, x='الطن المتوقع توريده', y='اسم المهندس', 
                         orientation='h', color_discrete_sequence=['#2E7D32'], text_auto='.2s')
        st.plotly_chart(fig_eng, use_container_width=True)

else:
    st.warning("يرجى التأكد من صلاحيات رابط SharePoint أو استخدام ملف محلي للتجربة.")
    # خيار لرفع الملف يدوياً في حال فشل الرابط
    uploaded_file = st.file_uploader("أو قم برفع ملف Excel يدوياً هنا", type="xlsx")
    if uploaded_file:
        df_raw = pd.read_excel(uploaded_file)
        st.rerun()

