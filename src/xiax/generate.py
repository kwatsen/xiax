from __future__ import print_function

import os
import sys
import subprocess
from lxml import etree
from datetime import date


#import pyang

xiax_namespace = '{https://watsen.net/xiax}'



def generate_tree_diagram(debug, force, src_dir, src_rel_path, dst_rel_path):
  if debug > 2:
    print("Spew: Inside generate_tree_diagram()...")

  # globals
  #src_dir = os.path.dirname(src_path)
  #src_file = os.path.basename(src_path)
  #dst_dir = os.path.dirname(dst_rel_path) if dst_rel_path.endswith(".xml") else dst_rel_path
  src_doc = etree.parse(src_rel_path) # this won't fail because it suceeded a moment ago in process()

  # get the 'tree-diagram' element
  tree_diagram_el = src_doc.getroot()[0]
  assert tree_diagram_el.tag == xiax_namespace+'yang-tree-diagram'

  source_el = tree_diagram_el.find('a:source', {'a':"https://watsen.net/xiax"})
  assert source_el != None
  assert source_el.tag == xiax_namespace+'source'

  source_el_uri_orig = source_el.text.strip()

  # notes:
  #  - wanted to use "urlparse", but is fails when '@' character is present
  #  - "len(uri_split[0])>1" lets Windows drives (e.g.: "c:") pass
  source_el_uri_split = source_el_uri_orig.split(':', 1)
  if len(source_el_uri_split)==2 and source_el_uri_split[0]!='file':
    if len(source_el_uri_split[0]) == 1:
      print("Error: a Windows-based drive path detected for the \"source\" element on " + src_file
             + ":" + str(source_el.sourceline) + " having value \"" + source_el_uri_orig + "\".",
             file=sys.stderr)
      return 1
    print("Error: the \"source\" element on " + src_file + ":" + str(source_el.sourceline) +
           +" having value \"" + source_el_uri_orig + "\" specifies a URI scheme other than \"file\".")
    return 1

  # normalize the relative path (i.e., remove any "file:" prefix)
  if len(source_el_uri_split)==1:
    source_el_rel_path = source_el_uri_split[0]
  else:
    source_el_rel_path = source_el_uri_split[1]

  # ensure the path is a local path
  if os.path.normpath(source_el_rel_path).startswith(('..','/')):
    print("Error: a non-local filepath is used for the \"source\" element on " + src_file + ":"
           + str(source_el.sourceline) + " having value \"" + source_el_uri_orig + "\".", file=sys.stderr)
    return 1

  # at this point, source_el_rel_path is considered okay (YYYY-MM-DD replacement, if any, already occurred)

  # calc full path to source file (YANG module), as the CWD may not be same as src_dir
  source_el_full_path = os.path.join(src_dir, source_el_rel_path)

  # ensure file exists
  if not os.path.isfile(source_el_full_path):
    extra=""
    if dst_rel_path == "":
        extra=(" Note: running `xiax` directly against a 'gen' file will not automatically"
               + " generate YYYY-MM-DD dependencies.")
    print("Error: the YANG module to generate the tree diagram for (" + source_el_full_path
           + ") doesn't exist." + extra , file=sys.stderr)
    return 1

  extra = ""
  if tree_diagram_el.find('a:print-yang-data', {'a':"https://watsen.net/xiax"}) is not None:
    extra = " --tree-print-yang-data"
    cmd = "pyang -f tree%s %s" % (extra, source_el_full_path)
  else:
    cmd = "yanglint -f tree%s %s" % (extra, source_el_full_path)

  p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  p.wait()
  if p.returncode != 0:
    err = p.stderr.read()
    if not err or err is None:
      print("Error: \"" + cmd + "\" failed (no error output)", file=sys.stderr)
    else:
      print("Error: \"" + cmd + "\" failed (" + str(err) + ")", file=sys.stderr)
    return 1


  if dst_rel_path == "":
    print(p.stdout.read().decode('utf-8'))
    return 0

  dst_full_path = os.path.join(src_dir, dst_rel_path)
  if os.path.isfile(dst_full_path) and force is False:
    print("Error: generated output file \"" + dst_full_path + "\" already exists"
           + " (use \"force\" flag to override).", file=sys.stderr)
    return 1

  fd = open(dst_full_path, 'w')
  fd.write(p.stdout.read().decode('utf-8'))
  fd.close()
  return 0





def generate_content(debug, force, src_dir, src_rel_path, dst_rel_path):
  """    
  src_dir: the document's top-level directory
  src_rel_path: the rel_path (to src_dir) to the 'val' file (i.e., what comes from the xiax:val attribute)
  dst_rel_path: where to save the generated content, or empty string for STDOUT
  """

  if debug > 2:
    print("Spew: Inside generate_content(%d, %s, %s, %s, %s)..."
           % (debug, force, src_dir, src_rel_path, dst_rel_path))

  # check if YYYY-MM-DD conversion needed
  # note: this routine only converts the embedded YYYY-MM-DD substrings; it does
  #       NOT recursively convert any referenced files.  This is to say that
  #       generating content is expected to occur AFTER the normal priming step.
  #       (this only matters for folks that run xiax directly against the gen.xml)
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
  assert root.tag == xiax_namespace+'generate'

  if root[0].tag == xiax_namespace+'yang-tree-diagram':
    doc = None # release reference 
    return generate_tree_diagram(debug, force, src_dir, src_rel_path, dst_rel_path)

  # add other generate request hendling logic here

  print("Error: unknown 'generate' request type \"" + root[0].tag + "\"", file=sys.stderr)
  return 1

