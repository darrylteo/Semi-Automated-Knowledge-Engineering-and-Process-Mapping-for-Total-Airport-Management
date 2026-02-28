import os
import glob
import re
import numpy as np
import pandas as pd
from owlready2 import *

class TextSanitizer:
    """Utility class for string cleaning and formatting."""
    
    @staticmethod
    def trailing_spaces_to_underscores(text):
        """Replaces trailing whitespaces with underscores."""
        if not isinstance(text, str):
            return text
        # Count trailing spaces
        stripped = text.rstrip()
        diff = len(text) - len(stripped)
        return stripped + ('_' * diff)

    @staticmethod
    def clean_rdf_identifiers(df, columns):
        """Applies standard RDF-safe cleaning to specific columns."""
        for col in columns:
            if col in df.columns:
                # Cast to string first to prevent AttributeError on float/NaN values
                df[col] = df[col].apply(
                    lambda x: str(x).replace("(", "").replace(")", "").replace(" ", "_") if pd.notna(x) else x
                )
        return df

class DataProcessor:
    """Handles the transformation of raw triple CSVs into a structured DataFrame."""
    
    def __init__(self, folder_path="./data", file_pattern="extracted_triples_"):
        self.folder_path = folder_path
        self.file_pattern = file_pattern
        self.combined_df = None
        self.final_merged_df = None

    def load_and_combine(self):
        """Reads multiple CSV files and adds context-aware prefixes."""
        dfs = {}
        search_path = os.path.join(self.folder_path, f"{self.file_pattern}*.csv")
        
        for file_path in glob.glob(search_path):
            base_name = os.path.basename(file_path)
            prefix = base_name.replace(self.file_pattern, "").replace(".csv", "")
            
            df = pd.read_csv(file_path)
            df["Subject"] = prefix + ":_" + df["Subject"].astype(str)
            
            # Link sequential steps
            mask = df["Predicate"] == "hasNext"
            df.loc[mask, "Object"] = prefix + ":_" + df.loc[mask, "Object"].astype(str)
            
            dfs[prefix] = df
        
        if not dfs:
            raise FileNotFoundError(f"No files found matching {search_path}")
            
        self.combined_df = pd.concat(dfs, ignore_index=True)
        self._basic_cleanup()

    def _basic_cleanup(self):
        """Initial cleaning of the combined dataframe."""
        self.combined_df = self.combined_df.drop(["Good", "Alignment"], axis=1, errors='ignore')
        # Apply underscore replacement to object types (excluding Source Text)
        self.combined_df = self.combined_df.apply(
            lambda col: col.str.replace(" ", "_") 
            if col.dtype == "object" and col.name != "Source Text" else col
        )

    def generate_procedural_map(self):
        """Main logic for aggregating stakeholders, sequences, and source text."""
        # 1. Stakeholders
        df_agg = (
            self.combined_df[self.combined_df["Predicate"] == "hasStakeholder"]
            .groupby("Subject")["Object"]
            .apply(lambda x: ', '.join(x.astype(str)))
            .reset_index()
            .rename(columns={"Object": "Stakeholder"})
        )

        # 2. Sequential Logic
        df_hasNext = self.combined_df[self.combined_df["Predicate"] == "hasNext"]
        df_merged = df_agg.merge(df_hasNext[["Subject", "Object"]], on="Subject", how="left")
        df_merged.columns = ["ProcedureStep", "Stakeholder", "NextProcedureStep"]

        # Clean identifiers
        df_merged = TextSanitizer.clean_rdf_identifiers(df_merged, ["ProcedureStep", "NextProcedureStep"])

        # 3. Sequenced Items (Group by prefix)
        df_merged["group"] = df_merged["ProcedureStep"].str.extract(r"^(.*?):_")[0]
        df_merged["Sequenced_Item"] = "NaN"
        df_merged["NextProcedureStep"] = df_merged["NextProcedureStep"].replace("nan", np.nan)

        for group, group_df in df_merged.groupby("group"):
            unique_vals = pd.unique(pd.concat([group_df["ProcedureStep"], group_df["NextProcedureStep"]]).dropna())
            unique_str = ", ".join(unique_vals)
            df_merged.at[group_df.index[0], "Sequenced_Item"] = unique_str

        # 4. Pivot Source Text
        grouped_st = self.combined_df.groupby(["Subject", "Predicate"])["Source Text"].agg(", ".join).reset_index()
        pivoted = grouped_st.pivot(index="Subject", columns="Predicate", values="Source Text").reset_index()
        pivoted.columns = ["ProcedureStep", "NextProcedureStep_SourceText", "Stakeholder_SourceText"]
        
        # 5. Final Join
        final_df = df_merged.merge(pivoted, on="ProcedureStep", how="left")
        final_df["SourceText"] = final_df[["NextProcedureStep_SourceText", "Stakeholder_SourceText"]].apply(
            lambda x: " ".join(x.dropna()), axis=1
        )
        
        # Apply the trailing whitespace sanitization requested
        final_df["SourceText"] = final_df["SourceText"].apply(TextSanitizer.trailing_spaces_to_underscores)
        
        self.final_merged_df = final_df.drop(["group", "NextProcedureStep_SourceText", "Stakeholder_SourceText"], axis=1)
        return self.final_merged_df

