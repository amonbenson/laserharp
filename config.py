import os
import yaml


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.yaml')
CONFIG = yaml.load(open(CONFIG_FILE, 'r'), Loader=yaml.FullLoader)


if __name__ == '__main__':
    import json

    print("Confguration:")
    print(json.dumps(CONFIG, indent=2))
