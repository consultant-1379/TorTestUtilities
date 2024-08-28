import os
import node, worker

base_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + os.sep + '..' + os.sep)

URL = "http://atmws40-6.athtem.eei.ericsson.se:8080/script-engine/services/commandRequest"
DELETE_NODE_ON_ERROR = False

def get_lines_from_file_gen(data_file):
    if not os.path.exists(data_file):
        raise RuntimeError("Could not find specified input file " + data_file)

    with open(data_file, "r") as file_handle:
        next(file_handle)
        for line in file_handle:
            yield line.strip()

def get_nodes_from_data_lines(lines, verbose_mode):
    url = URL

    if verbose_mode:
        print "REST endpoint: " + url

    for line in lines:
        values = line.split(",")
        if len(values) >= 3:
            node_obj = node.Node(url, values[0].strip(), values[1].strip(), values[2].strip())
            yield node_obj

def run_ops(identifier, operation, range_start=None, range_end=None, verbose_mode=False, delete_node_on_error=True):
    input_file = base_dir + os.sep + "results" + os.sep + identifier + ".nodes"
    
    node_counter = 0
    for node_obj in get_nodes_from_data_lines(get_lines_from_file_gen(input_file), verbose_mode):
        node_counter = node_counter + 1

        if range_start is not None and range_end is not None:
            if node_counter < range_start:
                continue
            elif node_counter > range_end:
                break

        node_obj.operation = operation
        worker.run_operation(node_obj, verbose_mode, DELETE_NODE_ON_ERROR)
