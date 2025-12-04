import streamlit as st
import re
from datetime import datetime
import anthropic

# Page configuration
st.set_page_config(
    page_title="Healthcare Buddy",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(to bottom right, #EBF4FF, #E0E7FF);
    }
    .stButton button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Anthropic client
try:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
except Exception as e:
    st.error("⚠️ API key not configured. Please add ANTHROPIC_API_KEY to Streamlit secrets.")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """Hello! I'm your Healthcare Buddy. I can help you with:

• Hospital services and appointment information  
• Basic symptom assessment  
• General health queries

How can I assist you today?""",
            "sentiment": "neutral",
            "timestamp": datetime.now(),
        }
    ]

# Medical terminology dictionaries
MEDICAL_ENTITIES = {
    "symptoms": [
        "fever", "headache", "cough", "nausea", "vomiting", "diarrhea", "fatigue",
        "pain", "ache", "dizzy", "dizziness", "weakness", "chills", "sweating",
        "bleeding", "rash", "itching", "swelling", "shortness of breath", "chest pain",
        "sore throat", "runny nose", "congestion", "sneezing", "wheezing", "cramps",
        "bloating", "constipation", "insomnia", "anxiety", "depression", "confusion",
    ],
    "body_parts": [
        "head", "eye", "eyes", "ear", "ears", "nose", "throat", "neck", "shoulder",
        "chest", "back", "abdomen", "stomach", "arm", "hand", "finger", "leg", "knee",
        "foot", "toe", "skin", "heart", "lungs", "liver", "kidney", "brain", "muscle",
        "joint", "bone", "teeth", "gums", "mouth", "tongue",
    ],
    "medications": [
        "aspirin", "ibuprofen", "acetaminophen", "tylenol", "advil", "paracetamol",
        "antibiotic", "antibiotics", "insulin", "inhaler", "antacid", "painkiller",
        "vitamin", "supplement", "medicine", "medication", "drug", "prescription",
    ],
}

# Common medical typos
MEDICAL_TYPOS = {
    "hedache": "headache",
    "hedake": "headache",
    "headach": "headache",
    "stomache": "stomach",
    "stomachache": "stomach ache",
    "diarhea": "diarrhea",
    "nausious": "nauseous",
    "painfull": "painful",
    "dizines": "dizziness",
    "temperture": "temperature",
    "symtom": "symptom",
    "symtoms": "symptoms",
    "medicin": "medicine",
    "perscription": "prescription",
    "antibotic": "antibiotic",
    "asprin": "aspirin",
    "ibuprofin": "ibuprofen",
    "febril": "fever",
    "cof": "cough",
    "cogh": "cough",
    "throaght": "throat",
    "cheast": "chest",
}

# Spell Correction Function
def correct_spelling(text):
    corrected_text = text
    corrections = []
    words = text.lower().split()

    for word in words:
        clean_word = re.sub(r"[^\w]", "", word)
        if clean_word in MEDICAL_TYPOS:
            corrected_word = MEDICAL_TYPOS[clean_word]
            corrections.append((clean_word, corrected_word))
            regex = re.compile(re.escape(clean_word), re.IGNORECASE)
            corrected_text = regex.sub(corrected_word, corrected_text)

    return corrected_text, corrections

# Named Entity Recognition Function
def extract_medical_entities(text):
    text_lower = text.lower()
    entities = {"symptoms": [], "body_parts": [], "medications": []}

    for symptom in MEDICAL_ENTITIES["symptoms"]:
        if re.search(r"\b" + re.escape(symptom) + r"\b", text_lower):
            entities["symptoms"].append(symptom)

    for body_part in MEDICAL_ENTITIES["body_parts"]:
        if re.search(r"\b" + re.escape(body_part) + r"\b", text_lower):
            entities["body_parts"].append(body_part)

    for medication in MEDICAL_ENTITIES["medications"]:
        if re.search(r"\b" + re.escape(medication) + r"\b", text_lower):
            entities["medications"].append(medication)

    entities["symptoms"] = list(set(entities["symptoms"]))
    entities["body_parts"] = list(set(entities["body_parts"]))
    entities["medications"] = list(set(entities["medications"]))

    return entities

# Sentiment Analysis Function
def analyze_sentiment(text):
    negative_words = [
        "pain", "hurt", "worried", "scared", "anxious", "bad", "severe",
        "terrible", "sick", "nausea", "dizzy", "weak", "vomit", "ache",
        "uncomfortable", "bleeding",
    ]
    positive_words = [
        "better", "good", "thank", "appreciate", "helped", "improved",
        "great", "relieved", "recovered",
    ]

    text_lower = text.lower()
    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)

    if neg_count > pos_count:
        return "negative"
    elif pos_count > neg_count:
        return "positive"
    return "neutral"

