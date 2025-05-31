import streamlit as st
import requests

st.title("🈯 Language Translator (Gemma 3B via Ollama)")

text = st.text_area("Enter text to translate:")
source_lang = st.text_input("Source Language (e.g., English)")
target_lang = st.text_input("Target Language (e.g., Spanish)")

if st.button("Translate"):
    if not text or not source_lang or not target_lang:
        st.warning("Please fill all fields.")
    else:
        with st.spinner("Translating..."):
            try:
                response = requests.post("http://localhost:5000/translate", json={
                    "text": text,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                })
                if response.status_code == 200:
                    result = response.json()
                    st.success("Translation:")
                    st.write(result["translation"])
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")
