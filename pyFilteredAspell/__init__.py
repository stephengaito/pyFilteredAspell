#!/usr/bin/env python3

# This python3 script wraps the Linux Aspell command line command with a
# configurable set of pre-filters.

# The pyFilteredAspell command manipulates the Aspell optional arguments:
# `--mode`, `-D`, '-e', '-H', '-t', '-n', '-M'. These optional arguments
# are used to set the pyFilteredAspell command's `filterName` variable.
# All other Aspell arguments are passed unchanged to Aspell.

# The pre-filters used by the pyFilteredAspell command are located in the
# user's `.config/pyFilteredAspellFilters` directory.

# The filters are chosen using configuration YAML which is loaded from
# the `.config/pyFilteredAspellFilters/config.yaml` file.

# This configuration YAML has three dictionaries, each a mapping from the
# filterName to some other (string) value:

# 1. `mapFilter` : (re)maps the filterName to a new filterName. This
# allows you to map an arbitrary filterName into a name either Aspell or
# pyFilteredAspell understands.

# 2. `mapFilterModule` : maps the filterName to a loadable Python module
# in the `.config/pyFilteredAspellFilters` directory. This allows a single
# Python module to handle multiple filterNames.

# 3. `useAspellFilter` : maps the filterName to a Boolean which if True
# will ensure Aspell's existing filter mode (with the name contained in
# the filterName variable) will be used directly.

# These mappings are applied in the order: `mapFilter`, `mapFilterModule`,
# `useAspellFilter`

import argparse
import importlib
import os
import subprocess
import sys
import time
import traceback
import yaml

def mergeConfigData(configData, newConfigData, thePath) :
  # This is a generic Python merge
  # It is a *deep* merge and handles both dictionaries and arrays
  #
  if type(configData) is None :
    print("ERROR configData should NEVER be None ")
    sys.exit(-1)

  if type(configData) != type(newConfigData) :
    print("Incompatible types {} and {} while trying to merge YAML data at {}".format(type(configData), type(newConfigData), thePath))
    print("Stoping merge at {}".format(thePath))
    return

  if type(configData) is dict :
    for key, value in newConfigData.items() :
      if key not in configData :
        configData[key] = value
      elif type(configData[key]) is dict :
        mergeConfigData(configData[key], value, thePath+'.'+key)
      elif type(configData[key]) is list :
        for aValue in value :
          configData[key].append(aValue)
      else :
        configData[key] = value
  elif type(configData) is list :
    for value in newConfigData :
      configData.append(value)
  else :
    print("ERROR configData MUST be either a dictionary or an array.")
    sys.exit(-1)

def mergeAspellArgs(aspellArgs, filterName) :

  if filterName not in aspellArgs :
    return aspellArgs['any']['args'].copy()

  result = []
  if 'basedOn' in aspellArgs[filterName] :
    result.extend(
      mergeAspellArgs(aspellArgs, aspellArgs[filterName]['basedOn'])
    )
  elif filterName != 'any' :
    result.extend(aspellArgs['any']['args'])

  if 'args' in aspellArgs[filterName] :
    result.extend(aspellArgs[filterName]['args'])

  return result

