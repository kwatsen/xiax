# xiax: eXtract or Insert artwork And sourcecode to/from Xml

Free software provided by Kent Watsen (Watsen Networks)


## Purpose

To aid in the construction (and deconstruction) of submittable `xml2rfc`
v2 [RFC 7749] and v3 [RFC 7991] documents.

  * For authors     : automates common steps.
  * For reviewers   : ensures correctness and facilitates validations.
  * For copyeditors : provides safety net for making changes.

```
  +----------+              +----------+     pack      +---------+
  |          |    prime     |          | ------------> |         |
  |  source  | -----------> |  primed  |               |  ready  |
  |          |              |          | <------------ |         |
  +----------+              +----------+     unpack    +---------+
                              |      ^
                              |      |
                              +------+
                              validate
```

## Installation

    `pip install xiax`

  * Developed on Python 3.7
  * Tested on Python 3.6, 3.5, 3.4, and 2.7.

## Usage

```
usage: xiax [-h] [-v] [-d] [-f] source [destination]

eXtract or Insert artwork And sourcecode to/from Xml

positional arguments:
  source         source XML document to extract from or insert into.
  destination    destination file or directory. If unspecified, then
                 the current working directory is assumed.

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show version number and exit.
  -d, --debug    print verbose output to stdout.
  -f, --force    allow existing files to be overwritten.

Exit status code: 0 on success, non-0 on error.  
Debug output goes to stdout. Error output goes to stderr.

```


## Auto-sensing Mode:

The "source" XML file is scanned for an XML comment beginning with the
string "##xiax-block-v1:".  If this string is found, then extraction
proceeds, else insertion proceeds.

Referring to the diagram above:

 - "insertion" refers to both priming and packing.
 - "extraction" refers only to unpacking.


## Insertion:

Insert local file content from `<artwork>` and `<sourcecode>` elements
into "source", saving the resulting "packed" XML file into as described
below.

The "source" parameter must refer to an XML file containing the `<rfc>`
element.  

If the "destination" parameter ends with ".xml", the argument is used 
to determined both the destination directory, as well as the draft's 
revision number.  For instance, "./foo-03.xml" would set the current
working directory to be the destination directory, and "03" as the
revision number to be used.

If the "destination" parameter is present, but does not end with ".xml",
then the argument is used only to determined the destination directory.
The system will try to determine the draft revision number as the next
logical `git tag` (see [Git Tagging] below) and, if that doesn't work,
will assume "-00".  The determined revision number is placed into the
"source" filename, either by replacing "latest" with it (if found), or
by appending it (e.g., both "foo.xml" and "foo-latest.xml" might result
in foo-00.xml).

If the "destination" parameter is not provided, then the current working
directory is used (same as if "./" had been passed).

In the source XML file, the `<rfc>` element `docName` attribute may
include the suffix "-latest", which will be replaced with the determined
revision number.  This is recommended.  The `<rfc>` element should also
defined the "xiax" prefix (e.g., `xmlns:xiax="https://watsen.net/xiax"`).

