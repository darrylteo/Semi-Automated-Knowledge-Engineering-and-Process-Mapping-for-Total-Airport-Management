from owlready2 import *

def extract_triples(ontology_path, output_file=None):
    """Extracts relationships from an OWL ontology and prints them in a format similar to OntoGraf.
    Args:        ontology_path (str): The file path or URL to the OWL ontology.
                 output_file (str, optional): The file path where extracted triples should be saved.
    Returns:     Returns all triples excluding class relationships (string format). Also saves to a file if output_file is provided.
    """
    # Load the ontology
    try:
        # If loading from a local file, ensure the path is correct
        onto = get_ontology(ontology_path).load()
        print(f"Loaded Ontology: {onto.base_iri}")
        print("Extracting OntoGraf-style relationships...\n")
    except Exception as e:
        print(f"Error loading ontology: {e}")
        return

    def get_name(entity):
        return entity.name if hasattr(entity, "name") else str(entity)

    # --- 1. EXTRACT CLASS-LEVEL RELATIONSHIPS (Restrictions) ---
    print(">> Class Relationships (Logic/Restrictions):")
    for cls in onto.classes():
        subject_name = get_name(cls)

        # In Owlready2, restrictions are found in is_a and equivalent_to
        # They appear as constructs like Restriction(property, type, value)
        for definition in cls.is_a + cls.equivalent_to:
            if isinstance(definition, Restriction):
                prop_name = get_name(definition.property)
                value = definition.value

                # Check if the filler (value) is a named class
                if isinstance(value, ThingClass):
                    print(f"{subject_name} -- {prop_name} --> {get_name(value)}")

    # --- 2. EXTRACT SUBCLASS RELATIONSHIPS (Hierarchy) ---
    print("\n>> Class Hierarchy (SubClassOf):")
    for cls in onto.classes():
        subject_name = get_name(cls)
        for parent in cls.is_a:
            if isinstance(parent, ThingClass):
                if parent != Thing:
                    print(f"{subject_name} -- subClassOf --> {get_name(parent)}")

    # --- 3. EXTRACT INDIVIDUAL RELATIONSHIPS ---
    # We are interested in this, only return these relationships, not the class-level ones
    output_lines = []
    print("\n>> Individual Assertions:")
    for ind in onto.individuals():
        subject_name = get_name(ind)

        # A. Type Assertions (rdf:type)
        for cls in ind.is_a:
            if isinstance(cls, ThingClass):
                line = f"{subject_name} -- type --> {get_name(cls)}"
                print(line)
                output_lines.append(line)

        # B. Object Property Assertions
        # Owlready2 allows accessing properties as attributes of the individual
        for prop in ind.get_properties():
            prop_name = get_name(prop)
            values = getattr(ind, prop.python_name)

            # Values is usually a list (for non-functional properties)
            if not isinstance(values, list):
                values = [values]

            for val in values:
                if isinstance(prop, ObjectPropertyClass):
                    # C. Object Property (Individual to Individual)
                    if isinstance(val, Thing):
                        line = f"{subject_name} -- {prop_name} --> {get_name(val)}"
                        print(line)
                        output_lines.append(line)
                elif isinstance(prop, DataPropertyClass):
                    # D. Data Property (Individual to Literal). Later used for tooltips
                    line = f"{subject_name} -- {prop_name} --> \"{val}\""
                    print(line)
                    output_lines.append(line)

    # Optionally, save the output to a file
    if output_file:
        try:
            with open(output_file, "w") as f:
                for line in output_lines:
                    f.write(line + "\n")
            print(f"\nExtracted triples saved to: {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")

    output_str = "\n".join(output_lines)
    return output_str


if __name__ == "__main__":
    # Replace with your actual file path
    # e.g., "data/test.rdf" or a URL
    myfile = "airport_ontology_revised_newdp.owl"
    output = extract_triples(myfile, output_file="extracted_triples.txt")
