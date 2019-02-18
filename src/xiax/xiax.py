from __future__ import print_function

import os
import re
import sys
import git
import gzip
import errno
import base64
import argparse
import pkg_resources
from lxml import etree
from datetime import date
from . import __version__
if "2.7" in sys.version:
  from StringIO import StringIO

"""xiax: eXtract or Insert artwork And sourcecode to/from Xml"""


xiax_namespace = '{https://watsen.net/xiax}'
xiax_block_header = " ##xiax-block-v1:"


# Force stable gzip timestamps
class FakeTime:
    def time(self):
        return 1225856967.109
gzip.time = FakeTime()



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
    except Exception as e:
      e_type, e_val, e_tb = sys.exc_info()
      if not (e_type == OSError and e.errno == errno.EEXIST):  # for 2.7
        template = "Error: os.makedirs('{}') failed on {}:{} [{!r}]"
        message = template.format(dst_dir, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
        print(message, file=sys.stderr)
        return 1

  src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()


  # extract the xiax-block
  for el in src_doc.getroot().iterchildren(etree.Comment):
  #for el in doc.xpath('/rfc/comment()'):
    if xiax_block_header in el.text:
      text=el.text.replace(xiax_block_header + "\n", "")
      decoded_str = base64.decodestring(text.encode('utf-8'))
      if "2.7" in sys.version:
        in_file = StringIO()
        in_file.write(decoded_str)
        in_file.seek(0)
        gzip_file = gzip.GzipFile(fileobj=in_file, mode='r')
        data = gzip_file.read()
        data = data.decode('utf-8')
        gzip_file.close()
      else:
        data=gzip.decompress(decoded_str) 
      xiax_block = etree.fromstring(data)
      src_doc.getroot().remove(el) # in case dst XML file be saved
    

  for inclusion in xiax_block.findall("a:inclusion", {'a':"https://watsen.net/xiax"}):
    p = inclusion[0].text  # [0] is the 'path' child
    el = src_doc.find(p)
    if el.text == None:
      print("Error: no content exists for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'originalSrc' value \"" + attrib_orig + "\".", file=sys.stderr)
      return 1

    attrib_orig = inclusion[1].text   # [1] is the 'originalSrc' child
    attrib_split = attrib_orig.split(':', 1) # don't need to scrutinize, like before, since it came from xiax-block


    # normalize the relative path (i.e., remove any "file:" prefix)
    if len(attrib_split)==1:
      attrib_rel_path = attrib_split[0]
    else:
      attrib_rel_path = attrib_split[1]

    # calc full dst path for this inclusion
    attrib_full = os.path.join(dst_dir, attrib_rel_path)

    # ensure it doesn't exist yet, without force
    if os.path.isfile(attrib_full) and force is False:
      print("Error: file already exists for the artwork/sourcecode element on line " + str(el.sourceline)
            + " having 'originalSrc' value \"" + attrib_orig + "\"  (use \"force\" flag to override).",
            file=sys.stderr)
      return 1

    # okay, ready to do the extraction

    attrib_full_dir = os.path.dirname(attrib_full)
    if not os.path.exists(attrib_full_dir):
      try:
        #os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
        os.makedirs(attrib_full_dir)
      except Exception as e:
        e_type, e_val, e_tb = sys.exc_info()
        if not (e_type == OSError and e.errno == errno.EEXIST):  # for 2.7
          template = "Error: os.makedirs('{}') failed on {}:{} [{!r}]"
          message = template.format(attrib_full_dir, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
          print(message, file=sys.stderr)
          return 1

    markers=False
    if el.text.startswith('<CODE BEGINS> file') and el.text.endswith('<CODE ENDS>'):
      markers=True
      el.text = '\n'.join(el.text.split('\n')[2:-2]) + '\n'

    # copy contents of element's "text" to specified file

    # this following line doesn't work on 2.7:
    #   ^-- attrib_full_fd = open(attrib_full, 'w' if force else 'x')
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
    # this code doesn't work on 2.7:
    #   ^-- dst_path_fd = open(dst_path, 'w' if force else 'x')
    if os.path.isfile(dst_path) and force == False:
      print("Error, file \"" + dst_path + "\" already exists (use \"force\" flag to override).", file=sys.stderr)
      return 1
    if "2.7" in sys.version:
      dst_path_fd = open(dst_path, 'wb')
      dst_str=etree.tostring(src_doc, pretty_print=True, encoding='unicode')
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
  src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()
  if "pytest" in sys.modules:
    YYYY_MM_DD = "1234-56-78"
  else:
    YYYY_MM_DD = date.today().strftime("%Y-%m-%d")


  ### 1. prime inclusions, if needed
  #
  # a) assert sane URIs (test don't need to be repeated later)
  # b) copy/patch any art/code files containing YYYY-MM-DD in name
  # c) generate derived views (FIXME: not implemented yet)

  for el in src_doc.iter('artwork', 'sourcecode'):

    # check if any 'xiax:' attributes exist
    if xiax_namespace not in '\t'.join(el.attrib):
      if debug > 1:
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline) 
               + " because it doesn't have any 'xiax:' prefixed attributes.")
        print('\t'.join(el.attrib))
      continue

    #rewritten (below) for better user messages
    #if bool(xiax_namespace+'src' in el.attrib) != (xiax_namespace+'gen' in el.attrib):
    #  print("Error: the artwork/sourcecode element on line " + str(el.sourceline) 
    #         + " must specify 'xiax:src' or 'xiax:gen' (not both).")
    #  return 1

    if xiax_namespace+'src' not in el.attrib and xiax_namespace+'gen' not in el.attrib:
      print("Error: the artwork/sourcecode element on line " + str(el.sourceline) 
             + " must specify 'xiax:src' or 'xiax:gen'.", file=sys.stderr)
      return 1

    if xiax_namespace+'src' in el.attrib and xiax_namespace+'gen' in el.attrib:
      print("Error: the artwork/sourcecode element on line " + str(el.sourceline) 
             + " cannot specify both 'xiax:src' and 'xiax:gen'.", file=sys.stderr)
      return 1


    # normalize the tag name used
    if xiax_namespace+'src' in el.attrib:
      xiax_tag = 'xiax:src'
    else:
      xiax_tag = 'xiax:gen'


    src_attrib_uri_orig = el.attrib[xiax_namespace+'src']

    # notes:
    #  - wanted to use "urlparse", but is fails when '@' character is present
    #  - "len(uri_split[0])>1" lets Windows drives (e.g.: "c:") pass
    src_attrib_uri_split = src_attrib_uri_orig.split(':', 1)
    if len(src_attrib_uri_split)==2 and src_attrib_uri_split[0]!='file':
      if len(src_attrib_uri_split[0]) == 1:
        print("Error: a Windows-based drive path detected for the artwork/sourcecode element on line "
               + str(el.sourceline) + " having 'xiax:src' value \"" + src_attrib_uri_orig + "\".",
               file=sys.stderr)
        return 1

      if debug > 1:
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline)
               + " having 'xiax:src' value \"" + src_attrib_uri_orig + "\" because it specifies a URI scheme"
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
             + str(el.sourceline) + " having 'xiax:src' value \"" + src_attrib_uri_orig + "\".", file=sys.stderr)
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
               + " having 'xiax:src' value \"" + src_attrib_uri_orig + "\". (full path: src_attrib_full_path)",
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
      el.attrib[xiax_namespace+'src'] = src_attrib_uri_orig.replace("YYYY-MM-DD", YYYY_MM_DD)




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
  xiax_block = etree.Element("xiax-block", xmlns="https://watsen.net/xiax")
  for el in src_doc.iter('artwork', 'sourcecode'):

    # check if any xiax-namespaced attributes exist
    if xiax_namespace not in '\t'.join(el.attrib):
      # don't print out another "skipping" debug message
      continue

    # don't assert again xiax:src xor xiax:gen (would've errored-out above)

    # normalize the tag name used
    if xiax_namespace+'src' in el.attrib:
      xiax_tag = 'xiax:src'
    else:
      xiax_tag = 'xiax:gen'

    # ensure 'src' attribute not also set
    if 'src' in el.attrib:
      print("Error: the \"src\" attribute is set for xiax-controlled artwork/sourcecode element on line "
            + str(el.sourceline) + " having '" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
           file=sys.stderr)
      return 1

    # ensure 'originalSrc' attribute not also set
    if 'originalSrc' in el.attrib:
      print("Error: the \"originalSrc\" attribute is set for xiax-controlled artwork/sourcecode element on line "
            + str(el.sourceline) + " having '" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
           file=sys.stderr)
      return 1

    # ensure 'markers' attribute not also set
    if 'markers' in el.attrib:
      print("Error: the \"markers\" attribute is set for xiax-controlled artwork/sourcecode element on line "
            + str(el.sourceline) + " having '" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
            + "\" (use \"xiax:markers='true'\" instead).", file=sys.stderr)
      return 1

    # ensure empty content
    if el.text != None:
      print("Error: content already exists for the artwork/sourcecode element on line " 
            + str(el.sourceline) + " having '" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
           file=sys.stderr)
      return 1




    src_attrib_uri_orig = el.attrib[xiax_namespace+'src']     # already has YYYY-MM-DD substitution from "prime" step
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
             + " having 'xiax:src' value \"" + src_attrib_uri_orig + "\". (full path: src_attrib_full_path)", file=sys.stderr)
      return 1


    # add an "inclusion" entry to the xiax-block
    inclusion = etree.Element("inclusion")
    xiax_block.append(inclusion)
    path = etree.Element("path")
    path.text = src_doc.getelementpath(el)
    inclusion.append(path)
    originalSrc = etree.Element("originalSrc")
    originalSrc.text = src_attrib_uri_orig
    inclusion.append(originalSrc)

    # remove the 'src' attribute
    el.attrib.pop(xiax_namespace+'src')

    # embed file contents into this element's "text"
    try:
      if "2.7" in sys.version:
        src_attrib_fd = open(src_attrib_full_path, "rb")
      else:
        src_attrib_fd = open(src_attrib_full_path, "r")
    except Exception as e:
      e_type, e_val, e_tb = sys.exc_info()
      template = "Error: open('{}') failed on {}:{} [{!r}]"
      message = template.format(src_attrib_full_path, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
      print(message, file=sys.stderr)
      return 1

    data = src_attrib_fd.read()
    if xiax_namespace+'markers' in el.attrib and el.attrib[xiax_namespace+'markers'] == "true":
      data = '<CODE BEGINS> file "%s"\n\n%s\n<CODE ENDS>' % (os.path.basename(src_attrib_full_path), data)
      el.attrib.pop(xiax_namespace+'markers')
    if "2.7" in sys.version:
      p = data.decode(encoding='utf-8')
      el.text = etree.CDATA(p)
    else:
      el.text = etree.CDATA(data)
    src_attrib_fd.close()

    # done processing art/code elements

  # remove the "xmlns:xiax" attribute (xmlns:xiax="https://watsen.net/xiax")
  etree.cleanup_namespaces(src_doc.getroot())

  # don't writeout the xiax-block if empty
  if len(xiax_block) == 0:
    print("Warn: no xiax processing instructions were found (no-op)")
  else:

    # create xiax-block data
    xiax_block = etree.tostring(xiax_block, pretty_print=True, encoding='unicode').encode(encoding='utf-8')
    if "2.7" in sys.version:
      out_file = StringIO()
      gzip_file = gzip.GzipFile(fileobj=out_file, mode='w')
      gzip_file.write(xiax_block.encode('utf-8'))
      gzip_file.close()
      xiax_block_gz = out_file.getvalue()
      xiax_block_gz_b64 = str(base64.encodestring(xiax_block_gz))
    else:
      xiax_block_gz = gzip.compress(xiax_block)              # str(data, 'utf-8')
      xiax_block_gz_b64 = str(base64.encodestring(xiax_block_gz), 'utf-8')  # .encode('utf-8')) 
  
    # add the xiax-block to DOM
    comment = etree.Comment(xiax_block_header + "\n%s\n" % xiax_block_gz_b64)
    comment.tail = "\n\n"
    src_doc.getroot().append(comment)
    if not comment.getprevious().tail:
      comment.getprevious().tail = "\n\n"
    else:
      comment.getprevious().tail.join("\n")



  # ensure dst_dir exists
  if not os.path.exists(dst_dir):
    try:
      #os.makedirs(dst_dir, exist_ok=True)    # exist_ok doesn't exist < 3.4 !!!
      os.makedirs(dst_dir)
    except Exception as e:
      e_type, e_val, e_tb = sys.exc_info()
      if not (e_type == OSError and e.errno == errno.EEXIST): # for 2.7
        template = "Error: os.makedirs('{}') failed on {}:{} [{!r}]"
        message = template.format(dst_dir, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
        print(message, file=sys.stderr)
        return 1

  # now save the "packed" xml file
  
  # open dst file, ony if doesn't exist, unless forced
  # note: the following line doesn't work on 2.7...
  #       dst_fd = open(dst_path, 'w' if force else 'x')
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

  # insert/extract? - see if any ##xiax-block exists
  do_insert=True
  for el in doc.getroot().iterchildren(etree.Comment):
  #for el in doc.xpath('/rfc/comment()'):
    if xiax_block_header in el.text:
      do_insert=False
      if debug > 2:
        print("Spew: switching to 'extract' mode because there is a comment ending on line "
               + str(el.sourceline) + " that contains the string \"%s\"." % xiax_block_header)
 
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

