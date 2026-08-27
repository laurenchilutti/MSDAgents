from pathlib import Path
from pydantic import BaseModel

import bs4


def _clean(text_to_clean: str|bs4.element.Tag) -> str:
    """
    Returns text inside tag and nested tags if text_to_clean is not None.
    Else, returns empty string.
    """
    if isinstance(text_to_clean, str):
        return text_to_clean.strip()
    elif isinstance(text_to_clean, bs4.element.Tag):
        return text_to_clean.get_text().strip() if text_to_clean is not None else ""
    else:
        return ""


class XMLsoup():

    """
    Returns a BeautifulSoup object for the given XML file.
    """

    @staticmethod
    def get_soup(xmldir: str|Path, xmlfile: str|Path):

        if xmlfile is None:
            raise IOError("xmlfile not specified")

        xmlfile = Path(xmldir)/Path(xmlfile)

        if xmlfile.exists():
            with open(xmlfile, "r") as openedfile:
                return bs4.BeautifulSoup(openedfile, "xml")
        else:
            raise FileNotFoundError(f"xml file '{xmlfile}' in directory '{xmldir}' does not exist")


class VariableData(BaseModel):

    """fields for module variables"""

    name: str
    type_: str
    description: str

class ProcedureData(BaseModel):

    """fields for subroutines and functions"""
    name: str
    type_: str
    arguments_list: list|str
    arguments_description: dict[str, VariableData]
    briefdescription: str
    detaileddescription: str
    inbodydescription: list|str


class ModuleVariableParser():

    def __init__(self):
        self.variables_dict = {}
    
    def get_module_variables(self, soup):

        """
        Documents module variables.  For example, parses

          module this module
            real(8) :: var1 !< is a variable
            integer :: var2 !< is another variable
          end module this module
        
        All variable descriptions are assumed to be less than ~400 tokens.
        """

        variablesoup = soup.doxygen.find("sectiondef", {"kind": "var"})
        if variablesoup is None:            
            print("No module variables")
            return

        variables = variablesoup.find_all("memberdef", {"kind": "variable"})

        if variables:
            for variable in variables:
                varname = _clean(variable.find("name"))
                self.variables_dict[varname] = VariableData(
                    name = varname, 
                    type_ = _clean(variable.type),
                    description = _clean(variable.briefdescription)
                )

        return self.variables_dict

    def get_direct_tag_to_string(self, tag, soup = None):

        """
        Returns the text of a direct child tag without descending into nested
        members that may contain same-named tags earlier in the document.
        """

        if soup is None:
            soup = self.soup

        tagobj = soup.find(tag, recursive=False)

        if tagobj is not None:
            tagstr = tagobj.text.strip()
            if tagstr:
                return tagstr

        return ""