class OntologyManager:
    """Manages Owlready2 ontology definition and population."""
    
    def __init__(self, iri="http://example.org/aviation_ontology#"):
        self.iri = iri
        self.ontology = get_ontology(iri)
        self.classes = {}
        self.props = {}
        self._define_schema()

    def _define_schema(self):
        """Sets up classes and properties in the ontology context."""
        with self.ontology:
            class Abstract_Procedure(Thing): pass
            class Improvised_Procedure(Abstract_Procedure): pass
            class Procedure(Abstract_Procedure): pass
            class Stakeholder(Thing): pass
            class Sequenced_Item(Thing): pass
            
            class hasStakeholder(ObjectProperty):
                domain = [Sequenced_Item]; range = [Stakeholder]
            class hasNext(ObjectProperty):
                domain = [Sequenced_Item]; range = [Sequenced_Item]
            class hasSequencedItem(ObjectProperty):
                domain = [Abstract_Procedure]; range = [Sequenced_Item]
            class SourceText(DataProperty):
                domain = [Sequenced_Item]; range = [str]

            self.classes = {
                "Procedure": Procedure,
                "Stakeholder": Stakeholder,
                "Sequenced_Item": Sequenced_Item
            }
            self.props = {
                "hasStakeholder": hasStakeholder,
                "hasNext": hasNext,
                "hasSequencedItem": hasSequencedItem,
                "SourceText": SourceText
            }

    def populate(self, df):
        """Populates the ontology directly from the DataFrame."""
        # Tracking dictionaries to ensure unique individuals
        prefix_inds = {}
        item_inds = {}
        stake_inds = {}

        # First Pass: Individuals and Direct Relationships
        for _, row in df.iterrows():
            subj_name = str(row["ProcedureStep"]).strip()
            prefix = subj_name.split(":", 1)[0]

            # Create/Get main Procedure and Sequenced_Item
            main_proc = prefix_inds.setdefault(prefix, self.classes["Procedure"](prefix))
            item = item_inds.setdefault(subj_name, self.classes["Sequenced_Item"](subj_name))

            # Handle Stakeholders
            if pd.notna(row["Stakeholder"]):
                for s_name in [s.strip() for s in str(row["Stakeholder"]).split(",") if s.strip()]:
                    s_name = s_name.replace(" ", "_")
                    s_ind = stake_inds.setdefault(s_name, self.classes["Stakeholder"](s_name))
                    if s_ind not in item.hasStakeholder:
                        item.hasStakeholder.append(s_ind)

            # Handle hasNext
            next_step = str(row["NextProcedureStep"])
            if next_step and next_step.lower() != "nan":
                next_name = next_step.strip().replace(" ", "_")
                next_ind = item_inds.setdefault(next_name, self.classes["Sequenced_Item"](next_name))
                if next_ind not in item.hasNext:
                    item.hasNext.append(next_ind)

            # Handle Source Text
            st_val = str(row["SourceText"]).strip()
            if st_val and st_val.lower() != "nan":
                if st_val not in item.SourceText:
                    item.SourceText.append(st_val)

        # Second Pass: Procedural Hierarchy
        for _, row in df.iterrows():
            seq_val = str(row["Sequenced_Item"])
            if seq_val and seq_val.lower() != "nan":
                items = [i.strip() for i in seq_val.split(",") if i.strip()]
                for i_name in items:
                    prefix = i_name.split(":", 1)[0]
                    if prefix in prefix_inds:
                        i_ind = item_inds.setdefault(i_name, self.classes["Sequenced_Item"](i_name))
                        if i_ind not in prefix_inds[prefix].hasSequencedItem:
                            prefix_inds[prefix].hasSequencedItem.append(i_ind)

    def save(self, filename="aviation_ontology.owl"):
        self.ontology.save(file=filename, format="rdfxml")
        print(f"Ontology saved to {filename}")

class TriplesToKG:
    """Controller class to run the full process with customizable parameters."""
    
    def __init__(self, folder_path="./data", file_pattern="extracted_triples_", iri="http://example.org/aviation_ontology#"):
        self.processor = DataProcessor(folder_path=folder_path, file_pattern=file_pattern)
        self.manager = OntologyManager(iri=iri)

    def run(self, output_filename="aviation_ontology.owl"):
        print(f"Initializing ABox Generation for folder: {self.processor.folder_path}...")
        self.processor.load_and_combine()
        data = self.processor.generate_procedural_map()
        
        print("Populating Ontology directly from memory...")
        self.manager.populate(data)
        self.manager.save(filename=output_filename)
        print("Pipeline finished successfully!")

if __name__ == "__main__":
    # Example of how a user can initialize with custom paths
    custom_folder = "./data" 
    custom_pattern = "extracted_triples_"
    custom_iri = "http://myproject.org/ontology#"
    custom_output = "final_output.owl"

    pipeline = TriplesToKG(
        folder_path=custom_folder,
        file_pattern=custom_pattern,
        iri=custom_iri
    )
    
    pipeline.run(output_filename=custom_output)