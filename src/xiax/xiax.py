#!/usr/bin/env python3

import sys
import argparse
from . import __version__

"""xiax: eXtract or Insert Artwork (or sourcecode) from/to Xml"""

__acronym__ = "eXtract or Insert Artwork (or sourcecode) from/to Xml"

manual = """
Extract or insert artwork/sourcecode from/to an `xml2rfc` XML document.

Extraction
==========
  Occurs when the "src" parameter is an XML file and the "dst" parameter
  is either unspecified or specifies a directory (the current directory
  is used when the "dst" parameter is unspecified.

  In the source XML file, only <artwork> and <sourcecode> elements
  matching the following criteria are processed:
    - the "name" attribute is present, and specifies a path that is
      either the current or a descendent directory.
    - the "src" attribute is not present.
    - the content is not empty.

  The result of the extraction process is the creation of the specified
  files in the destination directory.  Any intermediate subdirectories
  will be created.  It is an error if any file already exists, in which
  case, no extraction occurs, unless the "force" flag is specified. The
  source XML file is not modified.

Insertion
=========
  Occurs when both the "src" and "dst" parameters are XML files.

  In the source XML file, only <artwork> and <sourcecode> elements
  matching the following criteria are processed:
    - the "src" attribute is present, and specifies a path that is
      either the current or a descendent directory.
    - the "name" attribute is not present.
    - there is no content (i.e., an empty element)

  The result of the insertion process is the creation of the specified
  destination XML file in which each <artwork> and <sourcecode> element
  processed will have the following characteristics:
    - the "name" element will contain the name of the input file,
      including any supplied filepath.
    - the "src" element will be removed.
    - the content of the element will be the content of the specified
      file, wrapped by character data (CDATA) tags.
  It is an error for the destination file to already exist, in which
  case, no insertions will occur, unless the "force" flag is specified.
  The source XML file is not modified.
"""


def process(verbose, source, destination):
  print("processing: verbose=%s, source=%s, and destination=%s" % (str(verbose), source, destination))
  return 0


def version():
  return __version__.__version__


def main(argv=None):

  parser = argparse.ArgumentParser(
            description="xiax: eXtract or Insert Artwork (or sourcecode) from/to Xml",
            epilog="""Exit status code: 0 on success, non-0 on error.  Error output goes to stderr.
            """, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument("-m", "--manual",
                      help="show manual and exit.",
                      action="store_true")
  parser.add_argument("-v", "--version",
                      help="show version number and exit.",
                      action="store_true")
  parser.add_argument("-V", "--verbose",
                      help="print verbose output to stdout.",
                      action="store_true")
  parser.add_argument("-s", "--source",
                      help="source XML document from which to extract from or to insert into.",
                      required=True)
  parser.add_argument("-d", "--destination",
                      help="destination XML document (insertion) or directory (extraction). "
                           "If unspecified, then the value \"./\" is used (i.e., extraction "
                           "is assumed).")

  args = parser.parse_args()

  if args.manual:
    print(manual)
    return 0

  if args.version:
    print(version())
    return 0

  return xiax.process(args.verbose, args.source, args.destination)


if __name__ == "__main__":
  sys.exit(main())

