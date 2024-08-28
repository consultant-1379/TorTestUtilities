#!/usr/bin/python
import os, sys

base_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + os.sep + '..' + os.sep)
sys.path.append(base_dir + os.sep + "lib")

import node, node_parser, executor

supported_operations = ("parse", "create", "sync", "delete", "populate")

def print_help():
    print "\nUSAGE"
    print "-----"
    print "node_populator.py <operation> <identifier> (<input_dir>||<range>) <verbose>"
    print "  <operation>       One of: 'parse', 'create', 'sync', 'delete' or 'populate'"
    print "                      NOTE: populate = create + sync"
    print "  <identifier>      Unique identifier for set of nodes being actioned"
    print "  <input_dir>       Path to the directory of ARNE XML file(s) to be processed"
    print "                      NOTE: Only valid for parse operation"
    print "  <range>           Perform the operation on the subset of nodes in the specified range"
    print "                      NOTE: format is x-y inclusive, or just x for 1 node"
    print "                      NOTE: Optional argument; valid for all operations other than parse"
    print "  <verbose>         Turns on verbose output"
    print "                      NOTE: Optional argument"
    print "\nEXAMPLES"
    print "--------"
    print "node_populator.py parse james /var/tmp/arne-xmls"
    print "     Parse all of the .xml files in /var/tmp/arne-xmls and create a node output file james"
    print "node_populator.py populate james"
    print "     Create base MO structure and then synchronize each node in node output file james"
    print "node_populator.py create james verbose"
    print "     Create base MO structure for each node in node output file james"
    print "node_populator.py create james 1-10"
    print "     Create base MO structure for the first ten nodes in node output file james"
    print "node_populator.py sync james"
    print "     Synchronize each node in node output file james"
    print "node_populator.py sync james 1-10 verbose"
    print "     Synchronize the first ten nodes in node output file james"
    print "node_populator.py delete james"
    print "     Delete the MeContext MO sub-tree for all nodes in node output file james"
    print "node_populator.py delete james 2"
    print "     Delete the MeContext MO sub-tree for the second node in node output file james"

if __name__=="__main__":
    ### check for help request ###
    if "help" in sys.argv[1] or "-h" in sys.argv[1]:
        print_help()
        sys.exit(0)

    ### make sure we got at least 2 arguments ###
    if len(sys.argv) < 3:
        print "\nERROR: A minimum of two arguments required"
        print_help()
        sys.exit(2)

    operation = sys.argv[1].lower()
    identifier = sys.argv[2].lower()
    input_dir = None
    node_range = None
    range_start = None
    range_end = None
    verbose_mode = False

    ### if we got any additional arguments, figure out what they are ###
    if len(sys.argv) > 3:
        if "verbose" in sys.argv[3].lower():
            verbose_mode = True
        elif operation == "parse":
            input_dir = sys.argv[3]
        else:
            node_range = sys.argv[3]

    if len(sys.argv) > 4 and "verbose" in sys.argv[4].lower():
        verbose_mode = True

    ### validate arguments ###
    if operation not in supported_operations:
        print "\nERROR: Unknown/invalid operation (" + operation + ")"
        print_help()
        sys.exit(2)
        
    if operation == "parse" and input_dir is None:
        print "\nERROR: Parse operation requires third argument (XML input directory)"
        print_help()
        sys.exit(2)

    if input_dir is not None and not os.path.isdir(input_dir):
        print "\nERROR: Specified XML input directory (" + input_dir + ") doesn't exist"
        print_help()
        sys.exit(2)

    if node_range is not None:
        validation_fail = False

        if "-" in node_range:
            range_bounds = node_range.split("-")
            if len(range_bounds) != 2:
                validation_fail = True

            try:
                range_start = int(range_bounds[0])
                range_end = int(range_bounds[1])
            except:
                validation_fail = True

            if range_start > range_end:
                validation_fail = True
        else:
            try:
                range_start = int(node_range)
                range_end = int(node_range)
            except:
                validation_fail = True

        if validation_fail:
            print "\nERROR: Improperly formatted node range (" + node_range + ")"
            print_help()
            sys.exit(2)

    ### make sure that the results dir exists ###
    results_dir = base_dir + os.sep + "results"
    if not os.path.isdir(results_dir):
        print "\nERROR: Directory " + results_dir + " does not exist, but is required for this tool"
        sys.exit(2)

    result_file = results_dir + os.sep + identifier + ".nodes"

    ### perform the requested operation ###
    try:
        if operation == "parse":
            node_parser.parse_xml_files(result_file, input_dir)
        elif operation == "create":
            executor.run_ops(identifier, node.OPERATION.CREATE, range_start, range_end, verbose_mode)
        elif operation == "sync":
            executor.run_ops(identifier, node.OPERATION.SYNC, range_start, range_end, verbose_mode)
        elif operation == "populate":
            executor.run_ops(identifier, node.OPERATION.POPULATE, range_start, range_end, verbose_mode)
        elif operation == "delete":
            executor.run_ops(identifier, node.OPERATION.DELETE, range_start, range_end, verbose_mode)
    except Exception, e:
        print "\nERROR: " + e.args[0]
        sys.exit(1)
