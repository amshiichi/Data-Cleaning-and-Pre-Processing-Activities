import glob
import json
import os
import re
import zipfile
import pandas as pd

# File extraction
zip_path = "json_files.zip"
extract_folder = "unzipped_jsons"
with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(extract_folder)

folder_path = os.path.join(extract_folder, "*.json")
json_files = glob.glob(folder_path)

# File Sorting
json_files.sort(key=lambda f: int(re.findall(r"\d+", os.path.basename(f))[0]) if re.findall(r"\d+", os.path.basename(f)) else 0)

all_elements = []
all_edges = []
all_story_analytics = []

for file_index, file_path in enumerate(json_files):
    file_name = os.path.basename(file_path)

    # Building ID Generation
    file_start_building_id = file_index * 100
    with open(file_path, "r") as f:
        buildings_list = json.load(f)

    # Loop through every building graph inside the current JSON file
    for local_b_id, building in enumerate(buildings_list):

        # Continuous global building ID across all files, but local building ID resets for each file
        custom_building_id = file_start_building_id + local_b_id

        bar_nodes = building.get("bar_nodes", {})
        edges = building.get("edges", {})
        stories = building.get("bar_id_in_stories", [])
        drift_ratios = building.get("drift_ratio", [])

        # Story-Level Mapping
        story_mapping = {}
        for story_idx, element_ids in enumerate(stories):
            for eid in element_ids:
                story_mapping[eid] = story_idx + 1

        # Structural Element Extraction and Data Flattening
        coords_arr = bar_nodes.get("end_point_locations", [])
        if_beam = bar_nodes.get("if_beam", [])
        if_roof = bar_nodes.get("if_roof_beam", [])
        if_boundary = bar_nodes.get("if_boundary_beam", [])
        cross_sec = bar_nodes.get("cross_section", [])
        deck_area = bar_nodes.get("metal_deck_area_on_beam", [])

        for i in range(len(coords_arr)):
            coords = coords_arr[i]
            cs_vector = cross_sec[i] if i < len(cross_sec) else [0] * 9

            clean_global_id = f"{custom_building_id}_{i}"

            element_row = {
                "global_element_id": clean_global_id,
                "source_file": file_name,
                "custom_building_id": custom_building_id,
                "local_building_id": local_b_id,
                "local_element_id": i,
                "story_level": story_mapping.get(i, None),
                "start_x": coords[0], "start_y": coords[1], "start_z": coords[2],
                "end_x": coords[3], "end_y": coords[4], "end_z": coords[5],
                # Handling missing values
                "if_beam": if_beam[i] if i < len(if_beam) else 0.0,
                "if_roof_beam": if_roof[i] if i < len(if_roof) else 0.0,
                "if_boundary_beam": if_boundary[i] if i < len(if_boundary) else 0.0,
                "metal_deck_area": deck_area[i] if i < len(deck_area) else 0.0
            }

            # Cross-Section Encoding (One-Hot Encoding for 9 categories)
            for idx, bit in enumerate(cs_vector):
                element_row[f"cross_section_cat_{idx}"] = bit

            all_elements.append(element_row)

        # Graph Connectivity Extraction
        edge_types = [
            ("column_column", "column_column_senders", "column_column_receivers"),
            ("beam_column", "beam_column_senders", "beam_column_receivers"),
            ("column_ground", "column_ground_senders", "column_ground_receivers")
        ]

        for category, send_key, recv_key in edge_types:
            senders = edges.get(send_key, [])
            receivers = edges.get(recv_key, [])

            for idx in range(min(len(senders), len(receivers))):
                s_local = senders[idx]
                r_local = receivers[idx]

                all_edges.append({
                    "source_file": file_name,
                    "custom_building_id": custom_building_id,
                    "connection_type": category,
                    "global_sender_id": f"{custom_building_id}_{s_local}",
                    "global_receiver_id": f"{custom_building_id}_{r_local}",
                    "local_sender_id": s_local,
                    "local_receiver_id": r_local
                })

        # Story-Level Drift Ratio Extraction
        for reverse_idx, drift_values_list in enumerate(reversed(drift_ratios)):
            story_row = {
                "source_file": file_name,
                "custom_building_id": custom_building_id,
                "story_level": reverse_idx,  # Last entry in the dr array is for Story 0
            }

            for val_idx, val in enumerate(drift_values_list):
                story_row[f"drift_ratio_case_{val_idx}"] = val

            all_story_analytics.append(story_row)

# Table creation and CSV Export
df_elements = pd.DataFrame(all_elements)
df_edges = pd.DataFrame(all_edges)
df_stories = pd.DataFrame(all_story_analytics)

df_elements.to_csv("all_structural_elements.csv", index=False)
df_edges.to_csv("all_structural_edges.csv", index=False)
df_stories.to_csv("all_story_analytics.csv", index=False)