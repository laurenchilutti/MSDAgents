"""
Ingest FMSCoupler READMEs into Milvus.
Requires Milvus standalone on localhost:19530.
"""

from pathlib import Path
import doxygen_xml_parser
import markdownfile_parser

from client import Client
from utils import git_clone, run_doxygen

FMSCOUPLER_DIR = Path("./fmscoupler")
DOCS_DIR = FMSCOUPLER_DIR/"full/docs"
DOXYGEN_DIR = FMSCOUPLER_DIR/"docs"
XML_DIR = DOXYGEN_DIR/"xml"
MARKDOWN_DIR = FMSCOUPLER_DIR / "markdowns"
COLLECTION_NAME = "FMSCoupler"

DOC_FILES = [
    "README.md",
    "FLUX.md",
    "AtmosDataType.md",
    "IceDataType.md",
    "LandDataType.md",
    "OceanPublicType.md",
    "AtmosIceBoundaryType.md",
    "AtmosLandBoundaryType.md",
    "IceOceanBoundaryType.md",
    "LandIceAtmosBoundaryType.md",
    "OceanIceBoundaryType.md",
    "IceOceanDriverType.md",
]

XMLFILES = [
    "group__atm__land__ice__flux__exchange__mod.xml",
    "group__atmos__ocean__dep__fluxes__calc__mod.xml",
    "group__atmos__ocean__fluxes__calc__mod.xml",
    "group__flux__exchange__mod.xml",
    "group__full__coupler__mod.xml",
    "group__ice__ocean__flux__exchange__mod.xml",
    "group__land__ice__flux__exchange__mod.xml",    
]


# clone
git_clone("https://github.com/mlee03/fmscoupler.git", "doc/all-round1", FMSCOUPLER_DIR)

# run doxygen
run_doxygen(FMSCOUPLER_DIR)

all_collection_data = []

# parse code documentation
for xmlfile in XMLFILES:
    print(f"Processing {xmlfile}...")
    modxml = doxygen_xml_parser.FMSCouplerModuleDocument(XML_DIR, xmlfile)
    modxml.populate()
    mdfile = modxml.write_markdown(output_dir=MARKDOWN_DIR)
    collection_data = markdownfile_parser.parse(MARKDOWN_DIR, mdfile)
    all_collection_data.extend(collection_data)

for mdfile in DOC_FILES:
    print(f"parsing {mdfile}...", end=" ")
    docs = markdownfile_parser.parse(DOCS_DIR, mdfile)
    all_collection_data.extend(docs)

print(f"\nTotal: {len(all_collection_data)} collection data")

# Create the unified database
client = Client(COLLECTION_NAME, connect=True)
client.create_collection()
client.add_data(data=all_collection_data)
client.test_collection()

print("\nDatabase creation and testing completed successfully.")