def cli() :
  parser = argparse.ArgumentParser(
    description="A simple Aspell wrapper which provides configurable filters.",
    epilog="We are only interested in the `--mode` argument, all other arguments will be passed directly onto Aspell"
  )
  parser.add_argument("--mode", help="Specify a filter mode", type=str)
  parser.add_argument("-D", help="Use Debctrl filter mode.", action="store_true")
  parser.add_argument("-e", help="Use email filter mode.", action="store_true")
  parser.add_argument("-H", help="Use html filter mode.", action="store_true")
  parser.add_argument("-t", help="Use tex filter mode.", action="store_true")
  parser.add_argument("-n", help="Use nroff filter mode.", action="store_true")
  parser.add_argument("-M", help="Use markdown filter mode.", action="store_true")
  args, aspellArgs = parser.parse_known_args()

  filterName = None
  if args.mode and filterName is None :
    filterName = args.mode
  if args.D and filterName is None :
    filterName = "debctrl"
  if args.e and filterName is None :
    filterName = "email"
  if args.H and filterName is None :
    filterName = "html"
  if args.t and filterName is None :
    filterName = "tex"
  if args.n and filterName is None :
    filterName = "nroff"
  if args.M and filterName is None :
    filterName = "markdown"

  userConfigDir = os.path.expanduser("~/.config")
  sys.path.append(userConfigDir)

  filtersModuleName = "pyFilteredAspellFilters"
  filtersDir = os.path.join(userConfigDir, filtersModuleName)

  yamlConfigFile = os.path.join(filtersDir, "config.yaml")
  config = {
    'mapFilterModule' : { },
    'useAspellFilter' : {
      'all': True
    },
    'mapFilter' : { },
    'filterConfig' : { },
    'debug' : { },
    'aspellArgs' : {
      'any' : {
        'args' : []
      }
    }
  }
  if os.path.exists(yamlConfigFile) :
    with open(yamlConfigFile) as yamlFile :
      yamlConfig = yaml.safe_load(yamlFile)
    if yamlConfig:
      mergeConfigData(config, yamlConfig, "")

  debugFile = None
  if 'file' in config['debug'] :
    debugFile = open(config['debug']['file'].format(str(time.time())), 'w')
    debugFile.write("config:\n")
    debugFile.write("---------------------------------------------------------\n")
    debugFile.write(yaml.dump(config))
    debugFile.write("---------------------------------------------------------\n")

  stdinStr = sys.stdin.read()

  try:

    if filterName is None :
      print("Error: You must specify a filter mode")
      sys.exit(-1)

    if debugFile:
      debugFile.write("filterName: [{}]\n".format(filterName))

    newAspellArgs = mergeAspellArgs(config['aspellArgs'], filterName)

    mapFilter = config['mapFilter']
    if filterName in mapFilter :
      filterName = mapFilter[filterName]
    if debugFile:
      debugFile.write("mapped filterName: [{}]\n".format(filterName))

    filterModule = filterName
    mapFilterModule = config['mapFilterModule']
    if filterName in mapFilterModule :
      filterModule = mapFilterModule[filterName]
    if debugFile:
      debugFile.write("filterModule [{}]\n".format(filterModule))

    if debugFile:
      debugFile.write("---------------------------------------------------------\n")
      debugFile.write("stdinStr: [{}]\n".format(stdinStr))
      debugFile.write("---------------------------------------------------------\n")

    aspellArgs.insert(0, "aspell")
    aspellArgs.append("--mode")
    if filterName and filterName not in config['useAspellFilter'] :
      if os.path.exists(
         os.path.join(userConfigDir, "pyFilteredAspellFilters", filterModule+".py")) :
        if debugFile:
          debugFile.write("Running filter\n")
        filter = importlib.import_module("pyFilteredAspellFilters."+filterModule)
        filterConfig = { }
        filterConfiguration = config['filterConfig']
        if filterModule in filterConfiguration :
          mergeConfigData(filterConfig, filterConfiguration[filterModule], "")
        if filterName in filterConfiguration :
          mergeConfigData(filterConfig, filterConfiguration[filterName], "")
        if debugFile:
          debugFile.write("filterConfig:\n{}\n".format(yaml.dump(filterConfig)))
        filteredStdinStr = filter.filterStr(stdinStr, filterName, filterConfig, debugFile)
        filterName = "none"
      else:
        if debugFile:
          debugFile.write("No filter found\n")
        filteredStdinStr = stdinStr
        filterName = "none"
    else:
      if filterName == 'all' :
        if debugFile:
          debugFile.write("Using aspell with all content filtered out\n")
        filteredStdinStr = ""
      else :
        if debugFile:
          debugFile.write("Using aspell filter\n")
        filteredStdinStr = stdinStr

    aspellArgs.append(filterName)
    aspellArgs.extend(newAspellArgs)

    if debugFile:
      debugFile.write("---------------------------------------------------------\n")
      debugFile.write("filteredStdinStr: [{}]\n".format(filteredStdinStr))
      debugFile.write("---------------------------------------------------------\n")
      for anArg in aspellArgs :
        debugFile.write("anArg: [{}]\n".format(anArg))

  except Exception as ex:
    aspellArgs.append('none')
    if debugFile:
      debugFile.write("could not run pyFilterAspell:\n")
      debugFile.write("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n")
      debugFile.write("{}\n".format(str(ex)))
      debugFile.write("{}\n".format(traceback.format_exc()))
      debugFile.write("\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n")
    filteredStdinStr = stdinStr

  try:
    subprocess.run(aspellArgs, input=bytes(filteredStdinStr, "utf-8"))
  except Exception as ex:
    if debugFile:
      debugFile.write("could not run aspell:\n")
      for anArg in aspellArgs :
        debugFile.write("anArg: [{}]\n".format(anArg))
      debugFile.write("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n")
      debugFile.write("{}\n".format(str(ex)))
      debugFile.write("{}\n".format(traceback.format_exc()))
      debugFile.write("\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n")
