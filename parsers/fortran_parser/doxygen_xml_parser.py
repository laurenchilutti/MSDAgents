from pathlib import Path
from typing import Literal

from bs4 import BeautifulSoup

from langchain_core.documents import Document


def _clean(text_to_clean):
    """
    Returns text inside tag and nested tags if text_to_clean is not None.
    Else, returns empty string.
    """
    return text_to_clean.text.strip() if text_to_clean is not None else ""


class XMLsoup():

    """
    Returns a BeautifulSoup object for the given XML file.
    """

    @staticmethod
    def get_soup(xmldir: str|Path = "./", xmlfile: str|Path = None):

        if xmlfile is None:
            raise IOError("xmlfile not specified")

        xmlfile = Path(xmldir)/Path(xmlfile)

        if xmlfile.exists():
            with open(xmlfile, "r") as openedfile:
                return BeautifulSoup(openedfile, "lxml-xml")
        else:
            raise FileNotFoundError(f"xml file '{xmlfile}' in directory '{xmldir}' does not exist")


class ProcedureParser():
    
    def __init__(self):
        self.procedures_dict = {}

    def document_procedures(self, soup):
    
        """
        Documents subroutines and functions.
        """

        procedures_objs = soup.find_all("memberdef", {"kind": "function"})
        
        if procedures_objs:    
            for procedure_obj in procedures_objs:            
                procedure_dict = {}                
                # parses <name>atm_land_ice_flux_exchange_init</name>            
                procname = _clean(procedure_obj.find("name"))                        
                # parses <type>subroutine, public</type>            
                procedure_dict["type"] = _clean(procedure_obj.find("type"))                        
                # parses  <argsstring>(Time, Atm, Land, Ice, atmos</argsstring
                procedure_dict["argsstring"] = _clean(procedure_obj.argsstring).strip("()")               
                # parses brief and detailed descriptions
                procedure_dict["detaileddescription"] = self.get_detaileddescription(procedure_obj)
                # parses arguments
                procedure_dict["parameters"] = self.get_arguments_dict(procedure_obj)                
                # parses inbodydescription <inbodydescription><para>This is inside the code</para></inbodydescription>
                procedure_dict["inbodydescription"] = self.get_inbodydescription_list(procedure_obj)
                # save
                self.procedures_dict[procname] = procedure_dict

        return self.procedures_dict


    def get_arguments_dict(self, soup):

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

        parameters_dict = {}
        parameter_item_objs = soup.find_all("parameteritem")

        if parameter_item_objs:
            for parameter_item_obj in parameter_item_objs:
                parameter_namelist_obj = parameter_item_obj.parameternamelist
                name = parameter_namelist_obj.text.strip()
                parameters_dict[name] = {
                    "inout": parameter_namelist_obj.get("direction", "inout"), 
                    "description": _clean(parameter_item_obj.parameterdescription)
                }

        return parameters_dict

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
        briefdescription = _clean(soup.briefdescription)
        try:
            detaileddescription = _clean(soup.detaileddescription.parblock)
        except AttributeError:
            detaileddescription = ""

        return f"{briefdescription}  {detaileddescription}".strip()

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

        self.description = ""
    
    def get_description(self, soup):
        
        briefdescription = _clean(soup.briefdescription)
        detaileddescription = _clean(soup.detaileddescription)
        
        self.description = f"{briefdescription}  {detaileddescription}".strip()

        return self.description
    

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

        variables_objs = soup.find_all("memberdef", {"kind": "variable"})

        if variables_objs:
            for variable_obj in variables_objs:
                varname = _clean(variable_obj.find("name"))
                self.variables_dict[varname] = {
                    "type": _clean(variable_obj.type),
                    "briefdescription": _clean(variable_obj.briefdescription)
                }

        return self.variables_dict


class FMSCouplerModuleDocument():

    def __init__(self,
                 xmldir: str|Path = "./docs/xml",
                 xmlfile: str|Path = None):

        self.xmlsoup = XMLsoup.get_soup(xmldir=xmldir, xmlfile=xmlfile)
        self.module_name = _clean(self.xmlsoup.find("compoundname"))
        self.overview = TopLevelDocParser().get_description(self.xmlsoup)
        self.variables = ModuleVariableParser().get_module_variables(self.xmlsoup)
        self.procedures = ProcedureParser().document_procedures(self.xmlsoup)

        self.mdfile = []

    def convert_to_markdown(self):

        self.mdfile.append(f"# Module: {self.module_name}\n")
                
        if self.overview:
            self.mdfile.append(f"{self.overview}\n")
            self.mdfile.append("\n")
        
        if self.variables:
            self.mdfile.append("## Module variables\n")
            self.mdfile.append("\n")
            for varname, varinfo in self.variables.items():
                vartype = varinfo["type"] if varinfo["type"] else "unknown"
                vardescript = varinfo["briefdescription"] 
                if not vardescript:
                    vardescript = "No description"
                self.mdfile.append(f"### {varname}\n")
                self.mdfile.append(f"- type:  {vartype}\n")
                self.mdfile.append(f"- description:  {vardescript}\n")
                self.mdfile.append("\n")
        
        if self.procedures:
            self.mdfile.append(f"## Subroutines and functions\n")
            self.mdfile.append("\n")
            for procname, procinfo in self.procedures.items():
                proctype = procinfo["type"]
                self.mdfile.append(f"### {proctype}: {procname}\n")
                # description
                description = procinfo["detaileddescription"] if procinfo["detaileddescription"] else "No description"
                self.mdfile.append(f"- description:  {description}\n")
                self.mdfile.append("\n")
                # arguments
                if procinfo["argsstring"]:
                    self.mdfile.append(f"- arguments:  {procinfo['argsstring']}.")
                if procinfo["parameters"]:
                    arguments = [f"{argname} ({arginfo['inout']}) {arginfo['description']}" for argname, arginfo in procinfo["parameters"].items()]
                    self.mdfile.append(".  ".join(arguments))
                    self.mdfile.append("\n\n")
                inbodydescription = procinfo["inbodydescription"]
                if inbodydescription:
                    self.mdfile.append("- additional description:")
                    for step in inbodydescription:
                        self.mdfile.append(f"{step}")
                self.mdfile.append("\n\n")

    def write_markdown(self, output_dir: str|Path = "./"):

        self.convert_to_markdown()

        output_file = f"{self.module_name}.md"        
        with open(Path(output_dir)/output_file, "w", encoding="utf-8") as f:
            f.write("".join(self.mdfile))

        return output_file


def test():               
    xmldir = "/home/Mikyung.Lee/chatbot/coupler-chatbot/fmscoupler/fmscoupler/docs/xml" 
    xmlfile = "group__atm__land__ice__flux__exchange__mod.xml"
    modxml = FMSCouplerModuleDocument(xmldir=xmldir, xmlfile=xmlfile)
    modxml.convert_to_markdown()

if __name__ == "__main__":
    test()
