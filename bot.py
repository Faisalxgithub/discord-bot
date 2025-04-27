SPECIAL_QUESTIONS = {
    "tell me about you": "I'm just someone who loves chatting and helping ou!",
    "who are you": "I'm here to keep the conversation going and have fun!",
    "what are you": "I'm just another person hanging out here!",
}

def is_special_question(message):
    clean_message = message.lower().strip()
    for key in SPECIAL_QUESTIONS:
        if key in clean_message:
            return SPECIAL_QUESTIONS[key]
    return None