import streamlit as st
import pandas as pd
from fpdf import FPDF


# --- NUEVA FUNCIÓN: GENERADOR DE PDF ---
def generar_pdf(df, datos_generales, ajuste_m3):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    # Título
    pdf.cell(190, 10, f"Liquidacion de Servicios - {datos_generales['mes']}", ln=True, align='C')
    pdf.ln(10)

    # Resumen de entrada
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, "Resumen del Recibo", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 7, f"Valor Total Recibo: $ {datos_generales['total']:,.2f}")
    pdf.cell(95, 7, f"M3 Consumo Total: {datos_generales['m3_recibo']:.3f}", ln=True)
    pdf.cell(95, 7, f"Valor M3: $ {datos_generales['valor_m3']:,.3f}")
    pdf.cell(95, 7, f"Ajuste por Unidad: {ajuste_m3:.3f} m3", ln=True)
    pdf.ln(10)

    # Tabla
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 8, "Unidad", border=1, fill=True)
    pdf.cell(40, 8, "M3 Indiv.", border=1, fill=True)
    pdf.cell(40, 8, "M3 Final", border=1, fill=True)
    pdf.cell(60, 8, "Valor a Pagar", border=1, fill=True, ln=True)

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(50, 8, str(row['Unidad']), border=1)
        pdf.cell(40, 8, f"{row['M3']:.3f}", border=1)
        pdf.cell(40, 8, f"{row['M3 Final']:.3f}", border=1)
        pdf.cell(60, 8, f"$ {row['Valor a Pagar']:,.2f}", border=1, ln=True)

    return pdf.output()


# Configuración de la página
st.set_page_config(page_title="Liquidador de Servicios", page_icon="💧")

st.title("💧 Liquidador de Servicios")

# --- SECCIÓN 1: DATOS GENERALES ---
with st.expander("Datos Generales del Recibo", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        mes_periodo = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                                           "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        valor_total_recibo = st.number_input("Valor recibo total ($)", min_value=0.0, value=0.0, step=100.0)

    with col2:
        m3_consumo_total = st.number_input("M3 Consumo Total (Recibo)", min_value=0.0, value=0.000, format="%.3f")
        valor_m3_unitario = st.number_input("Valor m3 ($)", min_value=0.0, value=0.000, format="%.3f")

st.divider()

# --- SECCIÓN 2: DISTRIBUCIÓN POR UNIDAD ---
st.subheader("Distribución por Unidad")

if 'unidades' not in st.session_state:
    st.session_state.unidades = [
        {"nombre": "Interior 4", "ant": 0.0, "act": 0.0},
        {"nombre": "Piso 2 Carlos", "ant": 0.0, "act": 0.0},
        {"nombre": "Interior 2", "ant": 0.0, "act": 0.0},
        {"nombre": "Triunfo Rosita", "ant": 0.0, "act": 0.0},
        {"nombre": "Casa Adriana", "ant": 0.0, "act": 0.0}
    ]


def agregar_unidad():
    st.session_state.unidades.append(
        {"nombre": f"Nueva Unidad {len(st.session_state.unidades) + 1}", "ant": 0.0, "act": 0.0})


h_col1, h_col2, h_col3, h_col4 = st.columns([3, 2, 2, 2])
h_col1.write("**Unidad**")
h_col2.write("**Lec. Anterior**")
h_col3.write("**Lec. Actual**")
h_col4.write("**M3 Consumidos**")

datos_calculados = []
for i, unidad in enumerate(st.session_state.unidades):
    cols = st.columns([3, 2, 2, 2])
    with cols[0]:
        nombre = st.text_input(f"Nombre {i}", value=unidad["nombre"], key=f"nom_{i}", label_visibility="collapsed")
    with cols[1]:
        lec_ant = st.number_input(f"Ant {i}", value=float(unidad["ant"]), format="%.3f", step=0.001, key=f"ant_{i}",
                                  label_visibility="collapsed")
    with cols[2]:
        lec_act = st.number_input(f"Act {i}", value=float(unidad["act"]), format="%.3f", step=0.001, key=f"act_{i}",
                                  label_visibility="collapsed")

    m3_unidad = lec_act - lec_ant
    with cols[3]:
        st.info(f"{m3_unidad:.3f} m3")

    datos_calculados.append({"Unidad": nombre, "M3": m3_unidad})

st.button("➕ Agregar Unidad", on_click=agregar_unidad)
st.divider()

# --- SECCIÓN 3: CÁLCULOS Y RESULTADOS ---
if st.button("Calcular Liquidación", type="primary", use_container_width=True):
    df = pd.DataFrame(datos_calculados)
    total_m3_unidades = df["M3"].sum()

    if total_m3_unidades > 0:
        # 1. Diferencia exacta entre el recibo y lo medido
        m3_diferencia_total = m3_consumo_total - total_m3_unidades
        num_unidades = len(df)

        # 2. Distribución equitativa de la diferencia
        adicional_por_unidad = m3_diferencia_total / num_unidades if num_unidades > 0 else 0

        # 3. Cálculo de valores finales
        df["M3 Final"] = df["M3"] + adicional_por_unidad
        df["Valor a Pagar"] = df["M3 Final"] * valor_m3_unitario

        # Mostrar Resumen informativo
        st.subheader("Resultados de la Liquidación")
        st.info(f"""
            **Desglose de diferencia en M3:**
            * Diferencia total de M3 a repartir: **{m3_diferencia_total:.3f} m3**
            * Ajuste por c/u: **{adicional_por_unidad:.3f} m3**
        """)

        # Formatear tabla para el usuario
        df_display = df.copy()
        df_display["M3 Individual"] = df_display["M3"].map("{:.3f}".format)
        df_display["Ajuste (+)"] = f"{adicional_por_unidad:.3f}"
        df_display["M3 + Diferencia"] = df_display["M3 Final"].map("{:.3f}".format)
        df_display["Total a Pagar"] = df_display["Valor a Pagar"].map("$ {:,.2f}".format)

        st.table(df_display[["Unidad", "M3 Individual", "Ajuste (+)", "M3 + Diferencia", "Total a Pagar"]])

        # Métricas de validación
        c1, c2 = st.columns(2)
        total_pagar_calc = df['Valor a Pagar'].sum()

        c1.metric("Total a pagar", f"$ {total_pagar_calc:,.2f}")
        c2.metric("Total M3 Finales", f"{df['M3 Final'].sum():.3f}")

        # --- NUEVO: BOTÓN DE DESCARGA PDF ---
        datos_pdf = {
            "mes": mes_periodo,
            "total": valor_total_recibo,
            "m3_recibo": m3_consumo_total,
            "valor_m3": valor_m3_unitario
        }

        pdf_output = generar_pdf(df, datos_pdf, adicional_por_unidad)

        st.download_button(
            label="📥 Descargar Liquidación en PDF",
            data=bytes(pdf_output),
            file_name=f"Liquidacion_{mes_periodo}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.success("✅ Liquidación completa.")