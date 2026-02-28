import re
import xml.etree.ElementTree as ET
import uuid
from collections import deque, defaultdict
from . import KG_to_txt

def parse_data(raw_data):
    """
    Parses the custom text format into a structured dictionary.
    - hasStakeholder now accumulates into a LIST (multi-stakeholder support)
    - hasDataProperty populates tooltips
    """
    data_struct = {}
    triples = re.findall(r"(\S+) -- (\S+) --> (.*)", raw_data)
    item_to_milestone = {}
    tooltips = {}

    for subj, pred, obj in triples:
        subj = subj.strip()
        pred_norm = pred.strip().lower()
        obj = obj.strip()

        if pred_norm == "sourcetext":
            tooltips[subj] = obj
            continue

        if pred_norm == "type" and obj == "Procedure":
            if subj not in data_struct:
                data_struct[subj] = {"items": {}}

        elif pred_norm == "hassequenceditem":
            if subj not in data_struct:
                data_struct[subj] = {"items": {}}
            if obj not in data_struct[subj]["items"]:
                data_struct[subj]["items"][obj] = {"stakeholders": [], "next": []}
            item_to_milestone[obj] = subj

        elif pred_norm == "hasstakeholder":
            milestone_id = item_to_milestone.get(subj)
            if milestone_id and subj in data_struct[milestone_id]["items"]:
                sh_list = data_struct[milestone_id]["items"][subj]["stakeholders"]
                if obj not in sh_list:
                    sh_list.append(obj)

        elif pred_norm == "hasnext":
            milestone_id = item_to_milestone.get(subj)
            if milestone_id and subj in data_struct[milestone_id]["items"]:
                data_struct[milestone_id]["items"][subj]["next"].append(obj)

    # Fallback: any item with no stakeholder assigned
    for milestone_id, content in data_struct.items():
        for item_id, meta in content["items"].items():
            if not meta["stakeholders"]:
                meta["stakeholders"] = ["Unassigned"]

    return data_struct, tooltips


# ---------------------------------------------------------------------------
# Topological level assignment (BFS longest path)
# ---------------------------------------------------------------------------

def calculate_vertical_order(items):
    adj = {item_id: [] for item_id in items}
    in_degree = {item_id: 0 for item_id in items}

    for item_id, meta in items.items():
        for target in meta["next"]:
            if target in adj:
                adj[item_id].append(target)
                in_degree[target] += 1

    levels = {item_id: 0 for item_id in items}
    queue = deque([i for i in items if in_degree[i] == 0])

    while queue:
        u = queue.popleft()
        for v in adj[u]:
            levels[v] = max(levels[v], levels[u] + 1)
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    return levels


# ---------------------------------------------------------------------------
# Draw.io XML generator
# ---------------------------------------------------------------------------

