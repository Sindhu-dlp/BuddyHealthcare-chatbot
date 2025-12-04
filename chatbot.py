import streamlit as st
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Healthcare Buddy",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """Hello! I'm your Healthcare Buddy. I can help you with:

• Hospital services and appointment information  
• Basic symptom assessment  
• General health queries

Try asking me something like "I have a headache and fever" or "What are your visiting hours?"
""",
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

# Emergency keywords
EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "severe bleeding", "heavy bleeding", "unconscious", "seizure", 
    "heart attack", "stroke", "suicide", "suicidal"
]

# Common medical typos
MEDICAL_TYPOS = {
    "hedache": "headache", "hedake": "headache", "headach": "headache",
    "stomache": "stomach", "stomachache": "stomach ache",
    "diarhea": "diarrhea", "nausious": "nauseous", "painfull": "painful",
    "dizines": "dizziness", "temperture": "temperature",
    "symtom": "symptom", "symtoms": "symptoms",
    "medicin": "medicine", "perscription": "prescription",
    "antibotic": "antibiotic", "asprin": "aspirin",
    "ibuprofin": "ibuprofen", "febril": "fever",
    "cof": "cough", "cogh": "cough",
    "throaght": "throat", "cheast": "chest",
}

# Spell Correction Function
def correct_spelling(text):
    """Correct spelling using custom medical dictionary."""
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
    """Extract medical entities using rule-based matching."""
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

# Emergency Detection
def detect_emergency(text):
    """Detect emergency keywords."""
    text_lower = text.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

# Sentiment Analysis Function
def analyze_sentiment(text):
    """Simple rule-based sentiment analysis."""
    negative_words = [
        "pain", "hurt", "worried", "scared", "anxious", "bad", "severe",
        "terrible", "sick", "nausea", "dizzy", "weak", "vomit", "ache",
        "uncomfortable", "bleeding", "emergency", "urgent"
    ]
    positive_words = [
        "better", "good", "thank", "appreciate", "helped", "improved",
        "great", "relieved", "recovered",
    ]

    text_lower = text.lower()
    neg_count = sum(1 for word in negative_words if word in text_lower)
    pos_count = sum(1 for word in positive_words if word in text_lower)

    if neg_count > pos_count + 1:
        return "negative"
    elif pos_count > neg_count:
        return "positive"
    return "neutral"

# Response Generator
def get_response(user_message, sentiment, entities, is_emergency):
    """Generate rule-based response."""
    
    # Emergency check
    if is_emergency:
        return """🚨 **EMERGENCY DETECTED**

This sounds like it could be a medical emergency. Please:

• **Call 911 immediately** or
• **Go to the nearest Emergency Room**
• **Do not wait** - seek help right away

If you're with someone, stay with them and keep them comfortable until help arrives.

