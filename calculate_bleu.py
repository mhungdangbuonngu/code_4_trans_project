from datasets import load_dataset
import requests
import sacrebleu
import time

languages = {
    "fra_Latn": "French",
    "jpn_Latn": "Japanese",
    "deu_Latn": "German",
    "kor_Hang": "Korean",
    "spa_Latn": "Spanish",
    "tha_Thai": "Thai",
    "lao_Laoo": "Lao",
    "khm_Khmr": "Khmer"
}

with open("bleu_scores.txt", "w", encoding="utf-8") as out_file:
    for lang_code, lang_name in languages.items():
        print(f"\nEvaluating {lang_name} ({lang_code})...")

        try:
            dataset = load_dataset("openlanguagedata/flores_plus", lang_code, split="devtest")
        except Exception as e:
            print(f"Failed to load {lang_code}: {e}")
            continue

        # Extract source and target sentences
        source_sentences = [x["text"] for x in dataset if x["glottocode"] == "eng_Latn"]
        target_sentences = [x["text"] for x in dataset if x["glottocode"] == lang_code]

        # Ensure the number of source and target sentences match
        if len(source_sentences) != len(target_sentences):
            print(f"Mismatch in number of source and target sentences for {lang_code}")
            continue

        hypotheses = []
        for i, src in enumerate(source_sentences):
            try:
                print(f"Translating {i + 1}/{len(source_sentences)}: {src[:40]}...")
                response = requests.post(
                    "http://172.16.3.193:8088/translate",
                    data={
                        "source_lang": "eng",
                        "target_lang": lang_code.split("_")[0],
                        "text": src
                    },
                    timeout=1
                )
                translated = response.text.strip()
            except Exception as e:
                print(f"API error at {i}: {e}")
                translated = ""
            hypotheses.append(translated)
            time.sleep(0.1)  # to prevent overload

        bleu = sacrebleu.corpus_bleu(hypotheses, [target_sentences])
        result = f"{lang_name} ({lang_code}): {bleu.score:.2f}"
        print(result)
        out_file.write(result + "\n")
