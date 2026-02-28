import textwrap
import langextract as lx
from langextract.data import Extraction

# Model & API settings
MODEL_ID = "gemini-2.5-flash"   # Model to use (free-tier compatible)
MAX_WORKERS = 1                     # Keep at 1 for free-tier rate limits
SLEEP_SECS = 4                     # Pause between requests (free-tier)

# Few-shot examples
# (built once at import time; milestone_texts are read in lang_IO.py)

# NOTE: The example below references MILESTONE 7 text. This is based on
# the expert-curated A-CDM Knowledge Graph.

EXAMPLES = [
    # --- MILESTONE 7 (In-Block) ---
    lx.data.ExampleData(
        text="""
        MILESTONE 7 In-Block	

Definition AIBT - Actual In-Block Time. This is the time that an aircraft arrives in-blocks.
(Equivalent to Airline/Handler ATA – Actual Time of Arrival, ACARS = IN)

Note: ACGT is considered to commence at AIBT

Origin and priority ACARS equipped aircraft or automated docking systems or ATC systems 
(e.g. A-SMGCS) or by manual input.

Timing The information is directly available after occurrence of the milestone.

Data Quality Data is available with an accuracy of +/- 1 minute.

Effect The occurrence of AIBT should trigger an update of downstream estimates: TOBT and 
TTOT are updated automatically or inserted manually by the Aircraft Operator / Ground 
Handler, calculated on the basis of the estimated turn-round period for the departing 
flight.

Procedures To check whether the AO/GH TOBT is consistent with the ATC Flight Plan. Network Op-
erations is informed when the TTOT changes by more than the agreed TTOT tolerance.

This check shall be performed to verify feasibility of the ATC Flight Plan given the updat-
ed TOBT or ATC Flight Plan. A TTOT tolerance is respected before Network Operations 
is informed on updated TTOT.

This process is triggered by 
n   Actual In Blocks Time: AIBT

Operational Status 
(changes to) IN-BLOCK

Action on CDM EIBT changes to AIBT
Operation (ACISP) TOBT and TTOT updated
        """,
        extractions=[
            # --- Stakeholder Triples (hasStakeholder) ---
            # 1. Observation of Plane In-Block (via ATC)
            Extraction(
                extraction_class="triple",
                extraction_text="Definition AIBT - Actual In-Block Time. This is the time that an aircraft arrives in-blocks.",
                attributes={"subject": "Plane in-block observed",
                            "predicate": "hasStakeholder",
                            "object": "ATC"}
            ),
            # 2. ACARS Input (via Airline)
            Extraction(
                extraction_class="triple",
                extraction_text="ACARS = IN",
                attributes={"subject": "ACARS status set to IN",
                            "predicate": "hasStakeholder",
                            "object": "Airline"}
            ),
            # 3. Automatic System Input (via Airport)
            Extraction(
                extraction_class="triple",
                extraction_text="""Origin and priority ACARS equipped aircraft or automated docking systems or ATC systems 
(e.g. A-SMGCS) or by manual input.""",
                attributes={"subject": "Plane auto-docking initiated",
                            "predicate": "hasStakeholder",
                            "object": "Airport"}
            ),
            # 4. Process Action: EIBT change (ACISP)
            Extraction(
                extraction_class="triple",
                extraction_text="Action on CDM EIBT changes to AIBT",
                attributes={"subject": "EIBT changed to AIBT",
                            "predicate": "hasStakeholder",
                            "object": "ACISP"}
            ),
            # 5. Process Action: TOBT/TTOT Update (AO/GH)
            Extraction(
                extraction_class="triple",
                extraction_text="""TOBT and 
TTOT are updated automatically or inserted manually by the Aircraft Operator / Ground 
Handler""",
                attributes={"subject": "Update TOBT and TTOT",
                            "predicate": "hasStakeholder",
                            "object": "AO/GH"}
            ),
            # 6. Process Action: TOBT/TTOT Update (ACISP)
            Extraction(
                extraction_class="triple",
                extraction_text="Operation (ACISP) TOBT and TTOT updated",
                attributes={"subject": "Update TOBT and TTOT in ACISP",
                            "predicate": "hasStakeholder",
                            "object": "ACISP"}
            ),
            # 7. Procedure: Consistency Check (AO/GH)
            Extraction(
                extraction_class="triple",
                extraction_text="Procedures To check whether the AO/GH TOBT is consistent with the ATC Flight Plan.",
                attributes={"subject": "Check if AO/GH TOBT is consistent with flight plan",
                            "predicate": "hasStakeholder",
                            "object": "AO/GH"}
            ),
            # 8. Procedure: Network Information (Network_Operations)
            Extraction(
                extraction_class="triple",
                extraction_text="""Network Op-
erations is informed when the TTOT changes by more than the agreed TTOT tolerance.""",
                attributes={"subject": "Receive updated TTOT",
                            "predicate": "hasStakeholder",
                            "object": "Network_Operations"}
            ),

            # --- Sequence MILESTONE 7 triples (hasNext) ---
            # 9. In-Block -> EIBT Change
            Extraction(
                extraction_class="triple",
                extraction_text="""Origin and priority ACARS equipped aircraft or automated docking systems or ATC systems 
(e.g. A-SMGCS) or by manual input.""",
                attributes={"subject": "Plane in-block observed",
                            "predicate": "hasNext",
                            "object": "EIBT changed to AIBT"}
            ),
            # 10. ACARS Input -> EIBT Change
            Extraction(
                extraction_class="triple",
                extraction_text="""Origin and priority ACARS equipped aircraft or automated docking systems or ATC systems 
(e.g. A-SMGCS) or by manual input.""",
                attributes={"subject": "ACARS status set to IN",
                            "predicate": "hasNext",
                            "object": "EIBT changed to AIBT"}
            ),
            # 11. Auto-docking -> EIBT Change
            Extraction(
                extraction_class="triple",
                extraction_text="""Origin and priority ACARS equipped aircraft or automated docking systems or ATC systems 
(e.g. A-SMGCS) or by manual input.""",
                attributes={"subject": "Plane auto-docking initiated",
                            "predicate": "hasNext",
                            "object": "EIBT changed to AIBT"}
            ),
            # 12. EIBT Change -> Update TOBT/TTOT
            Extraction(
                extraction_class="triple",
                extraction_text="""Effect The occurrence of AIBT should trigger an update of downstream estimates: TOBT and 
TTOT are updated automatically or inserted manually by the Aircraft Operator / Ground 
Handler""",
                attributes={"subject": "EIBT changed to AIBT",
                            "predicate": "hasNext",
                            "object": "Update TOBT and TTOT"}
            ),
            # 13. EIBT Change -> Update TOBT/TTOT in ACISP
            Extraction(
                extraction_class="triple",
                extraction_text="""
                Effect The occurrence of AIBT should trigger an update of downstream estimates: TOBT and 
TTOT are updated automatically
""",
                attributes={"subject": "EIBT changed to AIBT",
                            "predicate": "hasNext",
                            "object": "Update TOBT and TTOT in ACISP"}
            ),
            # 14. Update TOBT/TTOT -> Update TOBT/TTOT in ACISP
            Extraction(
                extraction_class="triple",
                extraction_text="Operation (ACISP) TOBT and TTOT updated",
                attributes={"subject": "Update TOBT and TTOT",
                            "predicate": "hasNext",
                            "object": "Update TOBT and TTOT in ACISP"}
            ),
            # 15. Update TOBT/TTOT -> Check consistency
            Extraction(
                extraction_class="triple",
                extraction_text="""
                Procedures To check whether the AO/GH TOBT is consistent with the ATC Flight Plan.
""",
                attributes={"subject": "Update TOBT and TTOT",
                            "predicate": "hasNext",
                            "object": "Check if AO/GH TOBT is consistent with flight plan"}
            ),
            # 16. Check consistency -> Receive updated TTOT
            Extraction(
                extraction_class="triple",
                extraction_text="""
                Procedures To check whether the AO/GH TOBT is consistent with the ATC Flight Plan. Network Op-
erations is informed when the TTOT changes by more than the agreed TTOT tolerance.
""",
                attributes={"subject": "Update TOBT and TTOT in ACISP",
                            "predicate": "hasNext",
                            "object": "Receive updated TTOT"}
            )
        ]
    )
]

