import os
import csv
import io
import time
import langextract as lx


# ---------------------------------------------------------------------------
# Text loading
# ---------------------------------------------------------------------------

def load_milestone_texts(
    data_folder: str = "./data",
    n_milestones: int = 16,
    full_filename: str = "milestones.txt",
) -> tuple[list[str], str]:
    """
    Read individual milestone text files and the combined milestones file.

    Returns
    -------
    milestone_texts : list[str]
        Texts for milestone1.txt … milestone{n_milestones}.txt
    milestone_full : str
        Contents of the combined milestones file.
    """
    milestone_texts = []
    for i in range(1, n_milestones + 1):
        path = os.path.join(data_folder, f"milestone{i}.txt")
        with open(path, "r", encoding="utf-8") as f:
            milestone_texts.append(f.read())

    full_path = os.path.join(data_folder, full_filename)
    with open(full_path, "r", encoding="utf-8") as f:
        milestone_full = f.read()

    return milestone_texts, milestone_full


# ---------------------------------------------------------------------------
# LangExtract runner
# ---------------------------------------------------------------------------

def run_extraction(
    milestone_texts: list[str],
    prompt_description: str,
    examples: list,
    model_id: str = "gemini-2.5-flash",
    max_workers: int = 1,
    sleep_secs: float = 4.0,
) -> list:
    """
    Run lx.extract() on each milestone text and return all results.

    Parameters
    ----------
    milestone_texts     : list of raw text strings (one per milestone)
    prompt_description  : domain prompt from config.py
    examples            : few-shot ExampleData list from config.py
    model_id            : Gemini model string
    max_workers         : concurrency (keep 1 for free-tier)
    sleep_secs          : delay between requests (free-tier rate limits)

    Returns
    -------
    all_results : list of LangExtract annotated-document objects
    """
    all_results = []

    for i, text in enumerate(milestone_texts):
        print(f"  Extracting milestone {i + 1}/{len(milestone_texts)}...")
        result = lx.extract(
            text_or_documents=text,
            prompt_description=prompt_description,
            examples=examples,
            model_id=model_id,
            max_workers=max_workers,
        )
        all_results.append(result)
        if i < len(milestone_texts) - 1:
            time.sleep(sleep_secs)

    return all_results


# ---------------------------------------------------------------------------
# Saving results
# ---------------------------------------------------------------------------


def results_to_csvs(
    all_results: list,
    output_folder: str = ".",
    filename_prefix: str = "extracted_triples_milestone_",
) -> list[str]:
    """
    Convert LangExtract results to per-milestone CSV files.

    Each CSV contains columns:
        Subject, Predicate, Object, Good, Source Text, Alignment, Class

    The 'Good' column is left as 0 for later manual annotation.

    Parameters
    ----------
    all_results     : list returned by run_extraction()
    output_folder   : directory where CSV files are written
    filename_prefix : prefix for output file names

    Returns
    -------
    saved_paths : list of file paths that were written
    """
    os.makedirs(output_folder, exist_ok=True)
    saved_paths = []

    for i, annotated_doc in enumerate(all_results):
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # Header — 'Good' and 'Alignment' are kept for manual annotation workflow
        writer.writerow(["Subject", "Predicate", "Object",
                        "Good", "Source Text", "Alignment", "Class"])

        for extraction in annotated_doc.extractions:
            subject = extraction.attributes.get("subject", "")
            predicate = extraction.attributes.get("predicate", "")
            object_val = extraction.attributes.get("object", "")
            alignment = getattr(extraction, "alignment_status", "unknown")
            class_name = extraction.extraction_class
            src_text = extraction.extraction_text.replace(
                "\n", " ")  # flatten newlines

            writer.writerow([subject, predicate, object_val,
                            0, src_text, alignment, class_name])

        out_path = os.path.join(output_folder, f"{filename_prefix}{i + 1}.csv")
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write(buffer.getvalue())

        saved_paths.append(out_path)
        print(f"  CSV saved to {out_path}")

    return saved_paths
