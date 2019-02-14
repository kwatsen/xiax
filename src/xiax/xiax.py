from __future__ import print_function

import os
import re
import sys
import git
import errno
import argparse
import pkg_resources
from lxml import etree
from datetime import date
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
      print("Error: The destination XML file must not be the same as the source file.",
             file=sys.stderr)
      return 1
    if os.path.isfile(dst_path) and force is False:
      print("Error: The destination XML file already exists (use \"force\" flag to override).",
             file=sys.stderr)
      return 1
  else:
    dst_dir = dst_path
    dst_file = None

  # done testing input

  if not os.path.exists(dst_dir):
    try:
      #os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
      os.makedirs(dst_dir)
    except OSError as e:
      if e.errno != errno.EEXIST:  # for python < 3.4
        template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message, file=sys.stderr)
        return 1
    except Exception as e:
      template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1


  src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()

  for el in src_doc.iter('artwork', 'sourcecode'):
    if 'originalSrc' not in el.attrib:
      if debug > 1:
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline) + " because it"
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
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline) + " having 'originalSrc' value \""
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
      try:
        #os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
        os.makedirs(attrib_full_dir)
      except OSError as e:
        if e.errno != errno.EEXIST:  # for python < 3.4
          template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
          message = template.format(type(e).__name__, e.args)
          print(message, file=sys.stderr)
          return 1
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

    # this code doesn't work on 2.7...
    #try:
    #  attrib_full_fd = open(attrib_full, 'w' if force else 'x')
    #except Exception as e:
    #  template = "Error: an exception occurred while trying to open \"" + attrib_full + "\" for writing of type {0} occurred: {1!r}"
    #  message = template.format(type(e).__name__, e.args)
    #  print(message, file=sys.stderr)
    #  return 1
    if os.path.isfile(attrib_full) and force == False:
      print("Error, file \"" + attrib_full + "\" already exists (use \"force\" flag to override).", file=sys.stderr)
      return 1
    if "2.7" in sys.version:
      attrib_full_fd = open(attrib_full, 'wb')
      attrib_full_fd.write(el.text.encode('utf-8'))
    else:
      attrib_full_fd = open(attrib_full, 'w')
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

  # Now save the "unpacked" XML file, only if requested

  if dst_file:
    # this code doesn't work on 2.7...
    #try:
    #  dst_path_fd = open(dst_path, 'w' if force else 'x')
    #except Exception as e:
    #  template = "Error: an exception occurred while trying to open \"" + dst_path + "\" for writing of type {0} occurred: {1!r}"
    #  message = template.format(type(e).__name__, e.args)
    #  print(message, file=sys.stderr)
    #  return 1
    if os.path.isfile(dst_path) and force == False:
      print("Error, file \"" + dst_path + "\" already exists (use \"force\" flag to override).", file=sys.stderr)
      return 1
    if "2.7" in sys.version:
      dst_path_fd = open(dst_path, 'wb')
      dst_str=etree.tostring(src_doc, pretty_print=True, encoding='unicode')
      #p = unicode(dst_str, 'utf-8')
      #p = u''.join(dst_str.encoding('utf-8'))
      p = dst_str.encode(encoding='utf-8')
      dst_path_fd.write(p)
    else:
      dst_path_fd = open(dst_path, 'w')
      dst_str=etree.tostring(src_doc, pretty_print=True, encoding='unicode')
      dst_path_fd.write(str(dst_str))
    dst_path_fd.close()
    if debug > 0:
      print("Saved \"unpacked\" XML to file " + dst_path)

  return 0