PROMPT_DESCRIPTION = textwrap.dedent("""
    Role: You are a specialized aviation data engineer.
    Task: Convert the provided Airport Collaborative Decision Making (A-CDM) milestone text into a formal knowledge graph.
    
    Technical Glossary:
    - EIBT: Estimated In-Block Time
    - AIBT: Actual In-Block Time
    - TOBT: Target Off-Block Time
    - TTOT: Target Take-Off Time
    - ACISP: A-CDM Information Sharing Platform
    - AO/GH: Aircraft Operator / Ground Handler
    - ACARS: Aircraft Communications Addressing and Reporting System
    - (E)stimated, (T)arget, (C)alculated, (A)ctual, (X)taXi
    
    Extraction Rules:
    1. Identify every discrete operational event or "step" mentioned in the text.
    2. Map each step to its responsible stakeholder using the 'hasStakeholder' predicate.
    3. Determine the chronological sequence of events using the 'hasNext' predicate.                
    4. Exhaustive Extraction: Do not skip intermediate steps such as "System Updates" or "Consistency Checks."
    
    Constraint - Allowed Stakeholders:
    - ATC
    - Airline
    - Airport
    - ACISP
    - AO/GH
    - Network_Operations
    
    Output Format:
    Extractions must be structured as triples: (Subject, Predicate, Object).
    - Subject: The summarized name of the process step.
    - Predicate: Either 'hasStakeholder' or 'hasNext'.
    - Object: The Stakeholder name or the name of the following step.
                                     
    Note: Maintain separation between different Milestones; do not link the final step of one milestone to the first step of the next unless explicitly stated.
""")


def get_examples():
    return examples


def get_prompt_description():
    return prompt_description
