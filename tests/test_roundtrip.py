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
  orig = str(datadir.join('draft-kwatsen-git-xiax-automation.xml'))
  pack1 = str(datadir.join('fakedir1', 'draft-foo-03.xml'))
  unpack1 = str(datadir.join('fakedir2', 'draft-foo-03.xml'))
  pack2 = str(datadir.join('fakedir3', 'draft-foo-03.xml'))
  
  result = xiax.process(3, False, orig, pack1)
  assert result == 0

  result = xiax.process(3, False, pack1, unpack1)
  assert result == 0

  result = xiax.process(3, False, unpack1, pack2)
  assert result == 0

  result = filecmp.cmp(pack1, pack2)
  if result == False:
    file1 = open(pack1, 'r')
    file2 = open(pack2, 'r')
    diff = difflib.unified_diff(file1.readlines(), file2.readlines())
    print('\n'.join(list(diff)))
  assert result == True



def test_roundtrip_same_dir(datadir):
  orig = str(datadir.join('draft-kwatsen-git-xiax-automation.xml'))
  pack1 = str(datadir.join('packed-03.xml'))
  unpack1 = str(datadir.join('unpacked-03.xml'))
  pack2 = str(datadir.join('packed-03.xml'))

  result = xiax.process(3, False, orig, pack1)
  assert result == 0

  result = xiax.process(3, True, pack1, unpack1)
  assert result == 0

  result = xiax.process(3, True, unpack1, pack2)
  assert result == 0

  result = filecmp.cmp(pack1, pack2)
  if result == False:
    file1 = open(pack1, 'r')
    file2 = open(pack2, 'r')
    diff = difflib.unified_diff(file1.readlines(), file2.readlines())
    print('\n'.join(list(diff)))
  assert result == True








