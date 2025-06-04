from datasets import load_dataset
import requests
import sacrebleu
import time

# Define the target languages and their codes
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

# Open output file to save BLEU scores
with open("bleu_scores_nllb.txt", "w", encoding="utf-8") as out_file:
    for lang_code, lang_name in languages.items():
        print(f"Evaluating {lang_name} ({lang_code})...")

        try:
            # Load the dataset
            dataset = load_dataset("allenai/nllb", split="train")
        except Exception as e:
            print(f"Failed to load dataset: {e}")
            out_file.write(f"{lang_name} ({lang_code}): Dataset load error.\n")
            continue

        # Filter dataset for the specific language pair
        filtered_dataset = [item for item in dataset if lang_code in item['translation'] and 'eng_Latn' in item['translation']]
        
        if not filtered_dataset:
            print(f"No data found for language pair eng_Latn-{lang_code}")
            out_file.write(f"{lang_name} ({lang_code}): No data found for language pair.\n")
            continue

        source_sentences = [item['translation']['eng_Latn'] for item in filtered_dataset]
        target_sentences = [item['translation'][lang_code] for item in filtered_dataset]

        hypotheses = []
        for i, src in enumerate(source_sentences):
            try:
                print(f"Translating sentence {i}: {src}")
                response = requests.post(
                    "http://172.16.3.193:8088/translate",
                    data={
                        "source_lang": "eng_Latn",
                        "target_lang": lang_code,
                        "text": src
                    },
                    timeout=10
                )
                print(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    translated = result.get("data", "").strip()
                    hypotheses.append(translated)
                else:
                    print(f"API error for sentence {i}: {response.status_code} - {response.text}")
                    hypotheses.append("")
            except Exception as e:
                print(f"Exception for sentence {i}: {e}")
                hypotheses.append("")

            # Be nice to the API
            time.sleep(0.1)

        # Save raw translations for inspection
        with open(f"translations_{lang_code}.txt", "w", encoding="utf-8") as f:
            for src, ref, hyp in zip(source_sentences, target_sentences, hypotheses):
                f.write(f"SRC: {src}\nREF: {ref}\nHYP: {hyp}\n\n")

        # Filter out empty translations
        filtered_hypotheses = []
        filtered_references = []
        for hyp, ref in zip(hypotheses, target_sentences):
            if hyp.strip():
                filtered_hypotheses.append(hyp)
                filtered_references.append(ref)

        # Skip BLEU if no valid translations
        if not filtered_hypotheses:
            print(f"Skipping BLEU for {lang_code}: No valid translations.")
            out_file.write(f"{lang_name} ({lang_code}): No valid translations.\n")
            continue

        # Compute BLEU
        bleu = sacrebleu.corpus_bleu(filtered_hypotheses, [filtered_references])
        print(f"{lang_name}: BLEU = {bleu.score:.2f}")
        out_file.write(f"{lang_name} ({lang_code}): {bleu.score:.2f}\n")
