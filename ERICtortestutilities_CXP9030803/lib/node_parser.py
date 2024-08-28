import os, re
import xml.etree.ElementTree as et

def get_xml_files_in_dir_gen(directory):
    if os.path.exists(directory):
        for file in os.listdir(directory):
            if file.endswith(".xml"):
                yield os.path.realpath(directory + os.sep + file)

def get_xml_tree_from_file_gen(xml_files):
    for xml_file in xml_files:
        try:
            xml_tree = et.parse(xml_file)
            print "Parsing XML file " + xml_file + "..."
        except:
            raise RuntimeError("Unable to parse XML file " + xml_file)

        yield xml_tree

def get_all_mecontext_elements_from_xml_tree_gen(xml_trees):
    total_xml_files = 0
    total_nodes = 0
    for xml_tree in xml_trees:
        total_xml_files = total_xml_files + 1
        for mecontext_element in xml_tree.findall("./Create//ManagedElement").__iter__():
            total_nodes = total_nodes + 1
            yield mecontext_element

    print "\nProcessed " + str(total_nodes) + " node(s) from " + str(total_xml_files) + " XML file(s)"

def get_node_data_from_mecontext_elements_gen(mecontext_elements):
    find_regex = re.compile(r"^v(\w)\.")
    substitute_regex = re.compile(r"^\w{2}")

    duplicate_me_id_check_dict = {}
    duplicate_ip_addr_check_dict = {}

    ### build the column headers ##
    node_values = []
    node_values.append("managed_element_id")
    node_values.append("ip_address")
    node_values.append("mim_version")
    yield node_values

    ### build a line for each node ###
    for mecontext_element in mecontext_elements:
        node_values = []
        node_values.append(mecontext_element.find("ManagedElementId").get("string"))
        node_values.append(mecontext_element.find("Connectivity/DEFAULT/ipAddress").get("string"))
        mim_version = mecontext_element.find("neMIMVersion").get("string")

        if duplicate_me_id_check_dict.has_key(node_values[0]):
            raise RuntimeError("Duplicate managed element ID (" + node_values[0] + ") found")
        else:
            duplicate_me_id_check_dict[node_values[0]] = 0

        if duplicate_ip_addr_check_dict.has_key(node_values[1]):
            raise RuntimeError("Duplicate node IP address (" + node_values[1] + ") found")
        else:
            duplicate_ip_addr_check_dict[node_values[1]] = 0

        ### the MIM version needs to be converted ###
        match = find_regex.search(mim_version)
        if match:
            numeric_version = str(ord(match.group(1)) - 64)
            mim_version = re.sub(substitute_regex, numeric_version, mim_version)
            node_values.append(mim_version)
        else:
            raise RuntimeError("Could not parse MIM version\nMIM version: " + mim_version)

        yield node_values

def parse_xml_files(output_file, input_dir):
    if not os.path.isdir(input_dir):
        raise RuntimeError("Input directory " + str(input_dir) + " doesn't exist")

    ### get a generator of all nodes ###
    node_values = get_node_data_from_mecontext_elements_gen(get_all_mecontext_elements_from_xml_tree_gen(get_xml_tree_from_file_gen(get_xml_files_in_dir_gen(input_dir))))

    with open(output_file, "w") as file_handle:
        for node_values_list in node_values:
            file_handle.write(", ".join(node_values_list) + "\n")

    print "\nNode data written to " + output_file
