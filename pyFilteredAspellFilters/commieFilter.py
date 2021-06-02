# This Python3 module is a filter in the pyFilteredAspell package.

# The pyFilteredAspell command uses this module to extract comments 
# in order to spell check them using aspell. 

# This module uses the `commie` Python package to extract comments 
# from `sass`, `go`, `c`, `cpp`, `css`, `html`, `python`, `ruby`, and 
# `shell` code.

import importlib
import inspect
import re
import sys

commieMapping = {
  'sass'   : { 'parser': '.c_parser_regex',     'method' : 'extract_comments' },
  'go'     : { 'parser': '.c_parser_state',     'method' : 'iter_comments_go' },
  'c'      : { 'parser': '.c_parser_state',     'method' : 'iter_comments_c'  },
  'cpp'    : { 'parser': '.c_parser_state',     'method' : 'iter_comments_c'  },
  'css'    : { 'parser': '.css_parser_regex',   'method' : 'extract_comments' },
  'html'   : { 'parser': '.html_parser_regex',  'method' : 'extract_comments' },
  'python' : { 'parser': '.python_parser',      'method' : 'extract_comments' },
  'ruby'   : { 'parser': '.ruby_parser_regex',  'method' : 'extract_comments' },
  'shell'  : { 'parser': '.shell_parser_state', 'method' : 'extract_comments' },
}

def filterStdin(stdinStr, filterName, debugFile) :

  if filterName not in commieMapping : 
    return stdinStr
    
  commie = importlib.import_module(
    commieMapping[filterName]['parser'],
    package="commie.parsers"
  )
    
  iter_comments = getattr(commie, commieMapping[filterName]['method'])

  terseMode = False
  if stdinStr[0] == '!' :
    # We are in terse mode... so we need to remove the aspell terse mode 
    # markers
    terseMode = True
    stdinLines = stdinStr.splitlines()
    stdinLines.pop(0)
    fixedLines = []
    for aLine in stdinLines :
      fixedLines.append(aLine[1:len(aLine)])
    stdinStr = "\n".join(fixedLines)
  
    if debugFile :
      debugFile.write("======================================================\n")
      debugFile.write(stdinStr)
      debugFile.write("======================================================\n")

  strSpans = []

  codeEnd = 0

  # a python regular expression which identifies all NON whitespace characters
  nonWhiteSpace = re.compile(r'\S')

  for comment in iter_comments(stdinStr):
    codeStart = comment.text_span.start

    # This span is OUTSIDE a comment.... so translate it to whitespace...
    strSpans.append(nonWhiteSpace.sub(" ", stdinStr[codeEnd:codeStart]))

    codeEnd   = comment.text_span.end

    # This span is INSIDE a comment... so keep it as is...
    strSpans.append(stdinStr[codeStart:codeEnd])

  # This span is OUTSIDE a comment.... so translate it to whitespace...
  strSpans.append(nonWhiteSpace.sub(" ", stdinStr[codeEnd:len(stdinStr)]))

  if terseMode :
    # Now we need to replace the terse mode markers
    filteredLines = "".join(strSpans).splitlines()
    fixedLines = []
    for aLine in filteredLines :
      fixedLines.append('^'+aLine)
    fixedLines.insert(0, "!")
    filteredStdinStr = "\n".join(fixedLines)

    if debugFile :
      debugFile.write("======================================================\n")
      debugFile.write(filteredStdinStr)
      debugFile.write("======================================================\n")

  return filteredStdinStr