⚠️ This is not a diagnosis, but these symptoms require immediate medical attention."""

    # Sentiment-based prefix
    if sentiment == "negative":
        prefix = "I'm sorry you're not feeling well. I'm not a doctor, but I can share some general information.\n\n"
    elif sentiment == "positive":
        prefix = "I'm glad to hear that! Let me provide some helpful information.\n\n"
    else:
        prefix = "Thanks for sharing. I'll do my best to help with general guidance.\n\n"

    lines = []
    text_lower = user_message.lower()

    # Entity-based guidance
    if entities.get("symptoms"):
        symps = ", ".join(entities["symptoms"])
        lines.append(
            f"**Symptoms Detected:** {symps}\n\n"
            "**General Advice:**\n"
            "• If symptoms are severe or worsening, contact a doctor immediately\n"
            "• Stay hydrated and get plenty of rest\n"
            "• Keep track of when symptoms started and any changes\n"
            "• If symptoms persist for more than 2-3 days, consider seeing a healthcare provider"
        )

    if entities.get("body_parts"):
        bps = ", ".join(entities["body_parts"])
        lines.append(
            f"**Body Areas Mentioned:** {bps}\n\n"
            "It helps to note:\n"
            "• When the discomfort started\n"
            "• What makes it better or worse\n"
            "• Any recent injuries or activities"
        )

    if entities.get("medications"):
        meds = ", ".join(entities["medications"])
        lines.append(
            f"**Medications Mentioned:** {meds}\n\n"
            "**Medication Safety:**\n"
            "• Always follow dosage instructions\n"
            "• Don't mix medications without consulting a doctor\n"
            "• Keep a list of all medications you're taking\n"
            "• Inform your doctor about all supplements and over-the-counter drugs"
        )

    # FAQ responses
    if any(kw in text_lower for kw in ["visiting hours", "visit", "visitation"]):
        lines.append(
            "**🏥 Visiting Hours:**\n"
            "• General visiting hours: 10:00 AM - 8:00 PM daily\n"
            "• ICU and special units may have restricted hours\n"
            "• Please call the hospital for specific department hours\n"
            "• Visitor policies may change - check our website for updates"
        )

    if any(kw in text_lower for kw in ["appointment", "book", "schedule"]):
        lines.append(
            "**📅 Appointments:**\n"
            "• Call our appointment line: (555) 123-4567\n"
            "• Use our online booking portal at: www.hospital.com/book\n"
            "• For urgent matters, consider walk-in urgent care\n"
            "• Bring your insurance card and ID to your appointment"
        )

    if any(kw in text_lower for kw in ["insurance", "cost", "payment", "billing"]):
        lines.append(
            "**💳 Insurance & Billing:**\n"
            "• We accept most major insurance plans\n"
            "• Billing department: (555) 123-4568\n"
            "• Payment plans available\n"
            "• Bring your insurance card to every visit"
        )

    if any(kw in text_lower for kw in ["parking", "directions", "location"]):
        lines.append(
            "**🚗 Location & Parking:**\n"
            "• Address: 123 Medical Plaza, Healthcare City\n"
            "• Visitor parking: Levels 2-4 of main garage\n"
            "• First 2 hours free for visitors\n"
            "• Valet service available at main entrance"
        )

    # Default response
    if not lines:
        lines.append(
            "**How I Can Help:**\n\n"
            "I can provide information about:\n"
            "• General symptom guidance (not diagnosis)\n"
            "• Hospital services and visiting hours\n"
            "• Appointment scheduling\n"
            "• When to seek urgent care\n\n"
            "Could you tell me more about what you need help with?"
        )

    disclaimer = (
        "\n\n---\n"
        "⚠️ **Medical Disclaimer:** I'm an informational assistant, not a medical professional. "
        "This is not medical advice or diagnosis. For personal health concerns, please consult a licensed healthcare provider."
    )

    return prefix + "\n\n".join(lines) + disclaimer

# Display chat message
def display_message(message):
    """Display a chat message with NLP analysis."""
    role = message["role"]
    content = message["content"]
    sentiment = message.get("sentiment", "neutral")
    is_emergency = message.get("is_emergency", False)

    sentiment_emoji = {
        "negative": "🤗",
        "positive": "😊",
        "neutral": "🤖",
    }

    if role == "user":
        st.markdown("**👤 You:**")
        
        if is_emergency:
            st.error("🚨 **EMERGENCY KEYWORDS DETECTED**")
        
        st.info(content)

        # NLP Analysis
        if "entities" in message or "corrections" in message:
            with st.expander("🔍 View NLP Analysis", expanded=False):
                corrections = message.get("corrections", [])
                entities = message.get("entities", {})

                if corrections:
                    st.markdown("**✏️ Spelling Corrections:**")
                    for original, corrected in corrections:
                        st.markdown(f"• `{original}` → `{corrected}`")
                    st.divider()

                if entities.get("symptoms"):
                    st.markdown("**🩺 Symptoms Detected:**")
                    st.write(", ".join([f"💊 {s}" for s in entities["symptoms"]]))

                if entities.get("body_parts"):
                    st.markdown("**🫀 Body Parts:**")
                    st.write(", ".join([f"🫁 {bp}" for bp in entities["body_parts"]]))

                if entities.get("medications"):
                    st.markdown("**💊 Medications:**")
                    st.write(", ".join([f"💉 {m}" for m in entities["medications"]]))
    else:
        emoji = sentiment_emoji.get(sentiment, "🤖")
        st.markdown(f"**{emoji} Healthcare Buddy:**")
        st.markdown(content)

# Sidebar Analytics
def show_analytics():
    """Display conversation analytics in sidebar."""
    st.sidebar.header("📊 Analytics Dashboard")
    
    user_messages = [m for m in st.session_state.messages if m["role"] == "user"]
    
    if user_messages:
        # Total stats
        total_symptoms = sum(len(m.get("entities", {}).get("symptoms", [])) for m in user_messages)
        total_corrections = sum(len(m.get("corrections", [])) for m in user_messages)
        total_emergencies = sum(1 for m in user_messages if m.get("is_emergency", False))
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("💬 Messages", len(st.session_state.messages))
            st.metric("💊 Symptoms", total_symptoms)
        with col2:
            st.metric("✏️ Corrections", total_corrections)
            st.metric("🚨 Emergencies", total_emergencies)
        
        # Sentiment distribution
        sentiments = [m.get("sentiment", "neutral") for m in user_messages]
        st.sidebar.divider()
        st.sidebar.markdown("**😊 Sentiment Distribution:**")
        neg_count = sentiments.count("negative")
        pos_count = sentiments.count("positive")
        neu_count = sentiments.count("neutral")
        
        st.sidebar.write(f"• Negative: {neg_count}")
        st.sidebar.write(f"• Positive: {pos_count}")
        st.sidebar.write(f"• Neutral: {neu_count}")
    else:
        st.sidebar.info("Start chatting to see analytics!")
    
    st.sidebar.divider()
    
    # Export chat
    if st.sidebar.button("📥 Export Chat History"):
        chat_text = f"Healthcare Buddy - Chat History\n"
        chat_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        chat_text += "=" * 50 + "\n\n"
        
        for msg in st.session_state.messages:
            role = "You" if msg["role"] == "user" else "Healthcare Buddy"
            chat_text += f"{role}:\n{msg['content']}\n\n"
            chat_text += "-" * 50 + "\n\n"
        
        st.sidebar.download_button(
            label="💾 Download as TXT",
            data=chat_text,
            file_name=f"healthcare_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# Main App
def main():
    # Sidebar
    show_analytics()
    
    # Header
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.image("https://api.dicebear.com/7.x/bottts/svg?seed=healthcare", width=80)

    with col2:
        st.title("🏥 Healthcare Buddy")
        st.caption("NLP-Powered Healthcare Assistant | College Project Demo")

    with col3:
        if st.button("🗑️"):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()

    st.divider()

    # Info box
    with st.expander("ℹ️ About This Project", expanded=False):
        st.markdown("""
        **Healthcare Buddy** uses three core NLP techniques:
        
        1. **Spell Correction** - Custom medical dictionary for common typos
        2. **Named Entity Recognition (NER)** - Extracts symptoms, body parts, and medications
        3. **Sentiment Analysis** - Detects emotional tone of messages
        
        This is a rule-based system designed for educational purposes.
        """)

    # Display messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            display_message(message)

    st.divider()

    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_area(
                "Your message:",
                placeholder="Example: 'I have a hedache and fever' or 'What are your visiting hours?'",
                height=80,
                label_visibility="collapsed"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submit_button = st.form_submit_button("Send 📤", use_container_width=True)

    # Process input
    if submit_button and user_input.strip():
        # NLP Processing
        corrected_text, corrections = correct_spelling(user_input)
        entities = extract_medical_entities(corrected_text)
        sentiment = analyze_sentiment(corrected_text)
        is_emergency = detect_emergency(corrected_text)

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": corrected_text,
            "original_content": user_input,
            "sentiment": sentiment,
            "entities": entities,
            "corrections": corrections,
            "is_emergency": is_emergency,
            "timestamp": datetime.now(),
        })

        # Generate response
        with st.spinner("💭 Analyzing..."):
            response = get_response(corrected_text, sentiment, entities, is_emergency)

        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "sentiment": sentiment,
            "timestamp": datetime.now(),
        })

        st.rerun()

    # Footer
    st.divider()
    st.caption("⚠️ **Disclaimer:** This is an educational project. Not for actual medical use. Always consult healthcare professionals for medical advice.")

if __name__ == "__main__":
    main()
