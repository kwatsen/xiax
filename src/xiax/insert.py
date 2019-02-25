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
if "2.7" in sys.version:
  from StringIO import StringIO

from . import generate
from . import validate
from . import __version__
from .common import xiax_namespace
from .common import xiax_block_v1_header



# Force stable gzip timestamps
class FakeTime:
    def time(self):
        return 1225856967.109
gzip.time = FakeTime()




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
  # a) assert sane URIs (tests don't need to be repeated in step (3)
  # b) copy/patch any art/code files containing YYYY-MM-DD in filename  (both `src` and `gen`)
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
      xiax_tag = 'src'
    else:
      xiax_tag = 'gen'

    xxx_attrib_uri_orig = el.attrib[xiax_namespace + xiax_tag]

    # notes:
    #  - wanted to use "urlparse", but is fails when '@' character is present
    #  - "len(uri_split[0])>1" lets Windows drives (e.g.: "c:") pass
    xxx_attrib_uri_split = xxx_attrib_uri_orig.split(':', 1)
    if len(xxx_attrib_uri_split)==2 and xxx_attrib_uri_split[0]!='file':
      if len(xxx_attrib_uri_split[0]) == 1:
        print("Error: a Windows-based drive path detected for the artwork/sourcecode element on line "
               + str(el.sourceline) + " having 'xiax:" + xiax_tag + "' value \"" + xxx_attrib_uri_orig + "\".",
               file=sys.stderr)
        return 1

      if debug > 1:
        print("Debug: Skipping the artwork/sourcecode element on line " + str(el.sourceline)
               + " having 'xiax:" + xiax_tag + "' value \"" + xxx_attrib_uri_orig + "\" because it"
               + " specifies a URI scheme"
               + " other than \"file\".")
      continue

    # normalize the relative path (i.e., remove any "file:" prefix)
    if len(xxx_attrib_uri_split)==1:
      xxx_attrib_rel_path = xxx_attrib_uri_split[0]
    else:
      xxx_attrib_rel_path = xxx_attrib_uri_split[1]

    # ensure the path is a local path
    if os.path.normpath(xxx_attrib_rel_path).startswith(('..','/')):
      print("Error: a non-local filepath is used for the artwork/sourcecode element on line "
             + str(el.sourceline) + " having 'xiax:" + xiax_tag + "' value \"" + xxx_attrib_uri_orig
             + "\".", file=sys.stderr)
      return 1

    # at this point, xxx_attrib_rel_path is considered okay (sans possible YYYY-MM-DD replacement)

    # calc full path to inclusion (as the CWD may not be same as src_dir)
    xxx_attrib_full_path = os.path.join(src_dir, xxx_attrib_rel_path)

    # check if YYYY-MM-DD conversion needed
    if "YYYY-MM-DD" in os.path.basename(xxx_attrib_rel_path):
      if debug > 2:
        print("Spew: filename \"" + os.path.basename(xxx_attrib_full_path)
               + "\" has \"YYYY-MM-DD\" in it...")

      # ensure xxx_attrib file actually exists
      if not os.path.isfile(xxx_attrib_full_path):
        print("Error: file does not exist for the artwork/sourcecode element on line " + str(el.sourceline)
               + " having 'xiax:" + xiax_tag + "' value \"" + xxx_attrib_uri_orig + "\". (full path: "
               + xxx_attrib_full_path + ")", file=sys.stderr)
        return 1

      # calc new dst full path
      new_xxx_attrib_full_path = xxx_attrib_full_path.replace("YYYY-MM-DD", YYYY_MM_DD)
      
      # ensure dst file doesn't already exist
      if os.path.isfile(new_xxx_attrib_full_path) and force is False:
        print("Error: artwork/sourcecode \"" + new_xxx_attrib_full_path + "\" file already exists"
               + " (use \"force\" flag to override).", file=sys.stderr)
        return 1

      if debug > 2:
        print ("Spew: copying/patching " + xxx_attrib_full_path + " to " + new_xxx_attrib_full_path)

      # writeout new filename w/ substitutions
      with open(xxx_attrib_full_path) as infile, open(new_xxx_attrib_full_path, 'w') as outfile:
        for line in infile:
          line = line.replace("YYYY-MM-DD", YYYY_MM_DD)
          outfile.write(line)

      # minor layering violation, so "pack" logic below can be "YYYY-MM-DD" free
      el.attrib[xiax_namespace + xiax_tag] = xxx_attrib_uri_orig.replace("YYYY-MM-DD", YYYY_MM_DD)



  ### 1.5. now *generate* the derived views (generates a new file?)  [actual inclusion still in step 3]
  #
  # do this after all the `gen` files have been primed (have correct name)
  for el in src_doc.iter('artwork', 'sourcecode'):
    if xiax_namespace+'gen' not in el.attrib:
      continue

    if debug > 2:
      print("Spew: generating content for the artwork/sourcecode element on line " + str(el.sourceline)
             + " having 'xiax:gen' value \"" + el.attrib[xiax_namespace+'gen'] + "\".")

    gen_attrib_uri_orig = el.attrib[xiax_namespace + 'gen']
    gen_attrib_uri_split = gen_attrib_uri_orig.split(':', 1)
    if len(gen_attrib_uri_split)==1:
      gen_attrib_rel_path = gen_attrib_uri_split[0]
    else:
      gen_attrib_rel_path = gen_attrib_uri_split[1]
   
    dst_rel_path =  gen_attrib_rel_path + ".out"  # FIXME?  There's a round-tripping file-already-exists
                                                  # issue whereby the previous extract produces the .out
                                                  # file, so the next insert can't gen it again w/o force.
                                                  # Unsure if worth fixing, already the warning says to
                                                  # use 'force', which succeeds

    result = generate.generate_content(debug, force, src_dir, gen_attrib_rel_path, dst_rel_path)
    if result != 0:
      print("Error: failed trying to generate content for the artwork/sourcecode element on line "
             + str(el.sourceline) + " having 'xiax:gen' value \"" + el.attrib[xiax_namespace+'gen']
             + "\".", file=sys.stderr)
      return 1



  ### 2. validate inclusions, if 'xiax:val` attribute provided
  #
  # FIXME: validation support not implemented yet
  for el in src_doc.iter('artwork', 'sourcecode'):
    if xiax_namespace+'val' not in el.attrib:
      continue

    if debug > 2:
      print("Spew: validating content for the artwork/sourcecode element on line " + str(el.sourceline)
             + " having 'xiax:val' value \"" + el.attrib[xiax_namespace+'val'] + "\".")

    # get rel path to the "validate" input XML file
    val_attrib_uri_orig = el.attrib[xiax_namespace + 'val']
    val_attrib_uri_split = val_attrib_uri_orig.split(':', 1)
    if len(val_attrib_uri_split)==1:
      val_attrib_rel_path = val_attrib_uri_split[0]
    else:
      val_attrib_rel_path = val_attrib_uri_split[1]

    # get rel path to the file to be validated
    if xiax_namespace+'src' in el.attrib:
      xiax_tag = 'src'
    if xiax_namespace+'gen' in el.attrib:
      xiax_tag = 'gen'
    tag_attrib_uri_orig = el.attrib[xiax_namespace + xiax_tag]
    tag_attrib_uri_split = tag_attrib_uri_orig.split(':', 1)
    if len(tag_attrib_uri_split)==1:
      tag_attrib_rel_path = tag_attrib_uri_split[0]
    else:
      tag_attrib_rel_path = tag_attrib_uri_split[1]

    # validate it
    result = validate.validate_content(debug, force, src_dir, val_attrib_rel_path, tag_attrib_rel_path)
    if result == 1:
      print("Error: failed trying to validate \"" + tag_attrib_rel_path + "\" using the 'val' file \""
              + val_attrib_rel_path + "\".", file=sys.stderr)
      return 1




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
      xiax_tag = 'src'
    else:
      xiax_tag = 'gen'

    # ensure empty content
    if el.text != None:
      print("Error: content already exists for the artwork/sourcecode element on line " 
            + str(el.sourceline) + " having 'xiax:" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
           file=sys.stderr)
      return 1
   
    # ensure xml2rfc 'originalSrc' attribute not also set
    if 'originalSrc' in el.attrib:
      print("Error: the \"originalSrc\" attribute is set for xiax-controlled artwork/sourcecode element on line "
            + str(el.sourceline) + " having 'xiax:" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
           file=sys.stderr)
      return 1
 
    # ensure xml2rfc 'src' attribute not also set
    #  ^-- actually, this is okay for <artwork> (not <sourcecode>) and 
    #      the 'src' URL is a scheme other than "file:" (e.g., SVG)  FIXME
    if 'src' in el.attrib:
      print("Error: the \"src\" attribute is set for xiax-controlled artwork/sourcecode element on line "
            + str(el.sourceline) + " having 'xiax:" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
           file=sys.stderr)
      return 1

    # ensure 'markers' attribute not also set
    #  ^-- actually, this is okay for xml2rfc v3 docs, in which case xiax:markers should be ignored?  FIXME
    if 'markers' in el.attrib:
      print("Error: the \"markers\" attribute is set for xiax-controlled artwork/sourcecode element on line "
            + str(el.sourceline) + " having 'xiax:" + xiax_tag + "' value \"" + el.attrib[xiax_tag] + "\".",
            + "\" (use \"xiax:markers='true'\" instead).", file=sys.stderr)
      return 1


    xxx_attrib_uri_orig = el.attrib[xiax_namespace + xiax_tag] # already has YYYY-MM-DD substitution from "prime" step
    xxx_attrib_uri_split = xxx_attrib_uri_orig.split(':', 1)
    if len(xxx_attrib_uri_split)==2 and xxx_attrib_uri_split[0]!='file':
      # don't test for error condition again (it returned before)
      # don't print out another "skipping" debug message
      continue

    # normalize the relative path (i.e., remove any "file:" prefix)
    if len(xxx_attrib_uri_split)==1:
      xxx_attrib_rel_path = xxx_attrib_uri_split[0]
    else:
      xxx_attrib_rel_path = xxx_attrib_uri_split[1]

    # tack on 'gen' suffix, if needed
    if xiax_tag == "gen":
      xxx_attrib_rel_path += ".out"

    # don't again ensure the path is a local path
    # at this point, xxx_attrib_rel_path is considered okay (sans possible YYYY-MM-DD replacement)
    # calc full path to inclusion (as the CWD may not be same as src_dir)
    xxx_attrib_full_path = os.path.join(src_dir, xxx_attrib_rel_path)

    # ensure src file actually exists
    if not os.path.isfile(xxx_attrib_full_path):
      print("Error: file does not exist for the artwork/sourcecode element on line " + str(el.sourceline)
             + " having 'xiax:" + xiax_tag + "' value \"" + xxx_attrib_uri_orig + "\". (full path: "
             + xxx_attrib_full_path + ")", file=sys.stderr)
      return 1


    # remove the 'src/gen' attribute
    el.attrib.pop(xiax_namespace + xiax_tag)

    # embed file contents into this element's "text"
    try:
      if "2.7" in sys.version:
        xxx_attrib_fd = open(xxx_attrib_full_path, "rb")
      else:
        xxx_attrib_fd = open(xxx_attrib_full_path, "r")
    except Exception as e:
      e_type, e_val, e_tb = sys.exc_info()
      template = "Error: open('{}') failed on {}:{} [{!r}]"
      message = template.format(xxx_attrib_full_path, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
      print(message, file=sys.stderr)
      return 1
    data = xxx_attrib_fd.read()
    if xiax_namespace+'markers' in el.attrib and el.attrib[xiax_namespace+'markers'] == "true":
      data = '<CODE BEGINS> file "%s"\n\n%s\n<CODE ENDS>' % (os.path.basename(xxx_attrib_full_path), data)
      el.attrib.pop(xiax_namespace+'markers')
    if "2.7" in sys.version:
      p = data.decode(encoding='utf-8')
      el.text = etree.CDATA(p)
    else:
      el.text = etree.CDATA(data)
    xxx_attrib_fd.close()



    # add an "inclusion" entry to the xiax-block
    inclusion = etree.Element("inclusion")
    xiax_block.append(inclusion)
    path = etree.Element("path")
    path.text = src_doc.getelementpath(el)
    inclusion.append(path)
    if xiax_tag == "src":
      src = etree.Element("src")
      inclusion.append(src)
      attrib = etree.Element("attrib")
      attrib.text = xxx_attrib_uri_orig
      src.append(attrib)
      xxx = src

    if xiax_tag == "gen":
      gen = etree.Element("gen")
      inclusion.append(gen)
      attrib = etree.Element("attrib")
      attrib.text = xxx_attrib_uri_orig
      gen.append(attrib)
      file = etree.Element("file")
      xxx_attrib_full_path = xxx_attrib_full_path[:-4]  # sans the ".out"
      if "2.7" in sys.version:
        xxx_attrib_fd = open(xxx_attrib_full_path, "rb")
      else:
        xxx_attrib_fd = open(xxx_attrib_full_path, "r")
      data = xxx_attrib_fd.read()
      if "2.7" in sys.version:
        p = data.decode(encoding='utf-8')
        file.text = etree.CDATA(p)
      else:
        file.text = etree.CDATA(data)
      xxx_attrib_fd.close()
      gen.append(file)
      xxx = gen

    # for 'src' or 'gen', check if we need to add 'val'
    if xiax_namespace+'val' in el.attrib:
      val = etree.Element("val")
      xxx.append(val)
      attrib = etree.Element("attrib")
      attrib.text = el.attrib[xiax_namespace + 'val']
      val.append(attrib)
      file = etree.Element("file")
      val_attrib_full_path = os.path.join(src_dir, attrib.text)
      if "2.7" in sys.version:
        val_attrib_fd = open(val_attrib_full_path, "rb")
      else:
        val_attrib_fd = open(val_attrib_full_path, "r")
      data = val_attrib_fd.read()
      if "2.7" in sys.version:
        p = data.decode(encoding='utf-8')
        file.text = etree.CDATA(p)
      else:
        file.text = etree.CDATA(data)
      val_attrib_fd.close()
      val.append(file)

      # remove the 'val' attribute
      el.attrib.pop(xiax_namespace + 'val')


    # done processing art/code elements

  # remove the "xmlns:xiax" attribute (xmlns:xiax="https://watsen.net/xiax")
  etree.cleanup_namespaces(src_doc.getroot())

  # don't writeout the xiax-block if empty
  if len(xiax_block) == 0:
    print("Warn: no xiax processing instructions were found (no-op)")
  else:

    # create xiax-block data
    xiax_block = etree.tostring(xiax_block, pretty_print=True, encoding='unicode').encode(encoding='utf-8')
    #if debug > 2:
    #  print("Spew: saving xiax-block: " + str(xiax_block, 'utf-8'))

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
    comment = etree.Comment(xiax_block_v1_header + "\n%s\n" % xiax_block_gz_b64)
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


