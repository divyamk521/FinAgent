from config import config

print("GROQ:", config.GROQ_API_KEY)
print("FINLIGHT:", config.FINLIGHT_API_KEY)
print("MODEL:", config.LLM_MODEL)

print("Validation:", config.validate())