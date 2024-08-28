import os, sys, time
import node

base_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + os.sep + '..' + os.sep)
sys.path.append(base_dir + os.sep + "ext" + os.sep + "requests-2.2.0-16")
import requests

SYNCING_TIMEOUT = 20
SYNCHRONIZED_TIMEOUT = 240

class SYNC_STATE:
    """
    B{Enum defining node synchronization states}

    """

    UNSYNCHRONIZED = "UNSYNCHRONIZED"
    SYNCING = "SYNCING"
    SYNCHRONIZED = "SYNCHRONIZED"

def run_operation(node_obj, verbose_mode=False, delete_node_on_error=True):
    operation = node_obj.operation
    force_deletion = False

    print node_obj

    ### run the create operation ###
    if operation == node.OPERATION.CREATE or operation == node.OPERATION.POPULATE or operation == node.OPERATION.ALL:
        if not verbose_mode:
            print "  Running create operation...",

        mecontext_created = False
        cmd_counter = 0

        for node_cmd in node_obj.create_cmd_list:
            run_cmd(node_cmd, node_obj.url, verbose_mode=verbose_mode)
            _update_node_status(node_obj, node_cmd)

            if cmd_counter == 0 and node_cmd.result == node.RESULT.SUCCESS:
                mecontext_created = True
            elif node_cmd.result == node.RESULT.FAIL or node_cmd.result == node.RESULT.ERROR:
                if mecontext_created:
                    force_deletion = True
                break

            cmd_counter = cmd_counter + 1

        if not verbose_mode:
            print str(node_cmd.result)

    ### run the sync operation ###
    if node_obj.result == node.RESULT.SUCCESS and (operation == node.OPERATION.SYNC or operation == node.OPERATION.POPULATE or operation == node.OPERATION.ALL):
        if not verbose_mode:
            print "  Running sync operation...",

        for node_cmd in node_obj.sync_cmd_list:
            run_cmd(node_cmd, node_obj.url, verbose_mode=verbose_mode)
            _update_node_status(node_obj, node_cmd)

            if node_cmd.result == node.RESULT.FAIL or node_cmd.result == node.RESULT.ERROR:
                force_deletion = True
                break

        ### block until the synchronization has finished ###
        if not force_deletion:
            node_cmd = node_obj.sync_monitor_cmd
            _wait_for_sync_state_change(node_cmd, node_obj.url, SYNC_STATE.SYNCING, verbose_mode)
            if node_cmd.result == node.RESULT.FAIL or node_cmd.result == node.RESULT.ERROR:
                force_deletion = True

            if node_cmd.result == node.RESULT.SUCCESS:
                _wait_for_sync_state_change(node_cmd, node_obj.url, SYNC_STATE.SYNCHRONIZED, verbose_mode)
                if node_cmd.result == node.RESULT.FAIL or node_cmd.result == node.RESULT.ERROR:
                    force_deletion = True

        _update_node_status(node_obj, node_cmd)

        if not verbose_mode:
            print str(node_cmd.result)

    ### if we've been instructed not to delete nodes on error ###
    if not delete_node_on_error and force_deletion:
        force_deletion = False

    ### run the remove operation ###
    if force_deletion or operation == node.OPERATION.DELETE or operation == node.OPERATION.ALL:
        if not verbose_mode:
            print "  Running delete operation...",

        if force_deletion and verbose_mode:
            print "  Running delete command on MeContext sub-tree due to previous command failure"

        for node_cmd in node_obj.delete_cmd_list:
            run_cmd(node_cmd, node_obj.url, verbose_mode=verbose_mode)

            if node_cmd.result == node.RESULT.FAIL or node_cmd.result == node.RESULT.ERROR:
                break

        _update_node_status(node_obj, node_cmd)

        if not verbose_mode:
            print str(node_cmd.result)

def _update_node_status(node_obj, node_cmd):
    if node_cmd.result == node.RESULT.ERROR:
        node_obj.result = node.RESULT.ERROR
    elif node_cmd.result == node.RESULT.FAIL:
        node_obj.result = node.RESULT.FAIL

