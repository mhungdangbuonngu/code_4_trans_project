import os
import requests
import sacrebleu

# ── Settings ───────────────────────────────────────────────
src_lang = "eng_Latn"
lang_pairs = {
    "fra_Latn": "French",
    "jpn_Latn": "Japanese",
    "deu_Latn": "German",
    "kor_Hang": "Korean",
    "spa_Latn": "Spanish",
    "tha_Thai": "Thai",
    "lao_Laoo": "Lao",
    "khm_Khmr": "Khmer",
}
api_url = "http://172.16.3.193:8088/translate"

data_dir   = "/mnt/c/Users/PC/Downloads/flores_translations/flores_translations"
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

bleu_report = []

# ── Main loop ───────────────────────────────────────────────
for lang_code, lang_name in lang_pairs.items():
    print(f"\n🔄 Processing English → {lang_name} ({lang_code})")

    # Paths
    ref_file = f"flores200-{src_lang}-{lang_code}-devtest.hyp"
    src_file = f"flores200-{lang_code}-{src_lang}-devtest.hyp"
    ref_path = os.path.join(data_dir, ref_file)
    src_path = os.path.join(data_dir, src_file)
    hyp_path = os.path.join(output_dir, ref_file)

    # Load source and reference lines
    with open(src_path, "r", encoding="utf-8") as f:
        src_lines = [line.strip() for line in f]
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_lines = [line.strip() for line in f]

    assert len(src_lines) == len(ref_lines), f"Line count mismatch for {lang_code}"

    # Translate via API
    hypotheses = []
    for i, src in enumerate(src_lines):
        print(f"Translating sentence {i + 1}/{len(src_lines)}")
        try:
            response = requests.post(
                api_url,
                data={
                    "source_lang": src_lang,
                    "target_lang": lang_code,
                    "text": src
                },
                timeout=10
            )
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                translated = response.json().get("data", "").strip()
                hypotheses.append(translated)
            else:
                print(f"API error: {response.status_code} - {response.text}")
                hypotheses.append("")
        except Exception as e:
            print(f"Exception on sentence {i}: {e}")
            hypotheses.append("")

    # Save hypotheses
    with open(hyp_path, "w", encoding="utf-8") as f:
        for line in hypotheses:
            f.write(line + "\n")

    # BLEU score
    bleu = sacrebleu.corpus_bleu(hypotheses, [ref_lines])
    bleu_line = f"{lang_name} ({lang_code}): BLEU = {bleu.score:.2f}"
    bleu_report.append(bleu_line)
    print(f"✅ {bleu_line}")

# Save summary
bleu_txt = os.path.join(output_dir, "bleu_scores.txt")
with open(bleu_txt, "w", encoding="utf-8") as f:
    f.write("\n".join(bleu_report))

print(f"\n📄 BLEU scores saved to: {bleu_txt}")
