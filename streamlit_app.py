# -*- coding: utf-8 -*-
"""streamlit_app.py

Asistente Multimodal Nutricional con Streamlit y Gemini API (Multilingüe: Español / English)
"""

import io
import google.generativeai as genai
from PIL import Image
import streamlit as st

# ------------------------------
# CONFIG DE GOOGLE API KEY (SEGURO)
# ------------------------------
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error(
        "⚠️ No se encontró la API Key. Por favor confígurala en "
        ".streamlit/secrets.toml o en la sección Secrets de Streamlit Cloud."
    )
    st.stop()

# ------------------------------
# MODELO
# ------------------------------
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# ------------------------------
# INTERFAZ & SELECCIÓN DE IDIOMA
# ------------------------------
st.set_page_config(page_title="Nutri-Asistente IA", layout="centered")

# Selector de idioma en la barra lateral
with st.sidebar:
    st.header("🌐 Idioma / Language")
    lang = st.radio("Selecciona tu idioma / Select your language:", ["Español", "English"])

is_es = lang == "Español"

# Textos dinámicos según idioma
texts = {
    "title": "🧠 Nutri-Asistente Multimodal IA" if is_es else "🧠 Multimodal AI Nutri-Assistant",
    "subtitle": (
        "Sube tu estudio clínico (opcional) + platillo (opcional) + descripción de tu caso clínico con tus metas y obtén un análisis personalizado."
        if is_es
        else "Upload your lab test (optional) + meal photo (optional) + clinical description with your goals to receive a personalized analysis."
    ),
    "welcome_msg": (
        "👋 Hola, soy tu asistente de salud y nutrición. Para comenzar:\n"
        "1) ¿Cuál es tu edad, estatura y peso?\n"
        "2) ¿Tienes antecedentes como diabetes, hipertensión, colesterol alto o alguna otra enfermedad crónica?\n"
        "3) Explica tu caso clínico y metas en salud por esta consulta."
        if is_es
        else "👋 Hello! I am your health and nutrition assistant. To start:\n"
        "1) What is your age, height, and weight?\n"
        "2) Do you have any condition like diabetes, hypertension, high cholesterol, or other chronic disease?\n"
        "3) Explain your clinical case and health goals for this consultation."
    ),
    "input_placeholder": "Escribe tu respuesta..." if is_es else "Type your response...",
    "study_prompt": "Si tienes un **estudio clínico**, puedes subirlo a continuación (opcional)." if is_es else "If you have a **lab test/clinical study**, you can upload it below (optional).",
    "study_uploader_label": "Sube tu estudio clínico (opcional)" if is_es else "Upload your lab test (optional)",
    "skip_study_btn": "Continuar sin subir estudio clínico" if is_es else "Continue without lab test",
    "food_prompt": (
        "Ahora, si lo deseas, puedes subir una **imagen de tu platillo** (opcional) o presionar el botón para realizar el análisis directamente."
        if is_es
        else "Now, if you wish, you can upload a **photo of your meal** (optional) or press the button to analyze directly."
    ),
    "food_uploader_label": "Sube tu platillo (opcional)" if is_es else "Upload your meal (optional)",
    "skip_food_btn": "Continuar sin subir platillo / Analizar ahora" if is_es else "Continue without meal photo / Analyze now",
    "processing": "🧠 Procesando la información y generando tu análisis..." if is_es else "🧠 Processing information and generating your analysis...",
    "dish_img_label": "**Imagen del platillo analizado:**" if is_es else "**Analyzed meal image:**",
}

st.title(texts["title"])
st.write(texts["subtitle"])

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
        "content": texts["welcome_msg"],
    })
    with st.chat_message("assistant"):
        st.write(st.session_state.messages[-1]["content"])

# ----------------------------------------
# INPUT DEL USUARIO
# ----------------------------------------
user_input = st.chat_input(texts["input_placeholder"])

if user_input:
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
        st.write(texts["study_prompt"])

    image1 = st.file_uploader(
        texts["study_uploader_label"],
        type=["jpg", "jpeg", "png"],
        key="study_uploader",
    )
    skip_study = st.button(texts["skip_study_btn"])

    if image1 or skip_study:
        st.session_state.study_step_done = True
        if image1:
            st.session_state.image1_bytes = image1.read()
        st.rerun()

# ----------------------------------------------------------
# PASO 2: SUBIDA DEL PLATILLO (OPCIONAL) Y GENERACIÓN DE RESPUESTA
# ----------------------------------------------------------
if "study_step_done" in st.session_state and "done" not in st.session_state:
    with st.chat_message("assistant"):
        st.write(texts["food_prompt"])

    image2 = st.file_uploader(
        texts["food_uploader_label"],
        type=["jpg", "jpeg", "png"],
        key="food_uploader",
    )
    skip_food = st.button(texts["skip_food_btn"])

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

        target_language = "Spanish" if is_es else "English"

        prompt = f"""
SYSTEM:
You are an expert multimodal health and nutrition assistant. Analyze the user's information, lab tests (if provided), and meal image (if provided). Generate a comprehensive report tailored to their clinical case, metrics, and goals.

IMPORTANT: Response language MUST BE STRICTLY IN {target_language}.

USER DATA:
{user_data}
(A) Clinical study image: {"Provided" if tiene_estudio else "Not provided"}
(B) Meal image: {"Provided" if tiene_platillo else "Not provided"}

TASKS:
1. Analyze available data carefully.
2. Internally invoke several specialized "experts" (Nutrition, Cardiology, Endocrinology, Internal Medicine, Portion/Diet Calculator) to provide independent evaluations based on user goals.
3. Apply SELF-CONSISTENCY: have each expert reconsider their initial feedback and build a consensus with a confidence score/range.
4. Output a clear, actionable, and human-friendly structured report with:
   - Personal summary considering BMI and health metrics.
   - Key findings & lab test interpretation (if provided).
   - Meal identification, portion estimation, calories, macros, and fiber content (if image provided).
   - Personalized dietary recommendation tailored to goals and history.
   - Suggested dietary/meal adjustments.
   - Expert scores & multidisciplinary breakdown.
   - Final conclusion and follow-up questions for missing data.

CONSTRAINTS:
- Use probabilistic language, avoid definitive medical diagnoses.
- If urgent clinical flags are detected, state "Seek urgent medical attention".
- Natural text output only. NO JSON.

DISCLAIMER: Does not replace a professional medical consultation.
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
            st.write(texts["processing"])

        response = model.generate_content(inputs)

        with st.chat_message("assistant"):
            if tiene_platillo:
                st.write(texts["dish_img_label"])
                st.image(st.session_state.image2_bytes, use_column_width=True)
            st.write(response.text)

        st.session_state.messages.append(
            {"role": "assistant", "content": response.text}
        )