def _wait_for_sync_state_change(node_cmd, url, target_state, verbose_mode=False):
    start_time = time.time()
    elapsed_time = 0
    state_obtained = False

    if target_state == SYNC_STATE.SYNCING:
        timeout = SYNCING_TIMEOUT
    elif target_state == SYNC_STATE.SYNCHRONIZED:
        timeout = SYNCHRONIZED_TIMEOUT

    str_target_state = "'" + str(target_state) + "'"
    
    if verbose_mode:
        print "  Waiting for node synchronization state to transition to " + str(target_state) + "..."

    while elapsed_time < timeout:
        run_cmd(node_cmd, url, True, verbose_mode)
        output = node_cmd.cmd_output

        if node_cmd.result == node.RESULT.SUCCESS and str_target_state in str(output):
            if verbose_mode:
                print "  Node synchronization state has transitioned to " + str(target_state)

            state_obtained = True
            break
        else:
            if verbose_mode:
                if output is not None and len(output) > 0:
                    print "    Command output: " + str(output)
            time.sleep(3)

        elapsed_time = time.time() - start_time

    if not state_obtained:
        if verbose_mode:
            print "  Node synchronization timed out after " + str(timeout) + " seconds (never made it to " + str(target_state) + ")"
        node_cmd.error_msg_list.append("Node synchronization timed out after " + str(timeout) + " seconds")
        node_cmd.result = node.RESULT.ERROR
    else:
        node_cmd.result = node.RESULT.SUCCESS

    node_cmd.elapsed_time = "%.3f" % (time.time() - start_time)

def run_cmd(node_cmd, url, grab_output=False, verbose_mode=False):
    result = node.RESULT.ERROR
    expected_result = node_cmd.expected_result
    output = make_rest_call(node_cmd, url, verbose_mode)
    if grab_output:
        node_cmd.cmd_output = output

    if output is not None:
        try:
            status_code = int(output['statusCode'])
        except:
            node_cmd.error_msg_list.append("No statusCode attribute found in JSON response")
            node_cmd.error_msg_list.append("RESPONSE: " + output)
            status_code = node.STATUSCODE.UNEXPECTED_ERROR

        ### handle many affected MOs ###
        if status_code > node.STATUSCODE.MANY_AFFECTED:
            status_code = node.STATUSCODE.MANY_AFFECTED

        if status_code != expected_result:
            status_message = output['statusMessage']
            node_cmd.error_msg_list.append("Command '"+ node_cmd.cmd + "' did not produce expected status code '" + str(expected_result) + "'.")
            node_cmd.error_msg_list.append("Acutal status code is: '" + str(status_code) + "'.")
            node_cmd.error_msg_list.append("Status message is: '" + status_message + "'")
            result = node.RESULT.FAIL
        else:
            result = node.RESULT.SUCCESS

        if verbose_mode:
            print "    Status code: " + str(status_code)

            if status_code < 1 and len(node_cmd.error_msg_list) > 0:
                for error_msg in node_cmd.error_msg_list:
                    print "    ERROR MSG: " + error_msg

    if verbose_mode:
        print "    HTTP response code: " + str(node_cmd.http_response_code)
        print "    Elapsed time: " + node_cmd.elapsed_time + "ms"
        print "    Command result: " + str(result)

    node_cmd.result = result

def make_rest_call(node_cmd, url, verbose_mode=False):
    cmd = node_cmd.cmd
    data = {'command': cmd}
    result = None
    http_response_code = None

    node_cmd.elapsed_time = time.time()
    
    try:
        if verbose_mode:
            print "  Executing command '" + cmd + "'"

        r = requests.post(url, files = data, timeout = 10)
        http_response_code = r.status_code

        if r.status_code != 200:
            node_cmd.error_msg_list.append("REST request to '" + url + "' with command payload '" + cmd + "' returned HTTP error code "+ str(r.status_code) + ".")
            node_cmd.error_msg_list.append("Returned message is: " + r.text)
        else:
            result = r.json()
    except requests.exceptions.ConnectionError, e:
        node_cmd.error_msg_list.append("REST request to '" + url + "' with command payload  '" + cmd + "' returned a ConnectionError.")
        node_cmd.error_msg_list.append("Exception message is: " + str(e))
    except requests.exceptions.Timeout, e:
        node_cmd.error_msg_list.append("REST request to '" + url + "' with command payload  '" + cmd + "' timed out")
    finally:
        node_cmd.http_response_code = http_response_code

    node_cmd.elapsed_time = "%.3f" % (time.time() - node_cmd.elapsed_time)
    return result
