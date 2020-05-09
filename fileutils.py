import json


def read_json_file(file_name):
    with open(file_name) as json_file:
        file_content = json.load(json_file)

    return file_content


def write_json_file(file_name, data, cls=None):
    with open(file_name, 'w') as log_file:
        json.dump(data, log_file, sort_keys=True, indent=2, separators=(',', ': '), cls=cls)
