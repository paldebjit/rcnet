import os
import ruamel.yaml 
import sys


class config:
    home = ''

    paths = {}
    designs = {} 
    mutate = {}

    available = False

    @staticmethod
    def read_config():
        config.home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')) + '/'

        yaml = ruamel.yaml.YAML()

        with open(config.home + 'config/paths.yaml') as f:
            config.paths = yaml.load(f) 
    
        with open(config.home + 'config/design.yaml') as f:
            config.designs = yaml.load(f)
    
        with open(config.home + 'config/mutation.yaml') as f:
            config.mutate = yaml.load(f)
    
        config.available = True

    @staticmethod
    def update_config():
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=4, sequence=6, offset=4)

        with open(config.home + 'config/design.yaml', 'w') as f:
            yaml.dump(config.designs, f)
