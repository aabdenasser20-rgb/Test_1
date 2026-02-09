import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

# 1. إعدادات الصفحة
st.set_page_config(page_title="داشبورد إنتاجية البنجر", layout="wide")

# تنسيق المظهر ودعم اللغة العربية (RTL)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { direction: rtl; }
    .main { direction: rtl; text-align: right; }
    div.stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. إدارة مصدر البيانات في القائمة الجانبية
st.sidebar.title("📂 مصدر البيانات")
data_source = st.sidebar.radio("اختر طريقة التحميل:", ("رفع ملف يدوي", "رابط SharePoint التلقائي"))

df = None
# اسم العمود الجديد بعد التعديل
TARGET_COL = 'الطن المتوقع توريده'

if data_source == "رفع ملف يدوي":
    uploaded_file = st.sidebar.file_uploader("قم برفع ملف all_data.xlsx", type="xlsx")
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.sidebar.success("✅ تم تحميل الملف بنجاح")
        except Exception as e:
            st.sidebar.error(f"خطأ في قراءة الملف: {e}")

else:
    # الرابط الخاص بك
    SHAREPOINT_URL = "https://canalsugar-my.sharepoint.com/:x:/g/personal/ahmed_abdelnasser_canalsugar_com/EY6iLoxqqv5OndWxQ4iI6oABO9XFqE_vF_vN_vN_vN?download=1"
    try:
        resp = requests.get(SHAREPOINT_URL)
        if resp.status_code == 200:
            df = pd.read_excel(BytesIO(resp.content), engine='openpyxl')
        else:
            st.sidebar.error("⚠️ فشل الرابط (خطأ حماية الشركة). يرجى استخدام 'الرفع اليدوي'.")
    except Exception as e:
        st.sidebar.error("تعذر الاتصال بالرابط.")

# 3. عرض البيانات والرسوم البيانية
if df is not None:
    # التأكد من وجود العمود الجديد لتجنب توقف الكود
    if TARGET_COL not in df.columns:
        st.error(f"⚠️ لم يتم العثور على عمود باسم '{TARGET_COL}'. تأكد من تسمية العمود في ملف الإكسيل بشكل صحيح.")
    else:
        st.sidebar.divider()
        st.sidebar.header("🔍 فلاتر العرض")
        
        selected_mgmt = st.sidebar.multiselect("الإدارة", options=df['الادارة'].unique(), default=df['الادارة'].unique())
        selected_erwa = st.sidebar.multiselect("العروة", options=df['العروة'].unique(), default=df['العروة'].unique())
        
        # تطبيق الفلتر
        mask = df['الادارة'].isin(selected_mgmt) & df['العروة'].isin(selected_erwa)
        filtered_df = df[mask]

        # --- العنوان والمؤشرات ---
        st.title("📊 لوحة تحكم إنتاجية المحصول")
        
        kpi1, kpi2, kpi3 = st.columns(3)
        total_tons = filtered_df[TARGET_COL].sum()
        total_area = filtered_df['المساحة'].sum()
        avg_yield = total_tons / total_area if total_area > 0 else 0
        
        kpi1.metric("إجمالي الأطنان", f"{total_tons:,.0f} طن")
        kpi2.metric("إجمالي المساحة", f"{total_area:,.0f} فدان")
        kpi3.metric("متوسط الإنتاجية/فدان", f"{avg_yield:,.2f}")

        st.divider()

        # --- الرسوم البيانية ---
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("الأطنان حسب المنطقة (Tons by Area)")
            fig_area = px.bar(filtered_df.groupby('المنطقة')[TARGET_COL].sum().reset_index(), 
                              x='المنطقة', y=TARGET_COL, color_discrete_sequence=['#5A9E3F'])
            st.plotly_chart(fig_area, use_container_width=True)

        with col2:
            st.subheader("التوزيع حسب العروة (Tons by 3erwa)")
            fig_pie = px.pie(filtered_df.groupby('العروة')[TARGET_COL].sum().reset_index(), 
                             values=TARGET_COL, names='العروة', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        col3, col4 = st.columns([1, 2])
        
        with col3:
            st.subheader("إحصائيات الإدارة")
            summary = filtered_df.groupby(['الادارة', 'المنطقة']).agg({TARGET_COL:'sum', 'المساحة':'sum'}).reset_index()
            st.dataframe(summary, hide_index=True)

        with col4:
            st.subheader("أعلى المهندسين (Tons by Engineer)")
            eng_data = filtered_df.groupby('اسم المهندس')[TARGET_COL].sum().sort_values(ascending=True).reset_index()
            fig_eng = px.bar(eng_data, x=TARGET_COL, y='اسم المهندس', orientation='h', color_discrete_sequence=['#2E7D32'])
            st.plotly_chart(fig_eng, use_container_width=True)

else:
    st.warning("👈 يرجى اختيار مصدر البيانات ورفع الملف من القائمة الجانبية لبدء العرض.")
