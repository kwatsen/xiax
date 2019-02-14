# xiax: eXtract or Insert artwork And sourcecode to/from Xml

Free software provided by Kent Watsen (Watsen Networks)


## Purpose

To aid in the construction (and destruction) of submittable `xml2rfc`
v2 [RFC 7749] and v3 [RFC 7991] documents.

  * For authors   : automates common steps.
  * For reviewers : facilitates validations.

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

The "source" XML file is scanned for any `<artwork>` or `<sourcecode>`
elements containing an "originalSrc" attribute.  If any "originalSrc" 
attribute is found, then extraction proceeds, else insertion proceeds.

Referring to the diagram above:

 - "insertion" refers to both priming and packing.
 - "extraction" refers only to unpacking.


## Insertion:

Insert local file content from `<artwork>` and `<sourcecode>` elements
into "source", saving the resulting "packed" XML file into as described
below.

The "source" parameter must refer to an XML file that may be "raw" or
"primed" (i.e., external tools can do the priming step).  If it is
intended that the destination filename be determined (see "destination"
parameter below), a primed filename should match the pattern
`.*[0-9]{2}.xml`, whereas a raw filename should have the form
"foo-latest.xml" or "foo.xml", in either case the result is
"foo-00.xml", assuming revision "00".

If the "destination" parameter ends with ".xml", the argument is used 
to determined both the destination directory, as well as the draft's 
revision number.  For instance, "./foo-03.xml" would set the current
working directory to be the destination directory, and "03" as the
revision number to be used.

If the "destination" parameter is present, but does not end with ".xml",
then the argument is used only to determined the destination directory.
The system will try to determine the draft revision number as the next
logical `git tag` (see [Git Tagging] below) and, if that doesn't work,
will assume "-00".

If the "destination" parameter is not provided, then the current working
directory is used (same as if "./" had been passed).

In the source XML file, the `<rfc>` element `docName` attribute may
include the suffix "-latest", which will be replaced with the determined
revision number.  The only time `docName` should not end with "-latest"
is when the source XML file has been pre-primed.

In the source XML file, only `<artwork>` and `<sourcecode>` elements
having a `src` attribute representing a local file are processed.
Local files are specified by using of the "file" scheme or by using
no scheme.

It is an error for the "src" attribute to refer to a file that is not
contained by the source XML document's directory.  Files may be in
subdirectories.  This is consistent with RFC 7998 Section 7. To ensure
cross-platform extractions, directories must be specified using forward
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

Note that any strings containing "YYYY-MM-DD" (either in the "source" 
XML file, or in the linked filename or content) will be updated to 
have the value of the current.

It is an error if there is preexisting content for the `<artwork>` or 
`<sourcecode>` element.  This is consistent with RFC 7991 Section 2.48.3,
and not in conflict with Section 2.5.6, which has Errata filed against
it, since "src" attributes containing a scheme (e.g., "https") are 
skipped, thus preserving the "fallback" support described in Section 
2.5.  A solution for inserting "fallback" content while preserving a 
"src" attribute to binary (i.e., SVG) content has yet to be defined.

The result of the insertion process is the creation of the specified
destination XML file in which each `<artwork>` and `<sourcecode>` 
element processed will have i) the "src" attribute renamed to 
"originalSrc" and ii) the content of the referenced file as its text,
wrapped by wrapped by character data (CDATA) tags.  If the <artwork>
or sourcecode element has the attribute `markers="true"`, then the text
will also be wrapped by the `<CODE BEGINS>` and `<CODE ENDS>` tags
described in RFC 8407 Section 3.2.   Auto-folding will be added later,
when draft-ietf-netmod-artwork-folding finalizes (FIXME).  The ability
to auto-generate derived views (e.g., tree diagrams) will be added
later (FIXME).
 
It is an error for the destination file to already exist, unless the
"force" flag is specified, in which case the destination file will be
overwritten. 

The source XML file is never modified.


## Extraction:

Extract the content of `<artwork>` and `<sourcecode>` elements, having an
"originalSrc" attribute set, into the specified extraction directory.

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

Only `<artwork>` and `<sourcecode>` elements have the "originalSrc"
attribute set are extracted.  The extracted files are relative to the 
extraction directory.  Subdirectories will be created as needed.

It is an error if any file already exists, unless the "force" flag is
specified, in which case the file will be overwritten. 

The source XML file is never modified.


## Round-tripping

It is possible to run `xiax` in a loop:

```
  # xiax -f -s packed.xml -d unpacked.xml
  # xiax -f -s unpacked.xml -d packed.xml
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



## Details

This section describes the states and transitions for the state machine
diagram provided at the top of this page.


### States

There are 3 states: Source, Primed, and Ready.

#### Source

The "source" state represents the state of the author's files, as they
might be checked into a source control system (i.e., GitHub).  Notably,
the files in this state cannot bind any specific numbers, neither the
draft version (e.g. -03) or the current date.

Example source tree structure:

```
    draft-attrib-wg-foobar[-latest].xml
    foobar@YYYY-MM-DD.yang
    foobar-YYYY-MM-DD.asn1
    examples/
      ex1.xml
      ex2.json
      ex3.asn1
      etc.
```

#### Primed

The "primed" state is an intermediate state whereby:

  - All "-latest" suffixes are resolved to the determined revision number.
  - All occurrances or YYYY-MM-DD are resolved to the current date.
  - All "derived views" (e.g., tree diagrams) have been generated (FIXME: not implemented yet)

It is in this state that validation can occur, as the artwork and
source code files have proper names and content.


#### Ready

The "ready" state is the final submission-worthy state whereby there is a
single XML file that can be submitted to the IETF Submission tool.

 

### Transitions

There are 4 transitions: Primed, Pack, Unpack, and Ready.


#### Prime

The "prime" transition performs the following actions:

  - for in any locally referenced artwork and source code files having
    "YYYY-MM-DD" in their filename

      * any occurrence of "YYYY-MM-DD" within the file is replace.
      * the modified file is saved with the "YYYY-MM-DD" in the filename
        is replaced with the current date.

The ability to auto-generate derived artwork (e.g., tree diagrams
[RFC 8340]) will be included in a subsequent update (FIXME).


#### Pack

The "pack" transition performs the "insertion" logic described above.

The ability to automatically execute validation logic as a pre-step
will be included in a subsequent update (FIXME).

The ability to auto-fold sourcecode will be included in a subsequent
update (FIXME).


#### Unpack

The "unpack" transition reverts the "pack" operation.  A single XML
file is provided as input and the extraction directory is populated
with the content of the <artwork> and <sourcecode> elements and,
optionally, the unpacked/primed XML file.

The extraction of the artwork/sourecode elements alone is sufficient
for reviews (and validation).  The extraction of the unpacked/primed
XML file is only interesting for round-tripping purposes.

The ability to auto-unfold sourcecode will be included in a subsequent
update (FIXME).

The ability to execute validation logic as a post-step will be included
in a subsequent update (FIXME).



#### Validate

This transition is not implemented yet, due to uncertainty for how to
encode the validation logic into the "ready" XML file, or even if that
makes sense. (FIXME)

Validation will include three forms:

  - is a schema file a valid schema file
  - is an instance data file valid to a schema file
  - is a derived view (e.g., tree diagram) valid to a schema file

