from __future__ import print_function

import os
import sys
import subprocess
from lxml import etree
from datetime import date


#import pyang

xiax_namespace = '{https://watsen.net/xiax}'



def validate_yang_module(debug, force, src_dir, src_rel_path, tgt_rel_path):
  """
  src_dir: the document's top-level directory
  src_rel_path: the rel_path (to src_dir) to the 'val' file (i.e., what comes from the xiax:val attribute)
  tgt_rel_path: the rel_path (to src_dir) to the file to be validated
  NOTE: for both invocation cases, any validation errors go STDERR
  """


  if debug > 2:
    print("Spew: Inside validate_yang_module()...")

  src_doc = etree.parse(src_rel_path) # this won't fail because it suceeded a moment ago in process()

  # get the 'yang-module' element
  yang_module = src_doc.getroot()[0]
  assert yang_module.tag == xiax_namespace+'yang-module'

  for el in yang_module.findall(xiax_namespace+'additional-yang-modules'):
      print("NOT IMPLEMENTED YET: additional-yang-modules")
      return 1




  # at this point, ...

  # calc full path to target file (YANG module), as the CWD may not be same as src_dir
  tgt_full_path = os.path.join(src_dir, tgt_rel_path)

  # ensure file exists
  if not os.path.isfile(tgt_full_path):
    extra=""
    if "YYYY-MM-DD" in tgt_full_path:
        extra=(" Note: running `xiax` directly against a 'val' file will not" +
                 + " automatically generate YYYY-MM-DD dependencies.")
    print("Error: the YANG module to generate the tree diagram for (" + tgt_full_path
           + ") doesn't exist." + extra , file=sys.stderr)
    return 1

  # validate it
  cmd = "yanglint %s" % tgt_full_path
  p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  p.wait()
  if p.returncode != 0:
    err = p.stderr.read()
    if not err or err is None:
      print("Error: \"" + cmd + "\" failed (no error output)", file=sys.stderr)
    else:
      print("Error: \"" + cmd + "\" failed (" + str(err) + ")", file=sys.stderr)
    return 1

  return 0






def validate_xml_document(debug, force, src_dir, src_rel_path, tgt_rel_path):
  """
  src_dir: the document's top-level directory
  src_rel_path: the rel_path (to src_dir) to the 'val' file (i.e., what comes from the xiax:val attribute)
  tgt_rel_path: the rel_path (to src_dir) to the file to be validated
  NOTE: for both invocation cases, any validation errors go STDERR
  """

  if debug > 2:
    print("Spew: Inside validate_xml_documen()...")


  src_doc = etree.parse(src_rel_path) # this won't fail because it suceeded a moment ago in process()

  # get the 'xml-document' element
  xml_document = src_doc.getroot()[0]
  assert xml_document.tag == xiax_namespace+'xml-document'

  using_yang = xml_document[0]
  assert using_yang.tag == xiax_namespace+'using-yang'
  yang_modules = using_yang[0]
  assert yang_modules.tag == xiax_namespace+'yang-modules'
  modules_str = ""
  for yang_module in yang_modules.iterchildren(xiax_namespace+'yang-module'):
    file = os.path.join(src_dir, yang_module[0].text.strip())  # FIXME: yang_module[0] is just the 'name' field...
    if not os.path.isfile(file):
      extra=""
      if "YYYY-MM-DD" in file:
        extra=(" Note: running `xiax` directly against a 'val' file will not" +
               + " automatically generate YYYY-MM-DD dependencies.")
        print("Error: the YANG module (" + tgt_full_path + ") to validated the XML document ("
               + tgt_rel_path + ") doesn't exist." + extra , file=sys.stderr)
        return 1
    modules_str += file

  for el in xml_document.findall(xiax_namespace+'additional-xml-documents'):
    print("NOT IMPLEMENTED YET: additional-xml-documents")
    return 1


  # at this point, ...

  # calc full path to target file (YANG module), as the CWD may not be same as src_dir
  tgt_full_path = os.path.join(src_dir, tgt_rel_path)

  # ensure file exists
  if not os.path.isfile(tgt_full_path):
    extra=""
    if "YYYY-MM-DD" in tgt_full_path:
        extra=(" Note: running `xiax` directly against a 'val' file will not" +
                 + " automatically generate YYYY-MM-DD dependencies.")
    print("Error: the XML document to validate (" + tgt_full_path
           + ") doesn't exist." + extra , file=sys.stderr)
    return 1

  # validate it
  cmd = "yanglint %s %s" % (modules_str, tgt_full_path)
  p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  p.wait()
  if p.returncode != 0:
    err = p.stderr.read()
    if not err or err is None:
      print("Error: \"" + cmd + "\" failed (no error output)", file=sys.stderr)
    else:
      print("Error: \"" + cmd + "\" failed (" + str(err) + ")", file=sys.stderr)
    return 1

  return 0






