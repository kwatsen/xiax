from __future__ import unicode_literals
from distutils import dir_util
from pytest import fixture
import difflib
import filecmp
import xiax
import os


@fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir



def test_roundtrip_diff_dirs(datadir):
  orig_xml = str(datadir.join('draft-ietf-netconf-crypto-types-03.xml'))
  extract_xml = str(datadir.join('fakedir1', 'draft-foo-03.xml'))
  repacked_xml = str(datadir.join('fakedir2', 'draft-bar-03.xml'))

  
  result = xiax.process(3, False, orig_xml, extract_xml)
  assert result == 0

  result = xiax.process(3, False, extract_xml, repacked_xml)
  assert result == 0

  result = filecmp.cmp(orig_xml, repacked_xml)
  if result == False:
    file1 = open(orig_xml, 'r')
    file2 = open(repacked_xml, 'r')
    diff = difflib.unified_diff(file1.readlines(), file2.readlines())
    print('\n'.join(list(diff)))
  assert result == True



def test_roundtrip_same_dir(datadir):
  orig_xml = str(datadir.join('draft-ietf-netconf-crypto-types-03.xml'))
  extract_xml = str(datadir.join('draft-foo-03.xml'))
  repacked_xml = str(datadir.join('draft-bar-03.xml'))
  extract_xml2 = str(datadir.join('draft-baz-03.xml'))
  repacked_xml2 = str(datadir.join('draft-faz-03.xml'))

  result = xiax.process(3, False, orig_xml, extract_xml)
  assert result == 0

  result = xiax.process(3, False, extract_xml, repacked_xml)
  assert result == 0

  result = xiax.process(3, True, repacked_xml, extract_xml2)   # force == true
  assert result == 0

  result = xiax.process(3, False, extract_xml2, repacked_xml2)
  assert result == 0

  result = filecmp.cmp(orig_xml, repacked_xml2)
  if result == False:
    file1 = open(orig_xml, 'r')
    file2 = open(repacked_xml2, 'r')
    diff = difflib.unified_diff(file1.readlines(), file2.readlines())
    print('\n'.join(list(diff)))
  assert result == True








