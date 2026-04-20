import google.generativeai as genai

genai.configure(api_key="AIzaSyCeHCeUDsrOHP0Fziqyr-2vqH7GR1W73Bk")

models = genai.list_models()

for m in models:
    print(m.name, "->", m.supported_generation_methods)
