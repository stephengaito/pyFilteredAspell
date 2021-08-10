# pyFilteredAspell

A simple python command line wrapper to provide configurable pre-filters
to the [aspell command line tool](http://aspell.net/).

This python3 script wraps the Linux aspell command line command with a
configurable set of pre-filters.

The pyFilteredAspell command manipulates the aspell optional arguments:
`--mode`, `-D`, '-e', '-H', '-t', '-n', '-M'. These optional arguments are
used to set the pyFilteredAspell command's `filterName` variable. All
other aspell arguments are passed unchanged to aspell.

The pre-filters used by the pyFilteredAspell command are located in the
user's `.config/pyFilteredAspellFilters` directory.

The filters are chosen using configuration YAML which is loaded from
the `.config/pyFilteredAspellFilters/config.yaml` file.

This configuration YAML has five dictionaries. The first three
dictionaries are each a mapping from the filterName to some other (string)
value:

1. `mapFilter` : (re)maps the filterName to a new filterName. This allows
you to map an arbitrary filterName into a name either aspell or
pyFilteredAspell understands.

2. `mapFilterModule` : maps the filterName to a loadable Python module in
the `.config/pyFilteredAspellFilters` directory. This allows a single
Python module to handle multiple filterNames.

3. `useAspellFilter` : maps the filterName to a Boolean which if True will
ensure aspell's existing filter mode (with the name contained in the
filterName variable) will be used directly.

These mappings are applied in the order: `mapFilter`, `mapFilterModule`,
`useAspellFilter`

The final two dictionaries are:

4. `filterConfig` : Is a collection of dictionaries corresponding to
filterModules and/or filterNames. The contents of these (sub)dictionaries
will be merged and passed to the loaded filter function.

5. `debug` : contains the single key `file` which is a path to the file in
which to write debug output.

## Installation

Get and unpack a copy of this repository.

To install the command and associated filters type:

```
  cd pyFilteredAspell
  ./scripts/installConfigurationDirectories
  ./scripts/installEditablePyFilteredAspellCommand
```

If you wish to use the `commieFilter.py` filter provided, you will also
need to install the `commie` Python3 package:

```
  pip install commie
```

## Adding new filters

You can add your own aspell pre-filters by adding Python3 modules to the
`~/config/pyFilteredAspellFilters` directory. Any module you add *must*
define a `filterStr` function which takes four arguments:

1. the text string to be filtered

2. the name of the filter to apply (This is the final result of the
   `mapFilter` mapping defined above).

3. any configuration associated with either the filterModule or the
filterName obtained from the `filterConfig` section of the
pyFilteredAspell config.yaml file

4. a debugFile which if not None is a IO file handle associated with the
   debug file.

Your `filterStr` function *must* extract and return the contents of the
text string which you want spell checked. If you are using
pyFilteredAspell as part of the external spell checker for an editor, it
is *useful* to change all non-whitespace that you do not want to spell
check into spaces. (See the `commieFilter.py` for an example of how to do
this).
