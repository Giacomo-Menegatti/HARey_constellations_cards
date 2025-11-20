class FlagConfig:
    def __init__(self, **flags):
        # initial parameters
        self.flags = flags

    # Convert list of "flag" / "-flag" strings into {key: bool}
    def _flags_to_params(self, flags):
        params = {}
        for f in flags:
            if not isinstance(f, str):
                raise ValueError(f"Flags must be strings, got {type(f)}")

            enable = not f.startswith("-")
            key = f.lstrip("-")

            if key not in self.flags:
                raise KeyError(f"Unknown flag: '{key}'. Allowed: {list(self.flags)}")

            params[key] = enable
        return params

    # Set defaults parameters
    def set(self, *flags):
        self.flags.update(self._flags_to_params(flags))

    # Merge defaults + global overrides + call overrides
    def resolve(self, *call_flags):
        params = self.flags.copy()
        params.update(self._flags_to_params(call_flags))
        return params

    def __str__(self):
        str = 'Boolean flags used :\n\n'

        for k,v in self.flags.items():
            str = str + f'{k} : {v}\n'
        return str
    

class ColorConfig:
    def __init__(self, **colors):
        # initial parameters
        self.colors = colors

    # Set defaults parameters
    def set(self, colors):

        for key, value in colors.items():
            if key not in self.colors:
                raise ValueError(f"unknown color: '{key}'. Allowed colors are {list(self.colors.keys())}")
            self.colors.update(colors)

    def __str__(self):
        str = 'Colors used :\n\n'

        for k,v in self.colors.items():
            str = str + f'{k} : {v}\n'
        return str