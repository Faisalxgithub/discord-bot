SPECIAL_QUESTIONS = {
    "tell me about you": "I'm just here to grind roles sir",
    "who are you": "offcourse i'm human and i'm just here to grind for roles and learn about momentum finance",
    "what are you": "i'm human hehe🤣",
}

def is_special_question(message):
    clean_message = message.lower().strip()
    for key in SPECIAL_QUESTIONS:
        if key in clean_message:
            return SPECIAL_QUESTIONS[key]
    return None