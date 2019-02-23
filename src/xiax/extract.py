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
from . import __version__
from .common import xiax_namespace
from .common import xiax_block_v1_header



# Force stable gzip timestamps
class FakeTime:
      def time(self):
            return 1225856967.109
gzip.time = FakeTime()




def extract(debug, force, src_path, dst_path):
   if debug > 2:
      print("Spew: entering extract(%d, %s, %s, %s)" % (debug, force, src_path, dst_path))


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
         #os.makedirs(dst_dir, exist_ok=True)      # exist_ok doesn't exist < 3.4 !!!
         os.makedirs(dst_dir)
      except Exception as e:
         e_type, e_val, e_tb = sys.exc_info()
         if not (e_type == OSError and e.errno == errno.EEXIST):   # for 2.7
            template = "Error: os.makedirs('{}') failed on {}:{} [{!r}]"
            message = template.format(dst_dir, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
            print(message, file=sys.stderr)
            return 1

   src_doc = etree.parse(src_path) # this won't fail because it suceeded a moment ago in process()


   # extract the xiax-block
   for el in src_doc.getroot().iterchildren(etree.Comment):
   #for el in doc.xpath('/rfc/comment()'):
      if xiax_block_v1_header in el.text:
         text=el.text.replace(xiax_block_v1_header + "\n", "")
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

   # set the 'xiax' namespace before entrying this loop, so its attempts to rewrite attributes don't fail
   # note: lxml doesn't offer a clean way to do this, so some hackery is needed (the 'DELETEME' attrib
   #       is removed just before save at end...
   etree.register_namespace('xiax', 'https://watsen.net/xiax')
   src_doc.getroot().set(xiax_namespace+'DELETEME', 'true')

   for inclusion in xiax_block.findall("a:inclusion", {'a':"https://watsen.net/xiax"}):
      p = inclusion[0].text   # [0] is the 'path' child
      el = src_doc.find(p)
      if el.text == None:
         print("Error: no content exists for the artwork/sourcecode element on line " + str(el.sourceline)
                  + " having 'originalSrc' value \"" + attrib_orig + "\".", file=sys.stderr)
         return 1

      
      src_el = inclusion.find("a:src", {'a':"https://watsen.net/xiax"})
      gen_el = inclusion.find("a:gen", {'a':"https://watsen.net/xiax"})
      if src_el != None:
        tag_el = src_el
        tag_str = "src"
      elif gen_el != None:
        tag_el = gen_el
        tag_str = "gen"


      attrib_orig = tag_el[0].text    # [0] is the 'attrib' child
      attrib_split = attrib_orig.split(':', 1) # don't need to scrutinize, like before, since it came from xiax-block

      # normalize the relative path (i.e., remove any "file:" prefix)
      if len(attrib_split)==1:
         attrib_rel_path = attrib_split[0]
      else:
         attrib_rel_path = attrib_split[1]

      # calc full dst path for this inclusion
      attrib_full = os.path.join(dst_dir, attrib_rel_path)


      # minor segue: if 'gen' then save the text content to the ".out" file, and the
      # gen file iteself (from the xiax-block) to the "attrib_full" file...
      if tag_str == "gen":
         gen_file_el = gen_el[1]   # [1] is the 'file' child
         if os.path.isfile(attrib_full) and force is False:
            print("Error: file \"" + attrib_full + "\" already exists for the artwork/sourcecode element on line "
                   + str(el.sourceline) + " having 'xiax:" + tag_str + "' value \"" + attrib_orig + "\""
                   + " (use \"force\" flag to override).", file=sys.stderr)
            return 1

         attrib_full_dir = os.path.dirname(attrib_full)
         if not os.path.exists(attrib_full_dir):
            try:
               #os.makedirs(dst_dir, exist_ok=True)      # exist_ok doesn't exist < 3.4 !!!
               os.makedirs(attrib_full_dir)
            except Exception as e:
               e_type, e_val, e_tb = sys.exc_info()
               if not (e_type == OSError and e.errno == errno.EEXIST):   # for 2.7
                  template = "Error: os.makedirs('{}') failed on {}:{} [{!r}]"
                  message = template.format(attrib_full_dir, os.path.basename(e_tb.tb_frame.f_code.co_filename), e_tb.tb_lineno, e_val)
                  print(message, file=sys.stderr)
                  return 1
   
         # copy contents of xiax-block's element's "text" to specified file
   
         # this following line doesn't work on 2.7:
         #    ^-- attrib_full_fd = open(attrib_full, 'w' if force else 'x')
         if os.path.isfile(attrib_full) and force == False:
            print("Error, file \"" + attrib_full + "\" already exists (use \"force\" flag to override).",
                  file=sys.stderr)
            return 1
         if "2.7" in sys.version:
            attrib_full_fd = open(attrib_full, 'wb')
            attrib_full_fd.write(gen_file_el.text.encode('utf-8'))
         else:
            attrib_full_fd = open(attrib_full, 'w')
            attrib_full_fd.write(gen_file_el.text)
         attrib_full_fd.close()

         if debug > 0:
            print("Saved 'gen' file to file " + attrib_full)
         # now that this is complete, reset the value of the "attrib_full" variable so that 
         # the gen-ed content is saved to the ".out" file in the normal flow logic below...
         attrib_full += ".out"


      # ensure file doesn't exist yet, without force
      if os.path.isfile(attrib_full) and force is False:
         print("Error: file \"" + attrib_full + "\" already exists for the artwork/sourcecode element on line "
                + str(el.sourceline) + " having 'xiax:" + tag_str + "' value \"" + attrib_orig + "\"" 
                + " (use \"force\" flag to override).", file=sys.stderr)
         return 1

      # okay, ready to do the extraction

      attrib_full_dir = os.path.dirname(attrib_full)
      if not os.path.exists(attrib_full_dir):
         try:
            #os.makedirs(dst_dir, exist_ok=True)      # exist_ok doesn't exist < 3.4 !!!
            os.makedirs(attrib_full_dir)
         except Exception as e:
            e_type, e_val, e_tb = sys.exc_info()
            if not (e_type == OSError and e.errno == errno.EEXIST):   # for 2.7
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
      #    ^-- attrib_full_fd = open(attrib_full, 'w' if force else 'x')
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
      el.set(xiax_namespace+tag_str, attrib_orig)
      if markers:
         el.set(xiax_namespace+'markers', 'true')
      el.tail = tail

      # end of long for loop


   # remove the attribute used to install the namespace prefix on root node
   del src_doc.getroot().attrib[xiax_namespace+'DELETEME']

   # Now save the "unpacked" XML file, only if requested

   if dst_file:
      # this code doesn't work on 2.7:
      #    ^-- dst_path_fd = open(dst_path, 'w' if force else 'x')
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