def insert(debug, force, src_path, dst_path):
  ### Overview
  # 1. prime inclusions, if needed (inc. gen derived views)
  # 2. validate inclusions, if possible
  # 3. pack and save (inc. "rev" + YYYY-MM-DD replacements)


  # globals
  src_dir = os.path.dirname(src_path)
  src_file = os.path.basename(src_path)
  dst_dir = os.path.dirname(dst_path) if dst_path.endswith(".xml") else dst_path
  YYYY_MM_DD = date.today().strftime("%Y-%m-%d")
  src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()


  ### 1. prime inclusions, if needed
  #
  # a) assert sane URIs (test don't need to be repeated later)
  # b) copy/patch any art/code files containing YYYY-MM-DD in name
  # c) generate derived views (FIXME: not implemented yet)

  for el in src_doc.iter('artwork', 'sourcecode'):
    if 'src' not in el.attrib:
      if debug > 1:
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline) 
               + " because it doesn't have a 'src' attribute.")
      continue

    src_attrib_uri_orig = el.attrib['src']

    # notes:
    #  - wanted to use "urlparse", but is fails when '@' character is present
    #  - "len(uri_split[0])>1" lets Windows drives (e.g.: "c:") pass
    src_attrib_uri_split = src_attrib_uri_orig.split(':', 1)
    if len(src_attrib_uri_split)==2 and src_attrib_uri_split[0]!='file':
      if len(src_attrib_uri_split[0]) == 1:
        print("Error: a Windows-based drive path detected for the artwork/sourcecode element on line "
               + str(el.sourceline) + " having 'src' value \"" + src_attrib_uri_orig + "\".",
               file=sys.stderr)
        return 1

      if debug > 1:
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline)
               + " having 'src' value \"" + src_attrib_uri_orig + "\" because it specifies a URI scheme"
               + " other than \"file\".")
      continue

    # normalize the relative path (i.e., remove any "file:" prefix)
    if len(src_attrib_uri_split)==1:
      src_attrib_rel_path = src_attrib_uri_split[0]
    else:
      src_attrib_rel_path = src_attrib_uri_split[1]

    # ensure the path is a local path
    if os.path.normpath(src_attrib_rel_path).startswith(('..','/')):
      print("Error: a non-local filepath is used for the artwork/sourcecode element on line "
             + str(el.sourceline) + " having 'src' value \"" + src_attrib_uri_orig + "\".", file=sys.stderr)
      return 1

    # at this point, src_attrib_rel_path is considered okay (sans possible YYYY-MM-DD replacement)

    # calc full path to inclusion (as the CWD may not be same as src_dir)
    src_attrib_full_path = os.path.join(src_dir, src_attrib_rel_path)

    # check if YYYY-MM-DD conversion needed
    if "YYYY-MM-DD" in os.path.basename(src_attrib_rel_path):
      if debug > 2:
        print("Spew: filename \"" + os.path.basename(src_attrib_full_path)
               + "\" has \"YYYY-MM-DD\" in it...")

      # ensure src file actually exists
      if not os.path.isfile(src_attrib_full_path):
        print("Error: file does not exist for the artwork/sourcecode element on line " + str(el.sourceline)
               + " having 'src' value \"" + src_attrib_uri_orig + "\". (full path: src_attrib_full_path)",
               file=sys.stderr)
        return 1

      # calc new dst full path
      new_src_attrib_full_path = src_attrib_full_path.replace("YYYY-MM-DD", YYYY_MM_DD)
      
      # ensure dst file doesn't already exist
      if os.path.isfile(new_src_attrib_full_path) and force is False:
        print("Error: artwork/sourcecode \"" + new_src_attrib_full_path + "\" file already exists"
               + " (use \"force\" flag to override).", file=sys.stderr)
        return 1

      if debug > 2:
        print ("Spew: copying/patching " + src_attrib_full_path + " to " + new_src_attrib_full_path)

      # writeout new filename w/ substitutions
      with open(src_attrib_full_path) as infile, open(new_src_attrib_full_path, 'w') as outfile:
        for line in infile:
          line = line.replace("YYYY-MM-DD", YYYY_MM_DD)
          outfile.write(line)

      # minor layering violation, so "pack" logic below can be "YYYY-MM-DD" free
      el.attrib['src'] = src_attrib_uri_orig.replace("YYYY-MM-DD", YYYY_MM_DD)




  ### 2. validate inclusions, if possible
  #
  # FIXME: validation support not implemented yet




  ### 3. pack and save (inc. "rev" + YYYY-MM-DD replacements)
  #
  # a) determine doc version
  # b) fix docName attribute in <rfc> element
  # c) src --> originalSrc in <artwork> and <sourcecode> elements
  # d) convert any remaining YYYY-MM-DD strings 

  # determine doc revision number and filename
  if dst_path.endswith(".xml"):
    # easy, just extract it from the provided path
    dst_file = os.path.basename(dst_path)
    if not re.match(".*-[0-9]{2}\.xml", dst_file):
      print("Error: provided destination \"" + dst_file + "\" doesn't match regex pattern: .*-[0-9]{2}\.xml")
      return 1
    rev_str = dst_file[-6:-4]
  else:
    # see if we can grab it from git
    try:
      repo = git.Repo(src_dir)
      tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
      latest_tag = tags[-1]
      last_rev = str(latest_tag)[-2:]
      rev_str = "%02i" % (int(last_rev) + 1)
      if debug > 2:
        print("Spew: git repo found, next rev number should be \"" + rev_str + "\"...")
    except git.InvalidGitRepositoryError:
      # guess not...
      rev_str = "00"
      if debug > 2:
        print("Spew: git repo NOT found, using \"-00\"...")

    if "-latest" in src_file:
      dst_file = src_file.replace("-latest", "-" + rev_str)
    else:
      dst_file = src_file.replace(".xml", "-" + rev_str + ".xml")

    # update dst_path so it's a fullpath
    dst_path = os.path.join(dst_dir, dst_file)
    if debug > 1:
      print("Debug: Calculated destination file: " + dst_path)
 
  # assert dst != src 
  if os.path.normpath(src_path) == os.path.normpath(dst_path):
    print("Error: The destination file must not be the same as the source file.")
    return 1

  # patch the docName attribute
  for el in src_doc.iter('rfc'):
    if 'docName' not in el.attrib:
      print("Error: source XML's \"rfc\" element doesn't have a \"docName\" attribute.", file=sys.stderr)
      return 1
    docName_orig = el.attrib['docName']
    docName_new = docName_orig.replace("-latest", "-" + rev_str)
    el.attrib['docName'] = docName_new

  # pack the inclusions
  # note: much of this is a condensed form of the above code (no repeats)
  for el in src_doc.iter('artwork', 'sourcecode'):
    if 'src' not in el.attrib:
      # don't print out another "skipping" debug message
      continue

    src_attrib_uri_orig = el.attrib['src']     # already has YYYY-MM-DD substitution from "prime" step
    src_attrib_uri_split = src_attrib_uri_orig.split(':', 1)
    if len(src_attrib_uri_split)==2 and src_attrib_uri_split[0]!='file':
      # don't test for error condition again (it returned before)
      # don't print out another "skipping" debug message
      continue

    # normalize the relative path (i.e., remove any "file:" prefix)
    if len(src_attrib_uri_split)==1:
      src_attrib_rel_path = src_attrib_uri_split[0]
    else:
      src_attrib_rel_path = src_attrib_uri_split[1]

    # don't again ensure the path is a local path
    # at this point, src_attrib_rel_path is considered okay (sans possible YYYY-MM-DD replacement)
    # calc full path to inclusion (as the CWD may not be same as src_dir)
    src_attrib_full_path = os.path.join(src_dir, src_attrib_rel_path)

    # ensure src file actually exists
    if not os.path.isfile(src_attrib_full_path):
      print("Error: file does not exist for the artwork/sourcecode element on line " + str(el.sourceline)
             + " having 'src' value \"" + src_attrib_uri_orig + "\". (full path: src_attrib_full_path)", file=sys.stderr)
      return 1

    # ensure originalSrc not set
    if 'originalSrc' in el.attrib:
      print("Error: the \"originalSrc\" attribute is already set for the artwork/sourcecode element on line "
            + str(el.sourceline) + " having 'src' value \"" + src_attrib_uri_orig + "\".", file=sys.stderr)
      return 1

    # ensure empty content
    if el.text != None:
      print("Error: content already exists for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'src' value \"" + src_attrib_uri_orig + "\".", file=sys.stderr)
      return 1

    # okay, ready to make the change

    # swap attributes
    el.attrib.pop('src')
    el.set('originalSrc', src_attrib_uri_orig)

    # copy file contents into this element's "text"
    try:
      if "2.7" in sys.version:
        src_attrib_fd = open(src_attrib_full_path, "rb")
      else:
        src_attrib_fd = open(src_attrib_full_path, "r")
    except Exception as e:
      template = "Error: an exception occurred while trying to open \"" + src_attrib_full + "\" for reading of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1

    data = src_attrib_fd.read()
    if 'markers' in el.attrib and el.attrib['markers'] == "true":
      data = '<CODE BEGINS> file "%s"\n\n%s\n<CODE ENDS>' % (os.path.basename(src_attrib_full_path), data)
      el.attrib.pop('markers')
    if "2.7" in sys.version:
      p = data.decode(encoding='utf-8')
      el.text = etree.CDATA(p)
    else:
      el.text = etree.CDATA(data)
    src_attrib_fd.close()

    # done processing art/code elements

  # ensure dst_dir exists
  if not os.path.exists(dst_dir):
    try:
      #os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
      os.makedirs(dst_dir)
    except OSError as e:
      if e.errno != errno.EEXIST:  # for python < 3.4
        template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message, file=sys.stderr)
        return 1
    except Exception as e:
      template = "Error: an exception occurred while trying to makedir \"" + dst_dir + "\" of type {0} occurred: {1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message, file=sys.stderr)
      return 1

  # now save the "packed" xml file
  
  # open dst file, ony if doesn't exist, unless forced
  #
  # this code doesn't work on 2.7...
  #  try:
  #    dst_fd = open(dst_path, 'w' if force else 'x')
  #
  if os.path.isfile(dst_path) and force is False:
    print("Error, file \"" + dst_path + "\" already exists (use \"force\" flag to override).", file=sys.stderr)
    return 1
  if "2.7" in sys.version:
    dst_fd = open(dst_path, 'wb')
  else:
    dst_fd = open(dst_path, 'w')

  # write (w/ final YYYY-MM-DD replacements) and save
  dst_str=etree.tostring(src_doc, pretty_print=True, encoding='unicode')
  dst_str=dst_str.replace("YYYY-MM-DD", YYYY_MM_DD)
  if "2.7" in sys.version:
    dst_fd.write(dst_str.encode('utf-8'))
  else:
    dst_fd.write(dst_str)
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
               + str(el.sourceline) + " has an \"originalSrc\" attribute.")

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
                      help="source XML document to extract from or insert into.")
  parser.add_argument("destination",
                      help="destination file or directory.  If unspecified, then the current"
                            + " working directory is assumed.", nargs='?', default="./")
  args = parser.parse_args()
  return process(args.debug, args.force, args.source, args.destination)



if __name__ == "__main__":
  sys.exit(main())