def validate_content(debug, force, src_dir, src_rel_path, tgt_rel_path):
  """
  src_dir: the document's top-level directory
  src_rel_path: the rel_path (to src_dir) to the 'val' file (i.e., what comes from the xiax:val attribute)
  tgt_rel_path: the rel_path (to src_dir) to the file to be validated
  NOTE: for both invocation cases, any validation errors go STDERR
  """

  if debug > 2:
    print("Spew: Inside validate_content(%d, %s, %s, %s, %s)..." 
            % (debug, force, src_dir, src_rel_path, tgt_rel_path))

  # check if YYYY-MM-DD conversion needed
  # note: this routine only converts the embedded YYYY-MM-DD substrings; it does
  #       NOT recursively convert any referenced files.  This is to say that
  #       generating content is expected to occur AFTER the normal priming step.
  #       (this only matters for folks that run xiax directly against the val.xml)
  if "pytest" in sys.modules:
    YYYY_MM_DD = "1234-56-78"
  else:
    YYYY_MM_DD = date.today().strftime("%Y-%m-%d")

  if "YYYY-MM-DD" in os.path.basename(src_rel_path):  # on;y needed to when passed directly
    if debug > 2:
      print("Spew: filename \"" + os.path.basename(src_rel_path)
             + "\" has \"YYYY-MM-DD\" in it...")

    # calc new path
    new_src_rel_path = src_rel_path.replace("YYYY-MM-DD", YYYY_MM_DD)
    
    # ensure new_src_rel_path file doesn't already exist
    if os.path.isfile(new_src_rel_path) and force is False:
      print("Error: new \"source\" file \"" + new_src_rel_path + "\" already exists"
             + " (use \"force\" flag to override).", file=sys.stderr)
      return 1
  
    if debug > 2:
      print ("Spew: copying/patching " + src_rel_path + " to " + new_src_rel_path)

    # writeout new filename w/ substitutions
    with open(src_rel_path) as infile, open(new_src_rel_path, 'w') as outfile:
      for line in infile:
        line = line.replace("YYYY-MM-DD", YYYY_MM_DD)
        outfile.write(line)

    # swap before reentring normal flow
    src_rel_path = new_src_rel_path

  # determing what kind of generation is to occur, in order to
  # branch to the appropriate method
  doc = etree.parse(src_rel_path) # this won't fail because it suceeded a moment ago in process()
  root = doc.getroot()
  assert root.tag == xiax_namespace+'validate'

  if root[0].tag == xiax_namespace+'yang-module':
    doc = None # release reference 
    return validate_yang_module(debug, force, src_dir, src_rel_path, tgt_rel_path)

  elif root[0].tag == xiax_namespace+'xml-document':
    doc = None # release reference 
    return validate_xml_document(debug, force, src_dir, src_rel_path, tgt_rel_path)

  # add other generate request hendling logic here

  print("Error: unknown 'generate' request type \"" + root[0].tag + "\"", file=sys.stderr)
  return 1

