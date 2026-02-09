import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ضع رابط OneDrive الذي نسخته هنا بين القوسين
ONEDRIVE_LINK = "https://canalsugar-my.sharepoint.com/:x:/p/ahmed_abdelnasser/IQCD4iKMpGrzTp1bFDSLhuoKAelM4hshFAHAJDs325VsKJA?email=AYA.HASSAN%40CANALSUGAR.COM&e=XJgegV"

@st.cache_data
def load_data_from_onedrive(url):
    # كود لتحويل رابط OneDrive إلى رابط تحميل مباشر
    import base64
    base64_bytes = base64.b64encode(bytes(url, 'utf-8'))
    clean_base64_string = base64_bytes.decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
    direct_url = f"https://api.onedrive.com/v1.0/shares/u!{clean_base64_string}/root/content"
    
    # قراءة الملف
    df = pd.read_excel(direct_url)
    return df

try:
    df = load_data_from_onedrive(ONEDRIVE_LINK)
    st.success("✅ تم الاتصال بـ OneDrive وتحديث البيانات بنجاح!")
    

    # --- القائمة الجانبية (Sidebar) ---
    st.sidebar.header("🔍 فلاتر البحث")

    # فلتر الإدارة
    all_managements = ["الكل"] + list(df['الادارة'].unique())
    selected_management = st.sidebar.selectbox("اختر الإدارة", all_managements)

    # فلتر العروة
    all_erwas = ["الكل"] + list(df['العروة'].astype(str).unique())
    selected_erwa = st.sidebar.selectbox("اختر العروة", all_erwas)

    # --- تطبيق الفلترة على البيانات ---
    filtered_df = df.copy()
    if selected_management != "الكل":
        filtered_df = filtered_df[filtered_df['الادارة'] == selected_management]
    
    if selected_erwa != "الكل":
        filtered_df = filtered_df[filtered_df['العروة'].astype(str) == selected_erwa]

    # --- عرض المحتوى الرئيسي ---
    st.title("📊 لوحة تحكم الإنتاجية الزراعية")
    
    # مؤشرات سريعة (KPIs)
    total_tons = filtered_df['الطن المتوقع توريده'].sum()
    total_feddans = filtered_df['المساحة'].sum()
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("إجمالي الأطنان", f"{total_tons:,.0f}")
    col_kpi2.metric("إجمالي المساحة", f"{total_feddans:,.0f}")
    col_kpi3.metric("متوسط الإنتاجية", f"{(total_tons/total_feddans if total_feddans > 0 else 0):,.2f}")

    st.divider()

    # الرسوم البيانية (ستتأثر تلقائياً بالفلتر)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tons by area")
        area_chart = filtered_df.groupby('المنطقة')['الطن المتوقع توريده'].sum().reset_index()
        fig_area = px.bar(area_chart, x='المنطقة', y='الطن المتوقع توريده', color_discrete_sequence=['#5A9E3F'])
        st.plotly_chart(fig_area, use_container_width=True)

        st.subheader("Tons by 3erwa")
        erwa_chart = filtered_df.groupby('العروة')['الطن المتوقع توريده'].sum().reset_index()
        fig_pie = px.pie(erwa_chart, values='الطن المتوقع توريده', names='العروة')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("إحصائيات الإدارة والمنطقة")
        st.dataframe(filtered_df.groupby(['الادارة', 'المنطقة']).agg({'الطن المتوقع توريده':'sum', 'المساحة':'sum'}), use_container_width=True)

        st.subheader("Tons by engineer")
        eng_chart = filtered_df.groupby('اسم المهندس')['الطن المتوقع توريده'].sum().sort_values(ascending=True).reset_index()
        fig_eng = px.bar(eng_chart, x='الطن المتوقع توريده', y='اسم المهندس', orientation='h', color_discrete_sequence=['#5A9E3F'])
        st.plotly_chart(fig_eng, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ فشل الاتصال بالملف: تأكد من رابط المشاركة. الخطأ: {e}")
