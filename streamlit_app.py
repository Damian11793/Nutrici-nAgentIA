# -*- coding: utf-8 -*-
"""Agente.py

Asistente Multimodal Nutricional con Streamlit y Gemini API
"""

import io
import google.generativeai as genai
from PIL import Image
import streamlit as st

# ------------------------------
# CONFIG DE GOOGLE API KEY (SEGURO)
# ------------------------------
# La API Key se lee directamente desde los secretos de Streamlit (st.secrets)
# sin exponerla directamente en el código fuente.
if "GEMINI_API_KEY" in st.secrets:
  api_key = st.secrets["GEMINI_API_KEY"]
  genai.configure(api_key=api_key)
else:
  st.error(
      "⚠️ No se encontró la API Key. Por favor confígurala en"
      " .streamlit/secrets.toml o en la sección Secrets de Streamlit Cloud."
  )
  st.stop()

# ------------------------------
# MODELO
# ------------------------------
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# ------------------------------
# INTERFAZ
# ------------------------------
st.set_page_config(page_title="Nutri-Asistente IA", layout="centered")
st.title("🧠 Nutri-Asistente Multimodal IA")
st.write(
    "Sube tu estudio clínico (opcional) + platillo (opcional) + descripción de"
    " tu caso clínico con tus metas y obtén un análisis personalizado."
)

# Para simular conversación tipo ChatGPT
if "messages" not in st.session_state:
  st.session_state.messages = []

# Mostrar historial de mensajes
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.write(msg["content"])

# ----------------------------------------
# PRIMER MENSAJE DEL ASISTENTE
# ----------------------------------------
if len(st.session_state.messages) == 0:
  st.session_state.messages.append({
      "role": "assistant",
      "content": (
          "👋 Hola, soy tu asistente de salud y nutrición. Para comenzar:\n1)"
          " ¿Cuál es tu edad, estatura y peso?\n2) ¿Tienes antecedentes como"
          " diabetes, hipertensión, colesterol alto o alguna otra enfermedad"
          " crónica?\n3) Explica tu caso clínico y metas en salud por esta"
          " consulta."
      ),
  })
  with st.chat_message("assistant"):
    st.write(st.session_state.messages[-1]["content"])

# ----------------------------------------
# INPUT DEL USUARIO
# ----------------------------------------
user_input = st.chat_input("Escribe tu respuesta...")

if user_input:
  # Guardar mensaje
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.write(user_input)

# ----------------------------------------------------------
# PASO 1: SUBIDA DEL ESTUDIO CLÍNICO (OPCIONAL)
# ----------------------------------------------------------
last_user_message = None
for msg in reversed(st.session_state.messages):
  if msg["role"] == "user":
    last_user_message = msg["content"]
    break

if last_user_message and "study_step_done" not in st.session_state:
  with st.chat_message("assistant"):
    st.write(
        "Si tienes un **estudio clínico**, puedes subirlo a continuación"
        " (opcional)."
    )

  image1 = st.file_uploader(
      "Sube tu estudio clínico (opcional)",
      type=["jpg", "jpeg", "png"],
      key="study_uploader",
  )
  skip_study = st.button("Continuar sin subir estudio clínico")

  if image1 or skip_study:
    st.session_state.study_step_done = True
    if image1:
      st.session_state.image1_bytes = image1.read()
    st.experimental_rerun()

# ----------------------------------------------------------
# PASO 2: SUBIDA DEL PLATILLO (OPCIONAL) Y GENERACIÓN DE RESPUESTA
# ----------------------------------------------------------
if "study_step_done" in st.session_state and "done" not in st.session_state:
  with st.chat_message("assistant"):
    st.write(
        "Ahora, si lo deseas, puedes subir una **imagen de tu platillo**"
        " (opcional) o presionar el botón para realizar el análisis"
        " directamente."
    )

  image2 = st.file_uploader(
      "Sube tu platillo (opcional)",
      type=["jpg", "jpeg", "png"],
      key="food_uploader",
  )
  skip_food = st.button("Continuar sin subir platillo / Analizar ahora")

  if image2 or skip_food:
    st.session_state.done = True
    if image2:
      st.session_state.image2_bytes = image2.read()

    # Extraer datos del usuario
    user_data = "\n".join([
        msg["content"]
        for msg in st.session_state.messages
        if msg["role"] == "user"
    ])

    # Determinar disponibilidad de imágenes
    tiene_estudio = "image1_bytes" in st.session_state
    tiene_platillo = "image2_bytes" in st.session_state

    prompt = f"""
SISTEMA:
Eres un asistente multimodal experto en salud y nutrición. Analiza los datos del usuario, el estudio clínico (si se incluye) y el platillo (si se incluye), y produce un reporte detallado en base al caso clínico, metas y métricas compartidas.

USUARIO:
{user_data}
(A) Imagen del estudio clínico: {"Proporcionada" if tiene_estudio else "No proporcionada"}
(B) Imagen del platillo: {"Proporcionada" if tiene_platillo else "No proporcionada"}

TAREAS:
1. Analizar la información disponible.
2. Invocar internamente a varios "expertos" especializados (Nutrición, Cardiología, Endocrinología, Medicina Interna, y Calculador de Porciones/Dietas) que emitan su análisis independiente adaptado a las metas indicadas.
3. Aplicar SELF-CONSISTENCY: pedir a cada experto reconsiderar la evaluación y generar un consenso con intervalo/nivel de confianza.
4. Generar un informe estructurado claro, accionable y humano con:
   - Resumen rápido personalizado considerando IMC y métricas de salud.
   - Hallazgos clave e interpretación de estudios (si se enviaron).
   - Identificación del platillo, estimación de porciones, calorías, macronutrientes y fibra (si se envió imagen).
   - Recomendación dietética personalizada acorde a metas e historial.
   - Sugerencias de ajustes en la alimentación/platillo.
   - Puntuaciones por experto y análisis multidisciplinario.
   - Conclusión final y preguntas pendientes sobre datos faltantes.

RESTRICCIONES:
- Lenguaje probabilístico, no diagnósticos definitivos.
- Si detectas urgencia clínica, indica "Buscar atención médica urgente".
- Formato en texto natural estructurado. NO JSON.

DISCLAIMER: No sustituye una consulta médica.
"""

    inputs = [prompt]

    if tiene_estudio:
      inputs.append(
          {"mime_type": "image/jpeg", "data": st.session_state.image1_bytes}
      )

    if tiene_platillo:
      inputs.append(
          {"mime_type": "image/jpeg", "data": st.session_state.image2_bytes}
      )

    with st.chat_message("assistant"):
      st.write("🧠 Procesando la información y generando tu análisis...")

    response = model.generate_content(inputs)

    with st.chat_message("assistant"):
      if tiene_platillo:
        st.write("**Imagen del platillo analizado:**")
        st.image(st.session_state.image2_bytes, use_column_width=True)
      st.write(response.text)

    st.session_state.messages.append(
        {"role": "assistant", "content": response.text}
    )
