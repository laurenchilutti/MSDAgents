import re
from pathlib import Path
import yaml
import csv


def combine_yaml_files(file1_path, file2_path, output_path, replace_newlines=True):
    """
    Parses two YAML files containing query: answer mappings and combines them
    into a semicolon-separated file.
    """
    # Load YAML files (PyYAML automatically strips syntax quotes from keys)
    with open(file1_path, 'r', encoding='utf-8') as f1:
        data1 = yaml.safe_load(f1) or {}

    with open(file2_path, 'r', encoding='utf-8') as f2:
        data2 = yaml.safe_load(f2) or {}

    # Gather all unique queries while preserving key ordering
    queries = list(data1.keys())
    for q in data2.keys():
        if q not in queries:
            queries.append(q)

    # Write output file
    with open(output_path, 'w', encoding='utf-8', newline='') as out_file:
        writer = csv.writer(out_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        for query in queries:
            ans1 = data1.get(query, "")
            ans2 = data2.get(query, "")

            if replace_newlines:
                # Convert actual newlines to printable '\n' sequences so each record stays on one line
                if isinstance(ans1, str):
                    ans1 = ans1.replace('\r\n', '\\n').replace('\n', '\\n')
                if isinstance(ans2, str):
                    ans2 = ans2.replace('\r\n', '\\n').replace('\n', '\\n')

            writer.writerow([query, ans1, ans2])

    print(f"Successfully exported {len(queries)} query pairs to '{output_path}'.")

if __name__ == "__main__":
    # Replace file names with your actual input/output file paths
    combine_yaml_files("fms_chatbot.yaml", "fms_groundtruth.yaml", "fmsoutput.txt")
