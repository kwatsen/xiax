# xiax: eXtract or Insert artwork And sourcecode to/from Xml

Free software provided by Kent Watsen (Watsen Networks)


## Purpose

To aid in the construction (and destruction) of submittable `xml2rfc`
v2 [RFC 7749] and v3 [RFC 7991] documents.

  * For authors   : automates common steps.
  * For reviewers : facilitates validations.

```
  +----------+              +----------+    pack     +---------+
  |          |   prime      |          |------------>|         |
  |  source  | -----------> |  primed  |             |  ready  |
  |          |              |          | <---------- |         |
  +----------+              +----------+    unpack   +---------+
                              |      ^
                              |      |
                              |      |
                              +------+
                              validate
```
See bottom for [details].


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

Note, referring to the diagram above:

 - insertion includes both priming and packing.
 - extraction includes only unpacking.


## Insertion:

Insert local file content from `<artwork>` and `<sourcecode>` elements
into "source", saving the resulting "packed" XML file into as described
below.

If the "destination" parameter ends with ".xml", the argument is used 
to determined both the destination directory, as well as the draft's 
revision number.  For instance, "./foo-03.xml" would set the current
working directory and "03" (as the revision number) to be used.

If the "destination" parameter is present, but does not end with ".xml",
then the argument is used only to determined the destination directory.
The system will try to determine the draft revision number as the next
logical `git tag` (see [Git Tagging] below) and, if that doesn't work,
assumes "-00".

If the "destination" parameter is not provided, then the current working
directory is used (same as if "./" had been passed).

The draft's revision number is used only to i) set the destination 
filename, if not specified, and ii) set the `docName` attribute in the
destination file.  Destination directories are created as needed.
    
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
If no extraction directory is specified, the current working directory
is used.  The `<artwork>` and `<sourcecode>` elements are extracted into
subdirectories as specified by the "originalSrc" attribute.  Directories
will be created as needed.

If the "destination" parameter is ends with ".xml", the argument is used 
to determined both the destination directory, as well as the unpacked
draft name.

If the "destination" parameter is present, but does not end with ".xml",
then the argument is used only to determined the destination directory
for unpacking the artwork and sourcecode elements (the unpacked draft
XML file will not be saved).

If the "destination" parameter is not provided, then the current working
directory is used.

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

Notes:

  * The "-latest" suffix on the source XML filename is optional.

  * Inside the source XML file:

     - the `docName` attribute must end with "-latest".
       (.e.g, `docName="draft-attrib-wg-foobar-latest"`).

     - for `<sourcecode>` and `<artwork>` elements referring to files
       having "YYYY-MM-DD" in their names, the string "YYYY-MM-DD"
       must be included (e.g. `src="foobar@YYYY-MM-DD.yang"`).

       FIXME: this is kind of annoying (much like the "-latest"
              suffix), worth trying to fix?

  * Inside included files containing dates:

     - the placeholder date "YYYY-MM-DD" must be used (e.g.,
       `revision "YYYY-MM-DD" { ... }`).


#### Primed

The "primed" state is an intermediate state whereby:

  - All referenced artwork and source code files having the string
    "YYYY-MM-DD" in their filename are updated as follows:

    * the "YYYY-MM-DD" in the filename is replaced.
    * any occurrence of "YYYY-MM-DD" within the file is replace.

  - The source XML file is updated as follows:

    * the "-latest" suffix of the filename is replace with "-primed"

It is in this state that validation can occur, as the artwork and
source code files have proper names and content.


#### Ready

The "ready" state is the final submission-worthy state whereby:

  - `-primed` (both in the filename and the `docName` attribute) is
    converted to the appropriate draft revision number (e.g., from
    `git tag`).

  - all <artwork> and <sourcecode> elements having `src` attributes
    referring to a local file are "packed" into the XML document
    (i.e., their content is the XML element's "text" value), wrapped
    by CDATA tags (if needed), and folded (if needed, and supported),
    and including the `<CODE BEGINS>` and `<CODE ENDS>` tags (if requested,
    via the `markers="true"` attribute).
 

### Transitions

There are 4 transitions: Primed, Pack, Unpack, and Ready.


#### Prime

The "prime" transition performs the following actions:

  - in the source XML file:

      * the "-latest" suffix in the `docName` attribute is replaced
        with "-primed".
      * any occurrence of "YYYY-MM-DD" within the file is replace,
        regardless if specific to an <artwork> or <sourcecode> element
        or not.

    and the source XML file is saved using the "-primed" suffix.

  - in any referenced artwork and source code files having the string
    "YYYY-MM-DD" in their filename:

      * any occurrence of "YYYY-MM-DD" within the file is replace.

    after which the file is saved with the "YYYY-MM-DD" in the filename
    is replaced with the current date's value.


Note: the priming step is a no-op if none of the above is true, which
      enables round-tripping between the "primed" and "ready" states.


#### Pack

The "pack" transition performs the "insertion" logic described above.

The ability to auto-generate derived artwork (e.g., tree diagrams
[RFC 8340]) will be included in a subsequent update (FIXME).

The ability to auto-fold sourcecode will be included in a subsequent
update (FIXME).

The ability to execute validation logic as a pre-step will be included
in a subsequent update (FIXME).



#### Unpack

The "unpack" transition reverts the "pack" operation.  Essentially, it
takes a single XML file as input and populates a directory with the
content of the <artwork> and <sourcecode> elements.

The extraction of the artwork/sourecode elements alone is sufficient
for supporting reviews (and validation), but the "primed" XML file can
optionally be written out, if the "destination" parameter ends with
".xml".

The ability to re-generate derived artwork (e.g., tree diagrams) and
compare to artwork found in the draft will be included in a subsequent
update (FIXME).

The ability to auto-unfold sourcecode will be included in a subsequent
update (FIXME).

The ability to execute validation logic as a post-step will be included
in a subsequent update (FIXME).



#### Validate

This transition is not implemented yet, due to uncertainty for how to
encode the validation logic into the "ready" XML file, or even if that
makes sense. (FIXME)





