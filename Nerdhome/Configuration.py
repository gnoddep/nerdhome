import json


class Configuration():
    def __init__(self, filename=None, configuration={}):
        self.__configuration = configuration

        if filename is not None:
            with open(filename, 'r') as fd:
                self.__configuration = json.load(fd)

    def get(self, *args, **kwargs):
        try:
            value = self.__configuration
            for key in args:
                value = value[key]

            return value
        except KeyError:
            if not 'default' in kwargs:
                raise

            return kwargs['default']
