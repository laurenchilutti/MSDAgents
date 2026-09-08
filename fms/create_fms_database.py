from pathlib import Path
import subprocess

from parsers.fortran_parser import doxygen_xml_parser
import parsers.markdownfile_parser as markdownfile_parser
import parsers.markdownfile_parser as markdownfile_parser

from shared.client import newCollection
from shared.utils import git_clone, run_doxygen

import fmsfiles

FMS_DIR = Path("./FMS")
DOXYGEN_DIR = FMS_DIR/"docs"
XML_DIR = DOXYGEN_DIR/"xml"
COLLECTION_NAME = "FMS"
MARKDOWN_DIR = FMS_DIR / "markdowns"

bash_script = """

module load oneapi compiler mpi hdf5 netcdf libyaml

export CC="icx"
export FC="ifx"
export CPP="icx -E"
export FPP="ifx -E"
export CFLAGS="`nc-config --cflags` `nf-config --fflags` -O0 -g -traceback"
export FCFLAGS="`nc-config --cflags` `nf-config --fflags`-O0 -g -traceback -check all"

#set -e
cd FMS
autoreconf -if
./configure
make preprocess
"""

git_clone("https://github.com/laurenchilutti/FMS.git", "doxygen-fixes", FMS_DIR)

#process the Doxyfile.in to create a Doxyfile
doxy_in = FMS_DIR/"docs/Doxyfile.in"
doxy_out = FMS_DIR/"Doxyfile"
content = (
    doxy_in.read_text()
    .replace("@abs_top_builddir@", ".")
    .replace("@abs_top_srcdir@", ".")
    .replace("@PACKAGE_VERSION@", "main")
)

#run make preprocess in FMS to preprocess fortran files before doxygen generation
subprocess.run(bash_script, shell=True, executable='/bin/bash', check=True)

doxy_out.write_text(content)

run_doxygen(FMS_DIR)

all_collection_data = []

for xmlfile in fmsfiles.FMS_GROUP_FILES:
    print(f"Processing XML file: {xmlfile}")
    modxml = doxygen_xml_parser.ModuleDocument(XML_DIR, xmlfile)
    modxml.populate()
    mdfile = modxml.write_markdown(output_dir=MARKDOWN_DIR)
    all_collection_data.extend(markdownfile_parser.parse(MARKDOWN_DIR, mdfile))

#for mdfile in fmsfiles.FMS_MD_FILES:
#    print(f"Processing Markdown file: {mdfile}")
#    all_collection_data.extend(markdownfile_parser.parse(FMS_DIR, mdfile))

database = newCollection(COLLECTION_NAME, connect=True)
database.create_collection()
database.add_data(data=all_collection_data)
database.test_collection()

