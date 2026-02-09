import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Dashboard Canal Sugar", layout="wide")

# --- رابط OneDrive المنسوخ ---
# الصق الرابط الذي حصلت عليه بعد الضغط على Apply هنا
SHARE_URL = "https://canalsugar-my.sharepoint.com/:x:/g/personal/ahmed_abdelnasser_canalsugar_com/..."

def get_direct_link(url):
    """تحويل الرابط المؤسسي إلى رابط تحميل مباشر"""
    if "sharepoint.com" in url:
        # إزالة أي بارامترات زائدة وإضافة أمر التحميل المباشر
        base_url = url.split('?')[0]
        return f"{base_url}?download=1"
    return url

@st.cache_data(ttl=300) # تحديث تلقائي كل 5 دقائق
def load_data(url):
    try:
        direct_link = get_direct_link(url)
        # إرسال طلب للملف مع تجاوز حماية المتصفح البسيطة
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(direct_link, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content), engine='openpyxl')
        else:
            return None
    except:
        return None

# --- المعالجة الرئيسية ---
df_raw = load_data(SHARE_URL)

# خيار احتياطي في حال فشل الرابط (الرفع اليدوي كما نجح معك سابقاً)
if df_raw is None:
    st.sidebar.warning("⚠️ تعذر الاتصال التلقائي بـ OneDrive")
    uploaded_file = st.sidebar.file_uploader("يرجى رفع الملف يدوياً للتحديث", type="xlsx")
    if uploaded_file:
        df_raw = pd.read_excel(uploaded_file, engine='openpyxl')

if df_raw is not None:
    # التأكد من اسم العمود المطلوب
    TARGET_COL = 'الطن المتوقع توريده'
    
    # تنظيف أسماء الأعمدة من المسافات المخفية
    df_raw.columns = df_raw.columns.str.strip()
    
    st.title("🚜 متابعة إنتاجية بنجر السكر - القناة للسكر")
    
    # --- الفلاتر الجانبية ---
    st.sidebar.header("🔍 فلاتر البحث")
    mgmt = st.sidebar.multiselect("الإدارة", df_raw['الادارة'].unique(), default=df_raw['الادارة'].unique())
    erwa = st.sidebar.multiselect("العروة", df_raw['العروة'].unique(), default=df_raw['العروة'].unique())
    
    df = df_raw[(df_raw['الادارة'].isin(mgmt)) & (df_raw['العروة'].isin(erwa))]

    # --- عرض الأرقام الرئيسية ---
    c1, c2, c3 = st.columns(3)
    total_tons = df[TARGET_COL].sum()
    total_area = df['المساحة'].sum()
    c1.metric("إجمالي الأطنان", f"{total_tons:,.0f} طن")
    c2.metric("إجمالي المساحة", f"{total_area:,.1f} فدان")
    c3.metric("الإنتاجية (طن/فدان)", f"{(total_tons/total_area if total_area > 0 else 0):,.2f}")

    # --- الرسوم البيانية (بناءً على صورتك الأولى) ---
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("الأطنان حسب المنطقة")
        fig_area = px.bar(df.groupby('المنطقة')[TARGET_COL].sum().reset_index(), 
                          x='المنطقة', y=TARGET_COL, color_discrete_sequence=['#5A9E3F'])
        st.plotly_chart(fig_area, use_container_width=True)

    with col_right:
        st.subheader("توزيع العروة")
        fig_pie = px.pie(df, values=TARGET_COL, names='العروة', hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("إنتاجية المهندسين")
    eng_fig = px.bar(df.groupby('اسم المهندس')[TARGET_COL].sum().sort_values().reset_index(), 
                     x=TARGET_COL, y='اسم المهندس', orientation='h', color_discrete_sequence=['#2E7D32'])
    st.plotly_chart(eng_fig, use_container_width=True)
else:
    st.info("💡 بانتظار ربط البيانات.. تأكد من صلاحيات الرابط في القائمة الجانبية.")
