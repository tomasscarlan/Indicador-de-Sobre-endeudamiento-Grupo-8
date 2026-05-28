import streamlit as st
import pandas as pd
from src.finance import process_dataframe

st.set_page_config(page_title="Indicador de Sobre-endeudamiento", layout="wide")
st.title("Indicador de Sobre-endeudamiento")

uploaded = st.file_uploader("Sube el archivo Excel (si tiene encabezados en las dos primeras filas, se omiten)", type=["xls","xlsx"])
ingreso_mensual = st.number_input("Ingreso mensual", value=1200000, step=10000, format="%d")

if uploaded:
    try:
        df = pd.read_excel(uploaded, skiprows=2)
    except Exception:
        df = pd.read_excel(uploaded)

    results = process_dataframe(df, ingreso_mensual)

    st.subheader("Resumen")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total cuotas mensuales", f"${results['total_cuotas']:,.0f}")
    col2.metric("Ratio endeudamiento", f"{results['ratio_endeudamiento']:.2%}")
    col3.metric("Gastos impulsivos", f"${results['total_impulsivos']:,.0f}")

    st.markdown(f"**Nivel de riesgo:** {results['nivel']} — {results['alerta']}")

    st.subheader("Detalle de operaciones")
    st.dataframe(results['df'][['categoria','descripcion','monto','cuotas','tna','cuota_mensual']])

    if not results['gastos_impulsivos'].empty:
        st.subheader("Gastos impulsivos por categoría")
        imp_cat = results['gastos_impulsivos'].groupby('categoria')['monto'].sum().reset_index()
        imp_cat = imp_cat.set_index('categoria')
        st.bar_chart(imp_cat)

else:
    st.info("Sube un archivo Excel para comenzar. El archivo usado originalmente omite las dos primeras filas de título.")
