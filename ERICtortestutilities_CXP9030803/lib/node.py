class STATUSCODE:
    """
    B{Enum defining operation result statuses based on the JSON response}

    """
    
    MANY_AFFECTED = 2
    ONE_AFFECTED = 1
    ZERO_AFFECTED = 0
    EXPECTED_ERROR = -1
    UNEXPECTED_ERROR = -2
    PARSER_ERROR = -3

class RESULT:
    """
    B{Enum defining operation result types}

    """
    
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
            
class COMMAND_TYPE:
    """
    B{Enum defining command types that can be performed on a node}

    """

    CREATE = "CREATE"
    SYNC = "SYNC"
    DELETE = "DELETE"

class OPERATION:
    """
    B{Enum defining overall operation to run}

    """

    POPULATE = "POPULATE"
    CREATE = "CREATE"
    SYNC = "SYNC"
    DELETE = "DELETE"
    ALL = "ALL"

class Node:
    class NodeCommand:
        """
        B{NodeCommand constructor}

        @type cmd: string
        @param cmd: The fully populated cmedit command to be run
        @type cmd_type: COMMAND_TYPE
        @param cmd_type: The type of command
        @type cmd_desc: string
        @param cmd_desc: A text description of the command
        @type expected_result: STATUSCODE
        @param expected_result: The expected number of MO elements to be affected when the command is run
        @rtype: NodeCommand instance
        """
        def __init__(self, cmd, cmd_type, cmd_desc, expected_result):
            self.cmd = cmd
            self.cmd_type = cmd_type
            self.cmd_desc = cmd_desc

            self.expected_result = expected_result
            self.cmd_output = None
            self.result = RESULT.SUCCESS
            self.elapsed_time = 0
            self.error_msg_list = []
            self.http_response_code = None

        def __str__(self):
            return "CMD DESCRIPTION: " + self.cmd_desc + "\nCMD: " + self.cmd + "\nEXPECTED AFFECTED NODES: " + str(self.expected_result)

    ### TODO: consts that will be externalized to TorUtilities properties ###
    CREATE_MECONTEXT_CMD = "cmedit create MeContext=<node_id> MeContextId=<node_id>, neType=<netype> -namespace=<namespace> -version=<version>"
    CREATE_MANAGED_ELEMENT_CMD = "cmedit create MeContext=<node_id>, ManagedElement=<node_id> ManagedElementId=<node_id> -namespace=<namespace> -version=<version>"
    CREATE_ENODEB_CMD = "cmedit create MeContext=<node_id>, ManagedElement=<node_id>, ENodeBFunction=ENodeBFunction ENodeBFunctionId=ENodeBFunction -namespace=<namespace> -version=<version>"
    CREATE_CONNECTIVITY_INFO_CMD = """cmedit create MeContext=<node_id>, ManagedElement=<node_id>, ENodeBFunction=ENodeBFunction, ERBSConnectivityInfo=ERBSConnectivityInfo ConnectivityInfoId=ERBSConnectivityInfo, ipAddress="<ip_address>" -namespace=<namespace> -version=<version>"""
    SET_MIM_INFO_CMD = """cmedit set MeContext=<node_id>,ManagedElement=<node_id> mimInfo=(mimVersion="<mim_version>", mimRelease="", mimName="")"""
    SYNC_CMD = "cmedit action MeContext=<node_id> synchronise"
    SYNC_MONITOR_CMD = "cmedit get * MeContext.(MeContextId==<node_id>,mirrorSynchronizationStatus)"
    DELETE_NODE_TREE_CMD = "cmedit delete MeContext=<node_id> -ALL"

    MECONTEXT_NE_TYPE = "ENODEB"
    MECONTEXT_NAMESPACE = "OSS_TOP"
    MECONTEXT_VERSION = "1.1.0"

    MANAGED_ELEMENT_NAMESPACE = "CPP_NODE_MODEL"
    MANAGED_ELEMENT_VERSION = "3.12.0"

    ENODEB_NAMESPACE = "ERBS_NODE_MODEL"
    ENODEB_VERSION = "3.1.72"
    
    CONNECTIVITY_INFO_NAMESPACE = "ERBS_NODE_MODEL"
    CONNECTIVITY_INFO_VERSION = "1.0.0"


    """
    B{Node Constructor}

    @type url: string
    @param url: The full URL of the REST endpoint to run against
    @type node_id: string
    @param node_id: Node ID (unique across all nodes)
    @type node_ip: string
    @param node_ip: IP address of the node (unique across all nodes)
    @type mim_version: string
    @param mim_version: The node MIM version (in the format x.y.zzz)
    @rtype: Node instance
    """
    def __init__(self, url, node_id, node_ip, mim_version):
        self.url = url
        self.node_id = node_id
        self.node_ip = node_ip
        self.mim_version = mim_version
        self.operation = None

        self.elapsed_time = 0
        self.create_cmd_list = []
        self.sync_cmd_list = []
        self.delete_cmd_list = []
        self.sync_monitor_cmd = None
        self.result = RESULT.SUCCESS

        self.add_commands()

    def __str__(self):
        return "\nNode ID " + self.node_id + " (" + self.node_ip + ") [MIM version " + self.mim_version + "]"

    """
    B{Adds all of the commands for this node}

    @rtype: void
    """
    def add_commands(self):
        self._add_create_mecontext_cmd()
        self._add_create_managed_element_cmd()
        self._add_create_enodeb_cmd()
        self._add_create_connectivity_info_cmd()
        self._add_set_mim_info_cmd()
        self._add_sync_cmd()
        self._add_sync_monitor_cmd()
        self._add_delete_node_tree_cmd()

    def _add_create_mecontext_cmd(self):
        cmd = Node.CREATE_MECONTEXT_CMD
        cmd = cmd.replace("<node_id>", self.node_id).replace("<netype>", Node.MECONTEXT_NE_TYPE)
        cmd = cmd.replace("<namespace>", Node.MECONTEXT_NAMESPACE).replace("<version>", Node.MECONTEXT_VERSION)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.CREATE, "CREATE_MECONTEXT", STATUSCODE.ONE_AFFECTED)
        self.create_cmd_list.append(cmd_obj)

    def _add_create_managed_element_cmd(self):
        cmd = Node.CREATE_MANAGED_ELEMENT_CMD
        cmd = cmd.replace("<node_id>", self.node_id)
        cmd = cmd.replace("<namespace>", Node.MANAGED_ELEMENT_NAMESPACE).replace("<version>", Node.MANAGED_ELEMENT_VERSION)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.CREATE, "CREATE_MANAGED_ELEMENT", STATUSCODE.ONE_AFFECTED)
        self.create_cmd_list.append(cmd_obj)

    def _add_create_enodeb_cmd(self):
        cmd = Node.CREATE_ENODEB_CMD
        cmd = cmd.replace("<node_id>", self.node_id)
        cmd = cmd.replace("<namespace>", Node.ENODEB_NAMESPACE).replace("<version>", Node.ENODEB_VERSION)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.CREATE, "CREATE_ENODEB_FUNCTION", STATUSCODE.ONE_AFFECTED)
        self.create_cmd_list.append(cmd_obj)

    def _add_create_connectivity_info_cmd(self):
        cmd = Node.CREATE_CONNECTIVITY_INFO_CMD
        cmd = cmd.replace("<node_id>", self.node_id).replace("<ip_address>", self.node_ip)
        cmd = cmd.replace("<namespace>", Node.CONNECTIVITY_INFO_NAMESPACE).replace("<version>", Node.CONNECTIVITY_INFO_VERSION)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.CREATE, "CREATE_CONNECTIVITY_INFO", STATUSCODE.ONE_AFFECTED)
        self.create_cmd_list.append(cmd_obj)

    def _add_set_mim_info_cmd(self):
        cmd = Node.SET_MIM_INFO_CMD
        cmd = cmd.replace("<node_id>", self.node_id).replace("<mim_version>", self.mim_version)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.CREATE, "SET_MIM_VERSION", STATUSCODE.ONE_AFFECTED)
        self.create_cmd_list.append(cmd_obj)

    def _add_sync_cmd(self):
        cmd = Node.SYNC_CMD
        cmd = cmd.replace("<node_id>", self.node_id)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.SYNC, "SYNC_NODE", STATUSCODE.ONE_AFFECTED)
        self.sync_cmd_list.append(cmd_obj)

    def _add_sync_monitor_cmd(self):
        cmd = Node.SYNC_MONITOR_CMD.replace("<node_id>", self.node_id)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.SYNC, "SYNC_MONITOR_CMD", STATUSCODE.ONE_AFFECTED)
        self.sync_monitor_cmd = cmd_obj

    def _add_delete_node_tree_cmd(self):
        cmd = Node.DELETE_NODE_TREE_CMD.replace("<node_id>", self.node_id)
        cmd_obj = Node.NodeCommand(cmd, COMMAND_TYPE.DELETE, "DELETE_NODE_TREE", STATUSCODE.MANY_AFFECTED)
        self.delete_cmd_list.append(cmd_obj)

