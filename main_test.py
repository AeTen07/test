import google.generativeai as genai

genai.configure(api_key="你的API KEY")

models = genai.list_models()

for m in models:
    print(m.name)
