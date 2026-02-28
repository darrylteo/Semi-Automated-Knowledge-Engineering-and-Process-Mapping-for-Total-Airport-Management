from utils.KG_to_txt import extract_triples
from utils.txt_to_swimlanes import parse_data, create_drawio_xml
from utils.triples_to_KG import TriplesToKG

# This file can be imported into Protégé to visualize the knowledge graph, or used for reasoning tasks, etc.
KG_FILE_PATH = "../results/aviation_KG.owl"
# This file can be imported into draw.io to visualize the swimlanes
SWIMLANE_FILE_PATH = "../results/airport_swimlanes.drawio"
# Not that important, just a quirk of ontologies
IRI = "http://myproject.org/ontology#"
TRIPLES_FOLDER = "../data"
TRIPLES_PATTERN = "extracted_triples_"

if __name__ == "__main__":
    # Convert the extracted triples into a knowledge graph (OWL format)
    pipeline = TriplesToKG(
        folder_path=TRIPLES_FOLDER,
        file_pattern=TRIPLES_PATTERN,
        iri=IRI
    )
    pipeline.run(output_filename=KG_FILE_PATH)
    # Now we have the KG, we can extract triples and create swimlanes
    raw_input = extract_triples(KG_FILE_PATH)
    data, tooltips = parse_data(raw_input)
    create_drawio_xml(data, tooltips=tooltips, filename=SWIMLANE_FILE_PATH)
