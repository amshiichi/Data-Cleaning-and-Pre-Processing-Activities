import pandas as pd
import numpy as np

FILE = "lsdse_json2table.xlsx"
SHEET = "structural_elements"
TOLERANCE = 0.01

df = pd.read_excel(FILE, sheet_name=SHEET, skiprows=[1])

columns = df[df["if_beam"] == 0].copy()

results = []

for building_id in sorted(columns["continuous_building_id"].unique()):

    bldg = columns[columns["continuous_building_id"] == building_id]

    x_lines = sorted(np.round(bldg["start_x"].astype(float).unique(), 3))
    y_lines = sorted(np.round(bldg["start_y"].astype(float).unique(), 3))

    if len(x_lines) < 2:
        continue

    if len(y_lines) < 2:
        continue

    coords = set(zip(
        np.round(bldg["start_x"].astype(float), 3),
        np.round(bldg["start_y"].astype(float), 3)
    ))

    expected = len(x_lines) * len(y_lines)
    actual = len(coords)

    if actual != expected:
        continue

    x_spans = np.diff(x_lines)
    y_spans = np.diff(y_lines)

    if np.std(x_spans) > TOLERANCE:
        continue

    if np.std(y_spans) > TOLERANCE:
        continue

    z_values = sorted(set(
        np.round(
            pd.concat([bldg["start_z"], bldg["end_z"]]).astype(float),
            3
        )
    ))

    if len(z_values) < 2:
        continue

    story_heights = np.diff(z_values)

    if np.std(story_heights) > TOLERANCE:
        continue

    floor_count = len(z_values) - 1
    story_height = round(float(np.mean(story_heights)), 3)

    bay_count_x = len(x_lines) - 1
    bay_count_y = len(y_lines) - 1

    bay_width_x = round(float(np.mean(x_spans)), 3)
    bay_width_y = round(float(np.mean(y_spans)), 3)

    results.append({
        "Building_ID": int(building_id),
        "Floor_Count": floor_count,
        "Story_Height": story_height,
        "Bay_Count_X": bay_count_x,
        "Bay_Width_X": bay_width_x,
        "Bay_Count_Y": bay_count_y,
        "Bay_Width_Y": bay_width_y
    })

output = pd.DataFrame(results)

output.to_excel("regular_buildings.xlsx", index=False)