def create_drawio_xml(structured_data, tooltips, filename="swim.drawio"):
    mx_file = ET.Element("mxfile", host="app.diagrams.net", version="29.3.4")
    diagram = ET.SubElement(mx_file, "diagram", id=str(uuid.uuid4()), name="Page-1")
    mx_graph_model = ET.SubElement(
        diagram, "mxGraphModel",
        dx="1477", dy="806", grid="1", gridSize="10", guides="1",
        tooltips="1", connect="1", arrows="1", fold="1", page="1",
        pageScale="1", pageWidth="827", pageHeight="1169"
    )
    root = ET.SubElement(mx_graph_model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # Layout constants
    x_start            = 50
    y_start            = 50
    item_width         = 160
    item_height        = 60
    vertical_spacing   = 100   # px between BFS levels
    h_padding          = 20    # px between sibling nodes in the same slot
    lane_header_height = 30    # lane label strip height
    pool_header_height = 40    # pool label strip height
    inter_pool_gap     = 100   # gap between pools

    # id_map: item_id -> {stakeholder -> node_uuid}
    # Allows same-lane arrow routing for duplicated nodes
    id_map = {}   # item_id -> {sh_name: uuid}

    # Palette for multi-stakeholder node groups — one color per unique shared item
    # Colors are visually distinct, light enough for dark text to remain readable
    # ADD MORE IF NEEDED! Colors will be reused if there are more multi-shared items than colors.
    MULTI_COLORS = [
        "#fff2cc",  # yellow
        "#d5e8d4",  # green
        "#ffe6cc",  # orange
        "#e1d5e7",  # purple
        "#dae8fc",  # blue
        "#f8cecc",  # red/pink
        "#fff9c4",  # light yellow
        "#c8e6c9",  # mint
        "#ffe0b2",  # peach
        "#e8daef",  # lavender
    ]
    # Assign a color to each multi-stakeholder item_id encountered across all procedures
    multi_item_color = {}   # item_id -> hex color string
    color_counter = 0

    current_x = x_start

    for milestone_id, content in structured_data.items():
        items = content["items"]
        if not items:
            continue

        item_levels = calculate_vertical_order(items)
        max_level = max(item_levels.values())

        # Collect all unique stakeholder lanes needed
        all_stakeholders = []
        for meta in items.values():
            for sh in meta["stakeholders"]:
                if sh not in all_stakeholders:
                    all_stakeholders.append(sh)
        all_stakeholders = sorted(all_stakeholders)

        # ------------------------------------------------------------------
        # Count max duplicates per (stakeholder, level) to size lanes
        # A node with N stakeholders contributes 1 copy to each of those lanes
        # ------------------------------------------------------------------
        lane_level_counts = defaultdict(lambda: defaultdict(int))
        for item_id, item_meta in items.items():
            lvl = item_levels[item_id]
            for sh in item_meta["stakeholders"]:
                lane_level_counts[sh][lvl] += 1

        max_nodes_per_lane = {
            sh: max(lane_level_counts[sh].values()) if lane_level_counts[sh] else 1
            for sh in all_stakeholders
        }

        node_slot_width = item_width + h_padding
        lane_widths = {
            sh: max_nodes_per_lane[sh] * node_slot_width + h_padding
            for sh in all_stakeholders
        }

        pool_width  = sum(lane_widths.values())
        pool_height = (max_level + 1) * vertical_spacing + lane_header_height + 60

        # ------------------------------------------------------------------
        # Pool cell
        # ------------------------------------------------------------------
        pool_id    = str(uuid.uuid4())
        pool_label = milestone_id.replace("_", " ")
        pool_style = (
            "swimlane;whiteSpace=wrap;html=1;childLayout=stackLayout;horizontal=1;"
            "startSize=40;horizontalStack=1;stackSpacing=0;stackAnywhere=0;"
            "collapsible=1;dropTarget=0;fontStyle=1;fontSize=14;"
            "fillColor=#dae8fc;strokeColor=#6c8ebf;"
        )

        if milestone_id in tooltips:
            obj = ET.SubElement(root, "object", label=pool_label,
                                tooltip=tooltips[milestone_id], id=pool_id)
            pool_cell = ET.SubElement(obj, "mxCell")
        else:
            pool_cell = ET.SubElement(root, "mxCell", id=pool_id, value=pool_label)

        pool_cell.set("style", pool_style)
        pool_cell.set("vertex", "1")
        pool_cell.set("parent", "1")
        ET.SubElement(pool_cell, "mxGeometry", attrib={
            "x": str(current_x), "y": str(y_start),
            "width": str(pool_width), "height": str(pool_height),
            "as": "geometry"
        })

        # ------------------------------------------------------------------
        # Lane cells
        # ------------------------------------------------------------------
        lane_ids = {}
        acc_lane_x = 0
        for sh_name in all_stakeholders:
            lane_id = str(uuid.uuid4())
            lane_ids[sh_name] = lane_id
            lw = lane_widths[sh_name]

            lane_cell = ET.SubElement(
                root, "mxCell",
                id=lane_id, value=sh_name,
                style=(
                    "swimlane;html=1;startSize=30;container=1;collapsible=0;"
                    "dropTarget=0;fontStyle=1;fillColor=#f5f5f5;strokeColor=#666666;"
                ),
                vertex="1", parent=pool_id
            )
            ET.SubElement(lane_cell, "mxGeometry", attrib={
                "x": str(acc_lane_x), "y": str(pool_header_height),
                "width": str(lw),
                "height": str(pool_height - pool_header_height),
                "as": "geometry"
            })
            acc_lane_x += lw

        # ------------------------------------------------------------------
        # Node placement — one copy per stakeholder
        # ------------------------------------------------------------------
        lane_level_placed = defaultdict(lambda: defaultdict(int))

        for item_id, item_meta in items.items():
            lvl        = item_levels[item_id]
            clean_name = item_id.split(":")[-1].replace("_", " ")
            tooltip    = tooltips.get(item_id)

            is_multi = len(item_meta["stakeholders"]) > 1

            # Assign a unique group color the first time we see this multi-sh item
            if is_multi and item_id not in multi_item_color:
                multi_item_color[item_id] = MULTI_COLORS[color_counter % len(MULTI_COLORS)]
                color_counter += 1

            id_map.setdefault(item_id, {})

            for sh_name in item_meta["stakeholders"]:
                lw          = lane_widths[sh_name]
                slot_index  = lane_level_placed[sh_name][lvl]
                lane_level_placed[sh_name][lvl] += 1
                total       = lane_level_counts[sh_name][lvl]

                slot_width  = lw / total
                x_pos       = slot_width * slot_index + (slot_width - item_width) / 2
                y_pos       = lane_header_height + 10 + lvl * vertical_spacing

                node_uuid   = str(uuid.uuid4())
                id_map[item_id][sh_name] = node_uuid

                # Each multi-sh group gets its own color; single-owner nodes stay white
                fill_color  = multi_item_color[item_id] if is_multi else "#ffffff"
                node_style  = (
                    f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};"
                    "strokeColor=#333333;fontSize=11;arcSize=10;"
                )

                if tooltip:
                    obj_node = ET.SubElement(root, "object", label=clean_name,
                                             tooltip=tooltip, id=node_uuid)
                    node_cell = ET.SubElement(obj_node, "mxCell")
                else:
                    node_cell = ET.SubElement(root, "mxCell",
                                              id=node_uuid, value=clean_name)

                node_cell.set("style", node_style)
                node_cell.set("vertex", "1")
                node_cell.set("parent", lane_ids[sh_name])
                ET.SubElement(node_cell, "mxGeometry", attrib={
                    "x": str(int(x_pos)),
                    "y": str(int(y_pos)),
                    "width": str(item_width),
                    "height": str(item_height),
                    "as": "geometry"
                })

        current_x += pool_width + inter_pool_gap

    # ------------------------------------------------------------------
    # Flow arrows — same-lane only
    # source copy in lane L → target copy in lane L (if both exist)
    # ------------------------------------------------------------------
    flow_style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        "jettySize=auto;html=1;strokeColor=#444444;curved=0;"
        "exitX=0.5;exitY=1;exitDx=0;exitDy=0;"
        "entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
    )

    for milestone_id, content in structured_data.items():
        for item_id, item_meta in content["items"].items():
            for target_id in item_meta["next"]:
                if item_id not in id_map or target_id not in id_map:
                    continue

                src_copies = id_map[item_id]    # {sh -> uuid}
                tgt_copies = id_map[target_id]  # {sh -> uuid}

                for uuid_src in src_copies.values():
                    for uuid_tgt in tgt_copies.values():
                        edge_id   = str(uuid.uuid4())
                        edge_cell = ET.SubElement(
                            root, "mxCell",
                            id=edge_id, value="",
                            style=flow_style,
                            edge="1", parent="1",
                            source=uuid_src,
                            target=uuid_tgt
                        )
                        edge_cell.append(
                            ET.Element("mxGeometry", attrib={"relative": "1", "as": "geometry"})
                        )

    # ------------------------------------------------------------------
    # Write file
    # ------------------------------------------------------------------
    tree = ET.ElementTree(mx_file)
    ET.indent(tree, space="  ")
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"Success! Generated '{filename}'.")

if __name__ == "__main__":
    raw_input = KG_to_txt.extract_triples("airport_ontology_revised_newdp.owl")
    data, tooltips = parse_data(raw_input)
    create_drawio_xml(data, tooltips=tooltips, filename="test.drawio")