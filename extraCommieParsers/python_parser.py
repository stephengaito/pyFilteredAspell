# SPDX-FileCopyrightText: Copyright (c) 2021 Stephen Gaito <stephen@perceptisys.co.uk>
# SPDX-FileCopyrightText: Copyright (c) 2021 Art Galkin <ortemeo@gmail.com>
# SPDX-FileCopyrightText: Copyright (c) 2015 Jean-Ralph Aviles
# SPDX-License-Identifier: BSD-3-Clause

# This Python parser has been adapted from the original [Commie
# project's](https://github.com/rtmigo/commie) python_parser.py parser.
# The original was taken from the Commie project's commit: 7ae0950 from 21
# Mar 2021. It was copied on 2021/June/22.

# While the Commie project *does* have a Python specific comment parser,
# the Commie project's Python parser assumes that the Python it is parsing
# is correct Python or otherwise it throws an exception. IF this parser is
# being used to spell check the Python source code, this assumption is
# often incorrect. In this version of the python_parser.py we explicitly
# *ignore* the tokenizer's exception. We also identify multiline strings
# as comments.

import io
import tokenize
from typing import NamedTuple, Iterable

from commie.x01_common import Comment, Span

class PosToken(NamedTuple):
	tokenType: int
	text: str
	start: int
	end: int


def postokenize(infile: io.BytesIO) -> Iterable[PosToken]:
  # based on https://stackoverflow.com/a/62761208 (CC BY-SA 4.0)

  # Used to track starting position of each line.
  # Note that tokenize starts line numbers at 1 and column numbers at 0
  offsets = [0]

  def wrapped_readline():
    # Function used to wrap calls to infile.readline(); stores current
    # stream position at the beginning of each line.
    offsets.append(infile.tell())
    return infile.readline()

  # For each returned token, substitute type with exact_type and
  # add token boundaries as stream positions

  # To deal with the:
  #   tokenize.TokenError: ('EOF in multi-line statement', (86,0))
  # exception, we use the updated example in
  # https://stackoverflow.com/a/27613629

  tokenGenerator = tokenize.tokenize(wrapped_readline)
  while True :
    try:
      t = next(tokenGenerator)
      startline, startcol = t.start
      endline, endcol = t.end
      yield PosToken(t.exact_type, t.string,
        offsets[startline] + startcol,
        offsets[endline] + endcol)
    except tokenize.TokenError :
      continue
    except StopIteration :
      break

def extract_comments(code: str) -> Iterable[Comment]:
  """Extracts a list of comments from the given Python script.
  Comments are identified using the tokenize module. Now includes function,
  class, or module docstrings. Multiline strings are considered comments.
  Args:
    code: String containing code to extract comments from.
  Returns:
    Python list of common.Comment in the order that they appear in the code.
  Raises:
    none
  """

  for token in postokenize(io.BytesIO(code.encode())):

    if token.tokenType == tokenize.COMMENT:
      yield Comment(
        code,
        text_span=Span(token.start + 1, token.end),
        code_span=Span(token.start, token.end),
        multiline=False
      )
    elif (
      (token.tokenType == tokenize.STRING) and
       token.text.startswith('"""') ) :
      yield Comment(
        code,
        text_span=Span(token.start + 3, token.end - 3),
        code_span=Span(token.start, token.end),
        multiline=True
      )

if __name__ == "__main__":
	def experiment():
		from pathlib import Path
		extract_comments(Path(__file__).read_text())


	experiment()
