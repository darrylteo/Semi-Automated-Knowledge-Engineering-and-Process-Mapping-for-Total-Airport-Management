import os
from utils.lang_config import EXAMPLES, PROMPT_DESCRIPTION, MODEL_ID, MAX_WORKERS, SLEEP_SECS
from utils.lang_io import load_milestone_texts, run_extraction, results_to_csvs

# ---------------------------------------------------------------------------
# Configuration — adjust paths and filenames here
# ---------------------------------------------------------------------------
DATA_FOLDER = "../data"
N_MILESTONES = 1
CSV_OUTPUT_FOLDER = "../results"
CSV_PREFIX = "extracted_triples_milestone_"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== Step 1: Loading milestone texts ===")
    milestone_texts, _ = load_milestone_texts(
        data_folder=DATA_FOLDER,
        n_milestones=N_MILESTONES,
    )

    print(
        f"\n=== Step 2: Running LangExtract on {len(milestone_texts)} milestones ===")
    all_results = run_extraction(
        milestone_texts=milestone_texts,
        prompt_description=PROMPT_DESCRIPTION,
        examples=EXAMPLES,
        model_id=MODEL_ID,
        max_workers=MAX_WORKERS,
        sleep_secs=SLEEP_SECS,
    )

    print("\n=== Step 3: Converting results to CSV ===")
    results_to_csvs(
        all_results=all_results,
        output_folder=CSV_OUTPUT_FOLDER,
        filename_prefix=CSV_PREFIX,
    )

    print("\n Extraction pipeline complete.")


if __name__ == "__main__":
    os.environ["LANGEXTRACT_API_KEY"] = "YOUR API KEY HERE"
    main()
