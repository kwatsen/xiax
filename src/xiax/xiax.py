from __future__ import print_function

import os
import re
import sys
import git
import errno
import base64
import argparse
import pkg_resources
from lxml import etree
from datetime import date

from . import insert
from . import extract
from . import generate
from . import validate
from . import __version__
from .common import xiax_namespace
from .common import xiax_block_v1_header

"""xiax: eXtract or Insert artwork And sourcecode to/from Xml"""





def process(debug, force, src, dst):
  """
  Enrty point for processing.  Isolated from command-line arg parsing
  logic primarily for pytests.

  Args:
    debug: increases output level (0 is off, 1 is info, 2 is debug, 3 is spew)
    force: enables overwritting
    src:   filepath to src xml file.
    dst:   path to dst directory or file

  Returns:
    0 on success, 1 on error

  Raises:
    TBD
  """

  # add CWD to path if not passed
  if os.path.dirname(src) == "":
    src = os.path.join("./", src)
  if os.path.dirname(dst) == "":
    dst = os.path.join("./", dst)

  # sanity tests before parse(src)
  if not src.endswith(".xml"):
    print("Error: \"src\" file \"" + src + "\" does not end with \".xml\".", file=sys.stderr)
    return 1
  if not os.path.isfile(src):
    print("Error: \"src\" file \"" + src + "\" does not exist.", file=sys.stderr)
    return 1

  # parse(src)
  try:
    doc = etree.parse(src)
  except Exception as e:
    e_type, e_val, e_tb = sys.exc_info()
    template = "Error: etree.parse('{}') failed on {}:{} [{!r}]"
    message = template.format(src, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
    print(message, file=sys.stderr)
    return 1


  # examine root node to determine doc type (rfc, xiax:generate, or xiax:validate) and
  root = doc.getroot()
  if root.tag == 'rfc':

    # insert/extract? - see if any ##xiax-block exists
    do_insert=True
    for el in doc.getroot().iterchildren(etree.Comment):
    #for el in doc.xpath('/rfc/comment()'):
      if xiax_block_v1_header in el.text:
        do_insert=False
        if debug > 2:
          print("Spew: switching to 'extract' mode because there is a comment ending on line "
                 + str(el.sourceline) + " that contains the string \"%s\"." % xiax_block_v1_header)
   
    # release memory (in case it was a large XML file)
    doc = None
  
    if debug > 0:
      if do_insert == True:
        print("Info: using \"insertion\" mode")
      else:
        print("Info: using \"extraction\" mode")
  
    # centralizing this test
    if '\\' in src or '\\' in dst:
      print("Error: The backslash character is not supported in paths.")
      return 1
  
    if do_insert == True:
      return insert.insert(debug, force, src, dst)
    else:
      return extract.extract(debug, force, src, dst)



  elif root.tag == xiax_namespace+'generate':
    # release memory (in case it was a large XML file)
    doc = None

    gen_attrib_rel_path = os.path.dirname(src)
    if os.path.normpath(gen_attrib_rel_path).startswith(('..','/')):
      print("Error: a non-local filepath is used the 'source' parameter \"" + src
             + "\" [Note: the current working directory MUST be the document directory"
             + " when passing a 'gen' file as the 'source' parameter.", file=sys.stderr)
      return 1

    if dst != "./":  # "./" is the deault added by ArgumentParser
      print("Warning: the 'destination' parameter is ignored when passing a 'gen' file"
             + " as the 'source' parameter.", file=sys.stderr)

    result = generate.generate_content(debug, force, "./", src, "")  # empty string == stdout
    if result != 0:
      print("Error: failed trying to generate content for \"" + src + "\".", file=sys.stderr)

    return result



  elif root.tag == xiax_namespace+'validate':
    # release memory (in case it was a large XML file)
    doc = None

    val_attrib_rel_path = os.path.dirname(src)
    if os.path.normpath(val_attrib_rel_path).startswith(('..','/')):
      print("Error: a non-local filepath is used the 'source' parameter \"" + src
             + "\" [Note: the current working directory MUST be the document directory"
             + " when passing a 'val' file as the 'source' parameter.", file=sys.stderr)
      return 1

    if dst == "./":  # "./" is the deault added by ArgumentParser
      print("Error: the 'destination' parameter must specify the file to be validated,"
              + " when passing a 'val' file as the 'source' parameter.", file=sys.stderr)
      return 1

    result = validate.validate_content(debug, force, "./", src, dst)
    if result != 0:
      print("Error: failed trying to validate \"" + dst + "\" using the 'val' file \""
              + src + "\".", file=sys.stderr)

    return result


  print("Error: unreognized root element tag \"" + root.tag + "\" in source XML source.")
  return 1



def main(argv=None):

  parser = argparse.ArgumentParser(
            description="eXtract or Insert artwork And sourcecode to/from Xml",
            epilog="""Exit status code: 0 on success, non-0 on error.  Error output goes to stderr.
            """, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument("-v", "--version",
                      help="show version number and exit.)",
                      action="version", version=__version__.__version__)
  parser.add_argument("-d", "--debug",
                      help="increase debug output level up to 3x (e.g., -ddd)",
                      action="count", default=0)
  parser.add_argument("-f", "--force",
                      help="allow existing files to be overwritten.",
                      action="store_true", default=False)
  parser.add_argument("source",
                      help="source XML document to extract from or insert into.")
  parser.add_argument("destination",
                      help="destination file or directory.  If unspecified, then the current"
                            + " working directory is assumed.", nargs='?', default="./")
  args = parser.parse_args()
  return process(args.debug, args.force, args.source, args.destination)



if __name__ == "__main__":
  sys.exit(main())