# Get AI response using Anthropic API
def get_ai_response(user_message, entities, conversation_history):
    # Build context from entities
    entity_context = ""
    if entities.get("symptoms"):
        entity_context += f"\nDetected symptoms: {', '.join(entities['symptoms'])}"
    if entities.get("body_parts"):
        entity_context += f"\nBody parts mentioned: {', '.join(entities['body_parts'])}"
    if entities.get("medications"):
        entity_context += f"\nMedications mentioned: {', '.join(entities['medications'])}"

    # Build conversation history for Claude
    messages = []
    for msg in conversation_history:
        if msg["role"] in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message + entity_context
    })

    # System prompt
    system_prompt = """You are a helpful healthcare assistant chatbot. Your role is to:

1. Provide general health information and guidance
2. Help with hospital-related queries (visiting hours, appointments, services)
3. Offer compassionate support for symptom discussions
4. Give practical advice for common health concerns

IMPORTANT GUIDELINES:
- Be empathetic and supportive
- Keep responses clear and concise
- For serious symptoms (chest pain, severe bleeding, difficulty breathing), strongly advise seeking immediate medical attention
- For appointments, direct users to call the hospital or use the online portal
- Visiting hours are typically 10am-8pm
- Never provide specific medical diagnoses
- Always remind users that you're providing general information, not medical advice
- Be warm and conversational

Format your responses in a friendly, easy-to-read way."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"I apologize, but I'm having trouble connecting right now. Error: {str(e)}"

# Display chat message with NLP analysis
def display_message(message):
    role = message["role"]
    content = message["content"]
    sentiment = message.get("sentiment", "neutral")

    sentiment_emoji = {"negative": "🤗", "positive": "😊", "neutral": "🤖"}

    if role == "user":
        st.markdown("**👤 You:**")
        st.info(content)

        if "entities" in message or "corrections" in message:
            with st.expander("🔍 NLP Analysis"):
                if message.get("corrections"):
                    st.markdown("**✏️ Spelling Corrections:**")
                    for original, corrected in message["corrections"]:
                        st.markdown(f"- `{original}` → `{corrected}`")

                if message["entities"].get("symptoms"):
                    st.markdown("**🩺 Symptoms Detected:**")
                    st.markdown(", ".join([f"💊 {s}" for s in message["entities"]["symptoms"]]))

                if message["entities"].get("body_parts"):
                    st.markdown("**🫀 Body Parts Mentioned:**")
                    st.markdown(", ".join([f"🫁 {bp}" for bp in message["entities"]["body_parts"]]))

                if message["entities"].get("medications"):
                    st.markdown("**💊 Medications Mentioned:**")
                    st.markdown(", ".join([f"💉 {m}" for m in message["entities"]["medications"]]))

    else:
        emoji = sentiment_emoji.get(sentiment, "🤖")
        st.markdown(f"**{emoji} Buddy:**")

        # Only show disclaimer on the LAST assistant message
        is_last = message == st.session_state.messages[-1]

        final_content = content
        if is_last:
            final_content += (
                "\n\n⚠️ **Medical Disclaimer:** I'm an informational assistant and "
                "not a medical professional. This is not a diagnosis. For medical "
                "advice or treatment, please consult a licensed professional."
            )

        if sentiment == "negative":
            st.error(final_content)
        elif sentiment == "positive":
            st.success(final_content)
        else:
            st.info(final_content)

# Main App
def main():
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.image("https://api.dicebear.com/7.x/bottts/svg?seed=healthcare", width=80)

    with col2:
        st.title("🏥 Healthcare Buddy")
        st.caption("AI-powered Healthcare Assistant with NLP")

    with col3:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()

    st.divider()

    st.warning(
        "⚠️ **Disclaimer:** This chatbot provides general information only and is not a substitute "
        "for professional medical advice."
    )

    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            display_message(m)

    st.divider()

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your message:",
            placeholder="Try: 'I have a hedache and fever' or 'What are your visiting hours?'",
            height=100,
        )
        submit_button = st.form_submit_button("Send 📤", use_container_width=True)

    if submit_button and user_input.strip():
        corrected_text, corrections = correct_spelling(user_input)
        entities = extract_medical_entities(corrected_text)
        sentiment = analyze_sentiment(corrected_text)

        st.session_state.messages.append(
            {
                "role": "user",
                "content": corrected_text,
                "original_content": user_input,
                "sentiment": sentiment,
                "entities": entities,
                "corrections": corrections,
                "timestamp": datetime.now(),
            }
        )

        with st.spinner("💭 Thinking..."):
            response = get_ai_response(corrected_text, entities, st.session_state.messages[:-1])

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "sentiment": sentiment,
                "timestamp": datetime.now(),
            }
        )

        st.rerun()

if __name__ == "__main__":
    main()
