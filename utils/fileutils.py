import json


def read_json_file(file_name):
    try:
        with open(file_name) as json_file:
            file_content = json.load(json_file)
    except Exception as e:
        print(file_name)
        print(json_file)
        print(e)
        exit(0)

    return file_content


def write_json_file(file_name, data, cls=None):
    with open(file_name, 'w') as log_file:
        json.dump(data, log_file, sort_keys=True, indent=2, separators=(',', ': '), cls=cls)
