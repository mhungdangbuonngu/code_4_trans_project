import streamlit as st
import requests
import io 
st.set_page_config(page_title="Language Translator", layout="centered")
st.title("🈯 Language Translator (Gemma3 4B via Ollama)")
source_lang = st.text_input("Source Language (e.g., English)")
target_lang = st.text_input("Target Language (e.g., Spanish)")
mode = st.radio("Choose input method:", ("✍️ Type text", "📂 Upload file"))
# Common validation
if not source_lang or not target_lang:
    st.warning("Please enter both source and target languages.")

else:
    if mode == "✍️ Type text":
        text_input = st.text_area("Enter text to translate:")

        if st.button("Translate Text"):
            if not text_input.strip():
                st.warning("Please enter text to translate.")
            else:
                with st.spinner("Translating..."):
                    try:
                        response = requests.post("http://localhost:5000/translate", json={
                            "text": text_input,
                            "source_lang": source_lang,
                            "target_lang": target_lang
                        })
                        if response.status_code == 200:
                            result = response.json()
                            st.success("Translation:")
                            st.write(result["translation"])
                        else:
                            st.error(f"API Error: {response.status_code}\n{response.text}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")
    elif mode == "📂 Upload file":
            uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])

            if uploaded_file:
                file_text = uploaded_file.read().decode("utf-8")

                if st.button("Translate File"):
                    with st.spinner("Translating file..."):
                        try:
                            response = requests.post("http://localhost:5000/translate", json={
                                "text": file_text,
                                "source_lang": source_lang,
                                "target_lang": target_lang
                            })
                            if response.status_code == 200:
                                result = response.json()
                                translated_text = result["translation"]

                                # Download button
                                st.success("Translation completed!")
                                st.download_button(
                                    label="📥 Download Translated File",
                                    data=translated_text.encode("utf-8"),
                                    file_name="translated_file.txt",
                                    mime="text/plain"
                                )
                            else:
                                st.error(f"API Error: {response.status_code}\n{response.text}")
                        except Exception as e:
                            st.error(f"Request failed: {e}")    