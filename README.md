streamlit
google-generativeai
pillow


Multimodal AI Nutri-Assistant
System Overview
Nutri-Assistant AI is an interactive web application built with Streamlit and the Google Gemini 2.5 Flash API. Its primary goal is to act as a highly analytical health and nutrition co-pilot.

Unlike a standard chatbot, this system implements a Multi-Expert Consensus pattern via advanced prompt engineering. When a user inputs their data (goals, physical profile, clinical labs, or meal images), the system simulates a panel of specialists who evaluate the information from different angles before delivering a unified recommendation.

System Architecture Map
The following diagram illustrates the data flow from user interaction to AI output. GitHub will automatically render this Mermaid code as a visual diagram in your repository.

Fragmento de código
graph TD
    %% User Inputs
    U[User] -->|Text: Profile & Goals| UI[Streamlit Interface]
    U -->|Files: Labs / Images| UI
    
    %% Local Processing
    subgraph Frontend & Pre-processing
        UI --> Val[Session State Validation]
        Val --> PImg[Image Processing via PIL]
        Val --> PText[Clinical History Formatting]
    end
    
    %% AI Engine
    subgraph Artificial Intelligence Engine
        PImg --> Prompt[Contextual Prompt Assembly]
        PText --> Prompt
        Prompt --> API[Google Gemini 2.5 Flash API]
    end
    
    %% Simulated Multi-Agent Evaluation
    subgraph Simulated Multi-Expert System
        API --> AgN[Role: Clinical Nutrition]
        API --> AgC[Role: Cardiology / Metabolism]
        API --> AgE[Role: Endocrinology]
        AgN & AgC & AgE --> Sintesis[Synthesis & Consensus]
    end
    
    %% Output
    Sintesis --> Salida[Markdown Response Formatting]
    Salida --> UI
    UI -->|Result Visualization| U
Component Breakdown
1. UI and State Management (Streamlit)
st.session_state: Used to maintain conversational memory. Each interaction is stored in the history to provide continuous context, allowing the user to ask follow-up questions about their diets or labs.

File Uploader: Safely converts user-uploaded images into formats compatible with the Gemini vision model.

2. Multi-Expert Panel (Prompt Engineering)
The core system instruction forces the model to delay its final response until the data passes through several analytical layers:

Dietary Calculation Specialist: Analyzes portion sizes, estimates caloric intake, and macronutrient distribution from images.

Internal Medicine / Cardiology Specialist: Cross-references dietary data with the clinical lab history (e.g., glucose, triglycerides) provided by the user.

Sports Nutrition Specialist: Adjusts recommendations based on physical activity levels and specific goals (e.g., hypertrophy, caloric deficit).

3. Multimodal Processing
By leveraging Gemini 2.5 Flash, the system does not merely extract text from images (basic OCR). It performs semantic image understanding (identifying ingredients, cooking methods, and portion sizes) to give context to the user's text prompts.

Project Structure
Plaintext
nutri-assistant/
├── .streamlit/
│   └── secrets.toml         # Environment variables and API Keys (git ignored)
├── app.py                   # Main Streamlit execution file
├── requirements.txt         # Project dependencies
├── utils/
│   ├── prompt_manager.py    # Instruction templates for agents
│   └── image_processor.py   # Optimization functions using PIL
└── README.md                # Project documentation
Local Setup & Deployment
Clone the repository:

Bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
Create a virtual environment and install dependencies:

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
Configure your API Key:
Create the .streamlit folder and the secrets.toml file:

Ini, TOML
# .streamlit/secrets.toml
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
Run the application:

Bash
streamlit run app.py