In the source XML file, only `<artwork>` and `<sourcecode>` elements
having a `xiax:src` (for "source') or `xiax:gen` (for "generate")
attribute are processed (it is an error if both attributes appear for
the same element).  Both attributes take a URI, but the URI must specify
a local file under the draft document's directory.

Valid "xiax:src" attribute examples:
  - xiax:src="ietf-foobar@YYYY-MM-DD.yang"
  - xiax:src="images/ex-ascii-art.txt"
  - xiax:src="file:ietf-foobar@YYYY-MM-DD.yang"
  - xiax:src="file:images/ex-ascii-art.txt"
  
Invalid "src" attribute examples:
  - xiax:src="/ex-ascii-art.txt"
  - xiax:src="c:/ex-ascii-art.txt"
  - xiax:src="a/../../ex-ascii-art.txt"
  - xiax:src="file:///ex-ascii-art.txt"
  - xiax:src="file://c/ex-ascii-art.txt"
  - xiax:src="file:a/../../ex-ascii-art.txt"

Notes:
  * The `xiax:gen` and `xiax:val` attributes have the same pattern.
  * Any strings containing "YYYY-MM-DD" (either in the "source" 
    XML file, or in the linked filename or content) will be updated
    to have the value of the current.

It is an error if there is preexisting content for the `<artwork>` or 
`<sourcecode>` element.  A solution for inserting "fallback" content
while preserving an `xml2rfc` "src" attribute to binary (i.e., SVG)
content has yet to be defined.

In addition to the `xiax:src` and `xiax:gen` attributes, an optional
`xiax:val` (for "validate") attribute may be specified, to define
parameters for validating the `<artwork>` and `<sourcecode>` element's
content.  Additionally, a `xiax:markers` attribute may be specified
to wrap the content with the `<CODE BEGINS>` and `<CODE ENDS>` tags
described in RFC 8407 Section 3.2.

Additionally, `xiax` will automatically fold any content containing
a line exceeding 69 characters, using the algortihm defined in
draft-ietf-netmod-artwork-folding.  (Note: this logic isn't
implemented yet).

The result of the insertion process is the creation of the determined
destination XML file in which all `xiax:` prefixed attrbutes in the
`<rfc>`, `<artwork>`, and `<sourcecode>` elements have been removed,
and an XML comment beginning with the string "##xiax-block-v1:" is
added to the end of the XML file.
 
It is an error for the destination file to already exist, unless the
"force" flag is specified, in which case the destination file will be
overwritten. 

The source XML file is never modified.


## Extraction:

Extract the content of `<artwork>` and `<sourcecode>` elements, having
an entry in the "xiax-block" comment into the specified extraction
directory.  <!-- Also extract elements having the "originalSrc"
attribute set? -->

If the "destination" parameter ends with ".xml", the argument is used 
to determined both the extraction directory, as well as the unpacked
draft name.  Note: the "unpacked" (or "primed") XML file is extracted
only when the destination parameter ends with ".xml".

If the "destination" parameter is present, but does not end with ".xml",
then the argument is used only to determined the extraction directory
(the unpacked draft XML file will not be saved).

If the "destination" parameter is not provided, then the current working
directory is used as the extraction directory.  This is the same as if
"./" were passed.

Only `<artwork>` and `<sourcecode>` elements having entries in the
"xiax-block" are extracted.  The extracted files are relative to the 
extraction directory.  Subdirectories will be created as needed.

In addition to the element's content being extracted, all the additional
files used to generate and validate the content are also extracted.
This not only includes the files referenced by the `xiax:gen` and
`xiax:val` attributes, but also any additional local files files
referenced by those files.

It is an error if any file already exists, unless the "force" flag is
specified, in which case the file will be overwritten. 

It is planned to implement the ability to automatically validate the
`xiax:src` and `xiax:gen` content, but this is somewhat dependent on
input from users, as it may be sufficient the know that the validations
ran authomatically during "insertion" and that they may be manually
run after the extraction.

The source XML file is never modified.


## Round-tripping

It is possible to run `xiax` in a loop:

```
  # xiax -f -s packed-00.xml -d unpacked-00.xml
  # xiax -f -s unpacked-00.xml -d packed-00.xml
```


## Git Tagging

Git tags should (assuming `git` is being used as the SCM) be used to 
tag milestones.  In the context of authoring documents, the milestones 
are the published versions of the draft in progress.

By example, assuming that draft-<foo>-03 has already been published, 
which implies that 02, 01, and 00 were published before as well, than 
`get tag` should produce the following result in the working directory:

```
# git tag
draft-<foo>-00
draft-<foo>-01
draft-<foo>-02
draft-<foo>-03
```


## Special Support

Typically the "source" parameter specifies an `xml2rfc` XML file but, in
order to support the development of the "generate" and "validate" files,
these XML files MAY be passed as the "source" parameter instead, in which
case `xiax` just processes the single file.

If the "source" parameter specifies a "generate" file, the "destination"
parameter, if passed, will be ignored, as the generated content is sent
to STDOUT.

If the "source" parameter specifies a "validate" file, the "destination"
parameter must specify the relative path to the file to be validated.

Running `xiax` this way must occur from the draft document's top-level
directory (the current working directory is the document's directory).


