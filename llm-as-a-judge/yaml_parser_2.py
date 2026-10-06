import csv
import yaml


def combine_three_yamls(
    file1_path, file2_path, file3_path, output_path, replace_newlines=True
):
  """Parses three YAML files containing query: answer/eval mappings and combines

  them into a semicolon-separated file.
  """

  def clean_value(val):
    """Converts newlines to '\\n' for strings to keep rows on a single line."""
    if replace_newlines and isinstance(val, str):
      return val.replace('\r\n', '\\n').replace('\n', '\\n')
    return val if val is not None else ''

  # Load YAML files
  with open(file1_path, 'r', encoding='utf-8') as f1:
    data1 = yaml.safe_load(f1) or {}

  with open(file2_path, 'r', encoding='utf-8') as f2:
    data2 = yaml.safe_load(f2) or {}

  with open(file3_path, 'r', encoding='utf-8') as f3:
    data3 = yaml.safe_load(f3) or {}

  # Gather all unique queries across all 3 files in order
  queries = list(data1.keys())
  for q in list(data2.keys()) + list(data3.keys()):
    if q not in queries:
      queries.append(q)

  # Write output file
  with open(output_path, 'w', encoding='utf-8', newline='') as out_file:
    writer = csv.writer(out_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    for query in queries:
      ans1 = clean_value(data1.get(query, ''))
      ans2 = clean_value(data2.get(query, ''))

      # Safely extract dictionary values from YAML3
      entry3 = data3.get(query, {})
      if isinstance(entry3, dict):
        score3 = entry3.get('score', '')
        reasoning3 = clean_value(entry3.get('reasoning', ''))
      else:
        score3 = ''
        reasoning3 = clean_value(entry3)

      # Output row: query; yaml1 answer; yaml2 answer; yaml3 score; yaml3 reasoning
      writer.writerow([query, ans1, ans2, score3, reasoning3])

  print(f"Successfully exported {len(queries)} rows to '{output_path}'.")


if __name__ == '__main__':
  combine_three_yamls(
      'fre_chatbot.yaml', 'fre_groundtruth.yaml', 'fre_llm_as_a_judge_results.yaml', 'freoutput_combined.txt'
  )