class ProcedureParser():
    
    def __init__(self):
        self.procedures_dict = {}

    def get_module_procedures(self, soup):
    
        """
        Documents subroutines and functions.
        """
        functionsoup = soup.doxygen.find("sectiondef", {"kind": "func"})
        if functionsoup is None:
            return 

        procedures = functionsoup.find_all("memberdef", {"kind": "function"})
        
        if procedures:    
            for procedure in procedures:            
                procname = _clean(procedure.find("name"))  
                procedure_dict = ProcedureData(
                    name = procname,
                    type_ = _clean(procedure.find("type")),
                    arguments_list = _clean(procedure.argsstring).strip("()"),
                    arguments_description = self.get_arguments_description(procedure),
                    briefdescription = _clean(procedure.briefdescription),
                    detaileddescription = _clean(self.get_detaileddescription(procedure)),
                    inbodydescription = self.get_inbodydescription_list(procedure)
                )          
                self.procedures_dict[procname] = procedure_dict

        return self.procedures_dict

    def get_arguments_description(self, soup):

        """
        Returns the parameters for a subroutine
        <parameterlist>
            <parameteritem>
                <parameternamelist>
                    <parametername direction="in">time</parametername>
                </parameternamelist>
                <parameterdescription>
                    <para>is the current model time</para>
                </parameterdescription>
            </parameteritem>
        </parameterlist>
        """

        argument_dict = {}
        arguments = soup.find_all("parameteritem")

        if arguments:
            for argument in arguments:
                namelist = argument.parameternamelist
                name = namelist.text.strip()
                argument_dict[name] = VariableData(
                    name = name,
                    type_ = namelist.get("direction", "inout"),
                    description = _clean(argument.parameterdescription)
                )

        return argument_dict

    def get_detaileddescription(self, soup):

        """
        Parses
        <briefdescription>
            <para><parblock>Brief description.</parblock></para>
        </briefdescription>
        <detaileddescription>
            <para><parblock>Long description.</parblock></para>
        </detaileddescription>
        """
        try:
            return _clean(soup.detaileddescription.parblock)
        except Exception as e:
            return ""
        

    def get_inbodydescription_list(self, soup):
        
        """
        Parses
        <inbodydescription>
        <para><parblock><para>INITIALIZE MODULE-LEVEL VARIABLES. </para></parblock></para>
        <para><parblock><para>GET FILE UNIT FOR STDOUT AND STDLOG FOR INTERNAL LOGGING PURPOSES </para></parblock></para>
        </inbodydescription>
        """

        inbodydescription = []

        inbodydescription_obj = soup.find("inbodydescription")

        if inbodydescription_obj:
            for step in inbodydescription_obj.find_all("para"):
                if step.text.strip():
                    inbodydescription.append(f"{step.text.strip()}.")

        return inbodydescription

    
class TopLevelDocParser():

    def __init__(self):

        self.description_dict = {
            "brief": "",
            "detailed": ""
        }
    
    def get_description(self, soup):
        
        for child in soup.doxygen.compounddef.children:
            if child.name == "briefdescription":
                self.description_dict["brief"] = _clean(child)
            if child.name == "detaileddescription":
                self.description_dict["detailed"] = _clean(child)        

        return self.description_dict  
    

class FMSCouplerModuleDocument():

    def __init__(self, xmldir: str|Path, xmlfile: str|Path):

        self.xmlsoup = XMLsoup.get_soup(xmldir=xmldir, xmlfile=xmlfile)
        self.module_name = None
        self.overview = None
        self.variables = None
        self.procedures = None

        self.mdfile = []

    def populate(self):

        self.module_name = _clean(self.xmlsoup.doxygen.compoundname)
        self.overview = TopLevelDocParser().get_description(self.xmlsoup)
        self.variables = ModuleVariableParser().get_module_variables(self.xmlsoup)
        self.procedures = ProcedureParser().get_module_procedures(self.xmlsoup)

    def convert_to_markdown(self):

        self.mdfile.append(f"# Module: {self.module_name}\n")
                
        if self.overview:
            self.mdfile.append(f"{self.overview}\n")
            self.mdfile.append("\n")
        
        if self.variables:
            self.mdfile.append("## Module variables\n")
            self.mdfile.append("\n")
            for varname, varinfo in self.variables.items():
                vartype = varinfo.type_ if varinfo.type_ else "unknown"
                vardescript = varinfo.description
                if not vardescript:
                    vardescript = "No description"
                self.mdfile.append(f"### {varname}\n")
                self.mdfile.append(f"- name:  {varname}\n")
                self.mdfile.append(f"- type:  {vartype} variable\n")
                self.mdfile.append(f"- description:  {vardescript}\n")
                self.mdfile.append("\n")
        
        if self.procedures:
            self.mdfile.append(f"## Subroutines and functions\n")
            self.mdfile.append("\n")
            for procname, procinfo in self.procedures.items():
                proctype = procinfo.type_
                
                self.mdfile.append(f"### {proctype}: {procname}\n")
                self.mdfile.append(f"- name:  {procname}\n")
                self.mdfile.append(f"- type:  {proctype}\n")
                self.mdfile.append("\n")
                # description
                description = procinfo.detaileddescription if procinfo.detaileddescription else "No description"
                self.mdfile.append(f"- description:  {description}\n")
                self.mdfile.append("\n")
                # arguments
                if procinfo.arguments_list:
                    self.mdfile.append(f"- arguments:  {procinfo.arguments_list}.")
                if procinfo.arguments_description:
                    arguments = [f"{argname} ({arginfo.type_}) {arginfo.description}" for argname, arginfo in procinfo.arguments_description.items()]
                    self.mdfile.append(".  ".join(arguments))
                    self.mdfile.append("\n\n")
                inbodydescription = procinfo.inbodydescription
                if inbodydescription:
                    self.mdfile.append("- additional description:")
                    for step in inbodydescription:
                        self.mdfile.append(f"{step}")
                self.mdfile.append("\n\n")

    def write_markdown(self, output_dir: str|Path, output_file: str|Path = None, create_dir: bool = True):

        self.convert_to_markdown()

        output_file_ = f"{self.module_name}.md" if output_file is None else output_file

        if not Path(output_dir).is_dir():
            if create_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            else:
                raise RuntimeError(f"Directory {output_dir} does not exist")

        with open(Path(output_dir)/output_file_, "w", encoding="utf-8") as f:
            f.write("".join(self.mdfile))

        return output_file_


