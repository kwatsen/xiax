import os
import sys
import errno
import argparse
import pkg_resources
from lxml import etree;
from . import __version__

"""xiax: eXtract or Insert artwork And sourcecode to/from Xml"""


def extract(debug, force, src_path, dst_path):
  # test input

  src_dir = os.path.dirname(src_path)
  src_file = os.path.basename(src_path)

  if dst_path.endswith(".xml"):
    dst_dir = os.path.dirname(dst_path)
    dst_file = os.path.basename(dst_path)
    if os.path.normpath(src_path) == os.path.normpath(dst_path):
      print("Error: The destination XML file must not be the same as the source file.", file=sys.stderr)
      return 1
    if os.path.isfile(dst_path) and force is False:
      print("Error: The destination XML file already exists (use \"force\" flag to override).", file=sys.stderr)
      return 1
  else:
    dst_dir = dst_path
    dst_file = None

  # done testing input

  if not os.path.exists(dst_dir):
    print("trying to create dst dir \"" + dst_dir + "\"...")
    try:
      os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
    #except OSError as exc: # guard against race condition
    #  if exc.errno != errno.EEXIST:
    #    raise
    except Exception as e:
      template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1


  src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()

  for el in src_doc.iter('artwork', 'sourcecode'):
    if 'originalSrc' not in el.attrib:
      if debug > 1:
        print("Skipping the artwork/sourcecode element on line " + str(el.sourceline) + " because it"
              + "  doesn't have an 'originalSrc' attribute.")
      continue

    if el.text == None:
      print("Error: no content exists for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'originalSrc' value \"" + attrib_orig + "\".", file=sys.stderr)
      return 1

    if 'src' in el.attrib:
      if dst_file != None:
        print("Error: the \"src\" attribute is already set for the artwork/sourcecode element on line "
              + str(el.sourceline) + " having 'originalSrc' value \"" + attrib_orig + "\".", file=sys.stderr)
        return 1
      else:
        print("Warning: the \"src\" attribute is set for the artwork/sourcecode element on line "
              + str(el.sourceline) + " having 'originalSrc' value \"" + attrib_orig + "\".  This"
              + " is normally unsupported but, since writing out an \"extracted\" XML file is not"
              + " requested, it is just a warning.", file=sys.stderr)

    attrib_orig = el.attrib['originalSrc']

    attrib_split = attrib_orig.split(':', 1)
    if len(attrib_split)==2 and len(attrib_split[0])>1 and attrib_split[0]!='file':  # len(attrib_split[0])>1 lets Windows drives pass
      if debug > 1:
        print("Skipping the artwork/sourcecode element on line " + str(el.sourceline) + " having 'originalSrc' value \""
               + attrib_orig + "\" because it specifies a URI scheme other than \"file\".")
      continue

    # Note: splitdrive is only active on Windows-based platforms, e.g., splitdrive("c:foo")[0] == 'c'
    if (len(attrib_split)==1 and (os.path.normpath(attrib_split[0])).startswith(('..','/','\\'))) or \
       (len(attrib_split)==2 and (os.path.splitdrive(attrib_orig)[0]!='' or os.path.normpath(attrib_split[1]).startswith(('..','/','\\')))):
      print("Error: a non-local filepath is used for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'originalSrc' value \"" + attrib_orig + "\".", file=sys.stderr)
      return 1

    if len(attrib_split)==1:
      attrib_full = os.path.join(dst_dir, attrib_split[0])
    else:  # len(attrib_split)==2:
      attrib_full = os.path.join(dst_dir, attrib_split[1])


    if os.path.isfile(attrib_full) and force is False:
      print("Error: file already exists for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'originalSrc' value \"" + attrib_orig + "\"  (use \"force\" flag to override).",
            file=sys.stderr)
      return 1

    # okay, ready to do the extraction

    attrib_full_dir = os.path.dirname(attrib_full)
    #attrib_full_file = os.path.basename(attrib_ful)

    if not os.path.exists(attrib_full_dir):
      print("trying to create attrib dst path \"" + attrib_full_dir + "\"...")
      try:
        os.makedirs(attrib_full_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
        #except OSError as exc: # guard against race condition
        #  if exc.errno != errno.EEXIST:
        #    raise
      except Exception as e:
        template = "Error: an exception occurred while trying to makedir \"" + attrib_full_dir + "\" of type {0} occurred: {1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message, file=sys.stderr)
        return 1

    markers=False
    if el.text.startswith('<CODE BEGINS> file') and el.text.endswith('<CODE ENDS>'):
      markers=True
      el.text = '\n'.join(el.text.split('\n')[2:-2]) + '\n'

    # copy contents of element's "text" to specified file
    try:
      attrib_full_fd = open(attrib_full, 'w' if force else 'x')
    except Exception as e:
      template = "Error: an exception occurred while trying to open \"" + attrib_full + "\" for writing of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1
    attrib_full_fd.write(el.text)
    attrib_full_fd.close()
    if debug > 0:
      print("Saved artwork/sourcecode to file " + attrib_full)

    # reset the element
    tail = el.tail
    el.clear()
    el.set('src', attrib_orig)
    if markers:
      el.set('markers', 'true')
    el.tail = tail

    # end of long for loop

  # Now save the "unpacked" XML file, if requested
  if dst_file:
    try:
      dst_path_fd = open(dst_path, 'w' if force else 'x')
    except Exception as e:
      template = "Error: an exception occurred while trying to open \"" + dst_path + "\" for writing of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1
    dst_str=etree.tostring(src_doc, pretty_print=True, encoding='unicode')
    dst_path_fd.write(str(dst_str))
    dst_path_fd.close()
    if debug > 0:
      print("Saved \"unpacked\" XML to file " + dst_path)

  return 0



def insert(debug, force, src_path, dst_path):

  # test input

  src_dir = os.path.dirname(src_path)
  src_file = os.path.basename(src_path)

  if not dst_path.endswith(".xml"):
    dst_path = os.path.join(dst_path, src_file)
  
  if os.path.normpath(src_path) == os.path.normpath(dst_path):
    print("Error: The destination file must not be the same as the source file.")
    return 1

  # done testing input

  if os.path.isfile(dst_path) and force is False:
    print("Error: dst file already exists (use \"force\" flag to override).", file=sys.stderr)
    return 1

  src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()

  for el in src_doc.iter('artwork', 'sourcecode'):
    if 'src' not in el.attrib:
      if debug > 1:
        print("Skipping the artwork/sourcecode element on line " + str(el.sourceline) + " because it doesn't have a 'src' attribute.")
      continue

    attrib_orig = el.attrib['src']


    #url = urlparse(attrib_orig) # note: urlparse works on noscheme strings also, but not when they contain '@' character
    #if len(url.scheme) > 1 and url.scheme != 'file':  # url.schema>1 to support Windows, where "c:/foo" scheme is 'c'
    #
    # giving up on urlparse (old code above), too many issues...
    attrib_split = attrib_orig.split(':', 1)
    if len(attrib_split)==2 and len(attrib_split[0])>1 and attrib_split[0]!='file':  # len(attrib_split[0])>1 lets Windows drives pass
      if debug > 1:
        print("Skipping the artwork/sourcecode element on line " + str(el.sourceline) + " having 'src' value \""
               + attrib_orig + "\" because it specifies a URI scheme other than \"file\".")
      continue

    # at this point we switch from skipping to failing...

    # the below URI fragments don't really exist for "file" schemes and yet sometimes
    # files contain characters (e.g. '@', '?', and ':') that cause false positives
    # if url.netloc or url.params or url.query or url.fragment:
    #   print("Error: the URI contains unexpected parts (e.g., netloc, params, query, and/or fragment) for the"
    #          + "artwork/sourcecode element on line " + str(el.sourceline) + " having 'src' value \""
    #          + attrib_orig + "\".", file=sys.stderr)
    #   return 1


    # Note: splitdrive is only active on Windows-based platforms, e.g., splitdrive("c:foo")[0] == 'c'
    if (len(attrib_split)==1 and (os.path.normpath(attrib_split[0])).startswith(('..','/','\\'))) or \
       (len(attrib_split)==2 and (os.path.splitdrive(attrib_orig)[0]!='' or os.path.normpath(attrib_split[1]).startswith(('..','/','\\')))):
      print("Error: a non-local filepath is used for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'src' value \"" + attrib_orig + "\".", file=sys.stderr)
      return 1

    if len(attrib_split)==1:
      attrib_full = os.path.join(src_dir, attrib_split[0])
    else:  # len(attrib_split)==2:
      attrib_full = os.path.join(src_dir, attrib_split[1])

    if not os.path.isfile(attrib_full):
      print("Error: file does not exist for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'src' value \"" + attrib_orig + "\". (full path: attrib_full)", file=sys.stderr)
      return 1

    if 'originalSrc' in el.attrib:
      print("Error: the \"originalSrc\" attribute is already set for the artwork/sourcecode element on line "
            + str(el.sourceline) + " having 'src' value \"" + attrib_orig + "\".", file=sys.stderr)
      return 1

    if el.text != None:
      print("Error: content already exists for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'src' value \"" + attrib_orig + "\".", file=sys.stderr)
      return 1

    # okay, ready to make the change

    # swap attributes
    el.attrib.pop('src')
    el.set('originalSrc', attrib_orig)

    # copy file contents into this element's "text"
    try:
      attrib_fd = open(attrib_full, "r")
    except Exception as e:
      template = "Error: an exception occurred while trying to open \"" + attrib_full + "\" for reading of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1

    data = attrib_fd.read()
    if 'markers' in el.attrib and el.attrib['markers'] == "true":
      data = '<CODE BEGINS> file "%s"\n\n%s\n<CODE ENDS>' % (os.path.basename(attrib_full), data)
      el.attrib.pop('markers')
    el.text = etree.CDATA(data)
    attrib_fd.close()

    # end of long for loop

  dst_dir = os.path.dirname(dst_path)
  if not os.path.exists(dst_dir):
    print("trying to create dst dir \"" + dst_dir + "\"...")
    try:
      os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
      #except OSError as exc: # guard against race condition
      #  if exc.errno != errno.EEXIST:
      #    raise
    except Exception as e:
      template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1

  # now save the "packed" xml file
  try:
    dst_fd = open(dst_path, 'w' if force else 'x')
  except Exception as e:
    template = "Error: an exception occurred while trying to open \"" + dst_path + "\" for writing of type {0} occurred: {1!r}"
    message = template.format(type(e).__name__, e.args)
    print(message, file=sys.stderr)
    return 1

  dst_str=etree.tostring(src_doc, pretty_print=True, encoding='unicode')
  dst_fd.write(str(dst_str))
  dst_fd.close()

  if debug > 0:
    print("Saved \"packed\" XML to file " + dst_path)
  return 0



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

  if not os.path.isfile(src):
    print("Error: \"src\" file \"" + src + "\" does not exist.", file=sys.stderr)
    return 1

  try:
    doc = etree.parse(src)
  except Exception as e:
    template = "Error: XML parsing error.  An exception of type {0} occurred: {1!r}"
    message = template.format(type(e).__name__, e.args)
    print(message, file=sys.stderr)
    return 1

  do_insert=True
  for el in doc.iter('artwork', 'sourcecode'):
    if 'originalSrc' in el.attrib:
      do_insert=False
      if debug > 2:
        print("Spew: switching to 'extract' mode because artwork/sourcecode element on line "
               + str(el.sourceline) + " has an \"originalSrc\" attribite.")

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
    return insert(debug, force, src, dst)
  else:
    return extract(debug, force, src, dst)



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
                      help="source XML document from which to extract from or to insert into.")
  parser.add_argument("destination",
                      help="destination file or directory.  If unspecified, then the current"
                            + " working directory is assumed.", nargs='?', default="./")
  args = parser.parse_args()
  return process(args.debug, args.force, args.source, args.destination)



if __name__ == "__main__":
  sys.exit(main())

