import google.generativeai as genai

genai.configure(api_key="AIzaSyAKE7etexSgsiI41vjHnXg3UcUVNJoSEhE")

models = genai.list_models()

for m in models:
    print(m.name)
