# xiax: eXtract or Insert artwork And sourcecode to/from Xml
 

## Usage

```
usage: xiax [-h] [-v] [-d] [-f] source [destination]

eXtract or Insert artwork And sourcecode to/from Xml

positional arguments:
  source         source XML document to extract from or insert into.
  destination    destination file or directory. If unspecified, then the
                 current working directory is assumed.

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show version number and exit.
  -d, --debug    print verbose output to stdout.
  -f, --force    allow existing files to be overwritten.

Exit status code: 0 on success, non-0 on error. Error output goes to stderr.
```

## Auto-sensing Mode:

The "source" XML file is scanned for any `<artwork>` or `<sourcecode>`
elements containing an "originalSrc" attribute.  If any "originalSrc" 
attribute is found, then extraction proceeds, else insertion proceeds.

## Extraction:

Extract the content of `<artwork>` and `<sourcecode>` elements, having an
"originalSrc" attribute set, into the specified extraction directory.
If no extraction directory is specified, the current working directory
is used.  The `<artwork>` and `<sourcecode>` elements are extracted into
subdirectories as specified by the "originalSrc" attribute.  Directories
will be created as needed.

If "dst" represents an XML file, by ending with ".xml", the extraction
directory is determined to be the directory name part of "dst".  If
no directory name part exists, then the current working directory is
assumed.  Extraction proceeds as described above, followed by the saving
of the "unpacked" XML file.

It is an error if any file already exists, unless the "force" flag is
specified, in which case the file will be overwritten. 

The source XML file is never modified.


## Insertion:

Insert local file content into `<artwork>` and `<sourcecode>` elements,
saving the resulting XML "packed" file into "dst".  If "dst" does
not end with ".xml", it is assumed to represent a directory, in which
case a file having the same name as the source file will be saved into
that directory.  Directories will be created if needed.  If  "dst" is
not specified, then the current working directory is used.  In any
case, the resulting destination XML file must be different than the
source XML file.
    
In the source XML file, only `<artwork>` and `<sourcecode>` elements
having a "src" attribute representing a local file are processed.
Local files are specified by using of the "file" scheme or by using
no scheme.

It is an error for the "src" attribute to refer to a file that is not
contained by the source XML document's directory.  Files may be in
subdirectories.  This is consistent with RFC 7998 Section 7. To ensure
cross-platform extractions, directories must specified using forward
slashes.  

Valid "src" attribute examples:
  - src="ietf-foobar@YYYY-MM-DD.yang"
  - src="images/ex-ascii-art.txt"
  - src="file:ietf-foobar@YYYY-MM-DD.yang"
  - src="file:images/ex-ascii-art.txt"
  
Invalid "src" attribute examples:
  - src="/ex-ascii-art.txt"
  - src="c:/ex-ascii-art.txt"
  - src="a/../../ex-ascii-art.txt"
  - src="file:///ex-ascii-art.txt"
  - src="file://c/ex-ascii-art.txt"
  - src="file:a/../../ex-ascii-art.txt"

It is an error if there is preexisting content for the `<artwork>`
or `<sourcecode>` element.  This is consistent with RFC 7991 Section
2.48.3, and not in conflict with Section 2.5.6, which has Errata
filed against it, since "src" attributes containing a scheme (e.g.,
"https") are skipped, thus preserving the "fallback" support
described in Section 2.5.  A solution for inserting "fallback"
content while preserving a "src" attribute to binary (i.e., SVG)
content has yet to be defined.

The result of the insertion process is the creation of the specified
destination XML file in which each `<artwork>` and `<sourcecode>` element
processed will have i) the "src" attribute renamed to "originalSrc"
and ii) the content of the referenced file as its text, wrapped by
wrapped by character data (CDATA) tags.  It the artwork/sourcecode
element has the attribute markers="true", then the text will also
be wrapped by the `<CODE BEGINS>` and `<CODE ENDS>` tags described in
RFC 8407 Section 3.2.
 
It is an error for the destination file to already exist, unless
the "force" flag is specified, in which case the destination file
will be overwritten. 

The source XML file is never modified.


## Round-tripping

It is possible to run `xiax` in a loop:

```
  # xiax -f -s original.xml -d expanded.xml
  # xiax -f -s expanded.xml -d original.xml
```

## Background

Primarily developed to support`xml2rfc` v2 [RFC 7749] and v3 [RFC 7991] 
based XML documents, and the IETF RFC publishing process in general, 
but may be used for any XML based document containing elements called 
"artwork" or "sourcecode". 
