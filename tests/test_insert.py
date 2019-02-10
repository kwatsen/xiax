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




## Positive tests

def test_insert_okay_v2(datadir):
  insert_okay_v2_src = datadir.join('insert-okay-v2-src.xml')
  insert_okay_v2_dst = datadir.join('insert-okay-v2-dst.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_okay_v2_src), str(tmp_dst))
  assert result == 0
  result = filecmp.cmp(str(insert_okay_v2_dst), str(tmp_dst))
  if result == False:
    file1 = open(insert_okay_v2_dst, 'r')
    file2 = open(tmp_dst, 'r')
    diff = difflib.unified_diff(file1.readlines(), file2.readlines())
    print('\n'.join(list(diff)))
  assert result == True



## Skip tests  

def test_insert_skip1_v2(datadir):
  insert_skip_v2_src = datadir.join('insert-skip-v2-src.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_skip_v2_src), str(tmp_dst))
  assert result == 0
  result = filecmp.cmp(str(insert_skip_v2_src), str(tmp_dst))
  if result == False:
    file1 = open(insert_skip_v2_src, 'r')
    file2 = open(tmp_dst, 'r')
    diff = difflib.unified_diff(file1.readlines(), file2.readlines())
    print('\n'.join(list(diff)))
  assert result == True




## Negative tests

def test_src_missing():
  result = xiax.process(True, False, "", "foo")
  assert result == 1
  result = xiax.process(True, False, "foo", "foo")
  assert result == 1

def test_insert_fail1_v2(datadir):
  insert_fail1_v2_src = datadir.join('insert-fail1-v2.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_fail1_v2_src), str(tmp_dst))
  assert result == 1

def test_insert_fail2_v2(datadir):
  insert_fail2_v2_src = datadir.join('insert-fail2-v2.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_fail2_v2_src), str(tmp_dst))
  assert result == 1

def test_insert_fail3_v2(datadir):
  insert_fail3_v2_src = datadir.join('insert-fail3-v2.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_fail3_v2_src), str(tmp_dst))
  assert result == 1

def test_insert_fail4_v2(datadir):
  insert_fail4_v2_src = datadir.join('insert-fail4-v2.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_fail4_v2_src), str(tmp_dst))
  assert result == 1

def test_insert_fail5_v2(datadir):
  insert_fail5_v2_src = datadir.join('insert-fail5-v2.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_fail5_v2_src), str(tmp_dst))
  assert result == 1

#def test_insert_fail6_v2(datadir):
#  insert_fail6_v2_src = datadir.join('insert-fail6-v2.xml')
#  tmp_dst = datadir.join('tmp_dst.xml')
#  result = xiax.process(True, False, str(insert_fail6_v2_src), str(tmp_dst))
#  assert result == 1

def test_insert_fail7_v2(datadir):
  insert_fail7_v2_src = datadir.join('insert-fail7-v2.xml')
  tmp_dst = datadir.join('tmp_dst.xml')
  result = xiax.process(True, False, str(insert_fail7_v2_src), str(tmp_dst))
  assert result == 1

