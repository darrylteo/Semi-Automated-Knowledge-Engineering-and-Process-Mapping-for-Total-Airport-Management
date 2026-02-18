# Semi-Automated Knowledge Engineering and Process Mapping for Total Airport Management

This repository contains the code and datasets for the paper: **"Semi-Automated Knowledge Engineering and Process Mapping for Total Airport Management."**

The project focuses on extracting structured knowledge from the **Eurocontrol A-CDM** implementation manual to build a representative Knowledge Graph for airport operations, and evaluating the results for short-context and long-context information retrieval.

---

## Repository Structure

### `./data/`
Contains the source documentation and text conversions used for extraction.
* `milestones.pdf`: The original source document (Eurocontrol A-CDM manual).
* `milestones.txt`: The full source document converted from PDF to text.
* `milestone{i}.txt`: Segmented text files used for modular processing.
> *Note: Text conversion was performed using a free online .pdf to .txt processor (https://tools.pdf24.org/en/pdf-to-txt).*

### `./results/`
Contains the output of the extraction process.
* `extraction_results.csv`: The raw triples/data extracted via **LangExtract**.
* **Manual Annotation**: The column labeled `Good` in the CSV was manually annotated to validate the accuracy and relevance of the extracted knowledge.

### Source Code
* `getTriplesLang.ipynb`: The primary Jupyter Notebook containing the logic to process the text, perform triple extraction, and construct the Knowledge Graph.

---

## Citation

If you use this code or data in your research, please cite:

> *[Insert your full paper citation here]*