# needs to be updated
class InterfaceDocument(XMLsoup):

    def __init__(self,
                 xmldir: str|Path = "./docs/xml",
                 xmlfile: str|Path = None,
                 include_flowchart: bool = True):

        super().__init__(xmldir, xmlfile=xmlfile)
        self.include_flowchart = include_flowchart
        self.interface_name = self.toplevel_name
        name_parts = self.interface_name.split("::", 1)
        self.module_name = name_parts[0] if len(name_parts) == 2 else ""
        self.generic_name = name_parts[1] if len(name_parts) == 2 else self.interface_name
        self.mdfile = [f"# {self.interface_name}\n"]

    def document_interface(self):
        compounddef = self.soup.find("compounddef")
        briefdescription = self.get_direct_tag_to_string("briefdescription", compounddef)
        detaileddescription = self.get_direct_tag_to_string("detaileddescription", compounddef)

        if briefdescription and briefdescription[-1] != ".":
            briefdescription += "."
        if detaileddescription and detaileddescription[-1] != ".":
            detaileddescription += "."

        markdown = f"## interface {self.generic_name}\n"
        markdown += "### intro\n"
        if self.module_name:
            markdown += f"{self.generic_name} is a generic interface in {self.module_name}.\n"
        else:
            markdown += f"{self.generic_name} is a generic interface.\n"
        markdown += "### description\n"
        markdown += f"{briefdescription}  {detaileddescription}\n"

        procedures_obj = self.soup.find_all("memberdef", {"kind": "function"})
        if procedures_obj:
            markdown += "### implementations\n"
            for procedure in procedures_obj:
                procname = self.get_name(procedure)
                proctype = self.get_tag_to_string("type", procedure).split(",")[0].strip()
                parameters_description = self.get_parameters_description(procedure, subroutine_name=procname)
                proc_brief = self.get_tag_to_string("briefdescription", procedure)
                proc_detail = self.get_tag_to_string("detaileddescription", procedure)
                inbodydescription = self.get_inbodydescription(procedure) if self.include_flowchart else ""

                if proc_brief and proc_brief[-1] != ".":
                    proc_brief += "."
                if proc_detail and proc_detail[-1] != ".":
                    proc_detail += "."

                markdown += f"#### {procname}\n"
                markdown += f"{procname} is a {proctype} implementation of {self.generic_name}.\n"
                markdown += f"{proc_brief}  {proc_detail}\n"
                if parameters_description:
                    markdown += f"{parameters_description}\n"
                if self.include_flowchart and inbodydescription:
                    markdown += "##### flowchart\n"
                    markdown += f"{procname} does the following:  \n{inbodydescription}\n"

        self.mdfile.append(markdown)
        return markdown

    def write_markdown(self, output_dir: str|Path = "./"):
        interface_name = self.interface_name.replace("::", "__").replace("/", "_")
        output_file = f"{interface_name}.md"

        markdown_content = "\n".join(str(section) for section in self.mdfile)

        with open(Path(output_dir)/output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return output_file


if __name__ == "__main__":
    test()
