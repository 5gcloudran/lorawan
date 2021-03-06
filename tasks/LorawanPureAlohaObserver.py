import parameters.Constants as Constants
import util.LorawanUtil as LorawanUtil
import util.ProcessUtil as ProcessUtil
import random
import json
from models.PureAlohaCommunicationState import PureAlohaCommunicationState
from models.LorawanResults import LorawanResults

import util.LogUtil as LogUtil


observation_time = 0
observation_start_time = 0
succeeded_communications = []
failed_communications = []
banned_devices = []
failed_devices = []
out_of_simulation_devices = []
failed_end_device_id_to_active_transmission_time = {}

recursion_count = 0


def start(lorawan_groups):
    global observation_time
    global succeeded_communications
    global banned_devices
    global failed_devices
    global out_of_simulation_devices
    global observation_start_time
    global failed_communications
    global failed_end_device_id_to_active_transmission_time
    global recursion_count

    observation = True
    observation_time = Constants.SIMULATION_LIFE_TIME_IN_SECONDS
    counter = 0
    previous_observation_time = 0

    while observation:
        if previous_observation_time == observation_time:
            counter += 1
        else:
            counter = 0
        previous_observation_time = observation_time
        lorawan_groups = __communicate(lorawan_groups)
        if counter == 50:
            observation = False

    lorawan_results = LorawanResults([ed for com in succeeded_communications for ed in com.end_devices], failed_devices, banned_devices, out_of_simulation_devices)

    result_object = {}
    sf_succ_object = {}
    sf_fail_object = {}
    sf_ban_object = {}

    result_object['SuccXmt'] = str(len(lorawan_results.succeeded_t))
    result_object['FailXmt'] = str(len(lorawan_results.out_of_simulation_t) + len(lorawan_results.failed_t))
    result_object['BanXmt'] = str(len(lorawan_results.banned_t))
    result_object['ULMsgCnt'] = str(sum([ed.retransmission_attempt_count+1 for ed in lorawan_results.succeeded_t] +
                            [ed.retransmission_attempt_count for ed in lorawan_results.banned_t] +
                            [ed.retransmission_attempt_count for ed in lorawan_results.failed_t] +
                            [ed.retransmission_attempt_count for ed in lorawan_results.out_of_simulation_t]))
    result_object['DLAckCnt'] = str(len(lorawan_results.succeeded_t))
    result_object['ULMsgSz'] =  str(sum([(ed.retransmission_attempt_count + 1)*(13+Constants.SF_TO_MAC_PAYLOAD_IN_BYTE[getattr(ed, "_sf")]) for ed in lorawan_results.succeeded_t] +
                            [(ed.retransmission_attempt_count)*(13+Constants.SF_TO_MAC_PAYLOAD_IN_BYTE[getattr(ed, "_sf")]) for ed in lorawan_results.banned_t] +
                            [(ed.retransmission_attempt_count)*(13+Constants.SF_TO_MAC_PAYLOAD_IN_BYTE[getattr(ed, "_sf")]) for ed in lorawan_results.failed_t] +
                            [(ed.retransmission_attempt_count)*(13+Constants.SF_TO_MAC_PAYLOAD_IN_BYTE[getattr(ed, "_sf")]) for ed in lorawan_results.out_of_simulation_t]))
    result_object['DLAckSz'] = str(13*len(lorawan_results.succeeded_t))

    for sf in range(7, 13):
        sf_succ_object[sf] = len([ed for ed in lorawan_results.succeeded_t if int(getattr(ed, "_sf")) == sf])
        sf_fail_object[sf] = len([ed for ed in lorawan_results.out_of_simulation_t if int(getattr(ed, "_sf")) == sf]) + len([ed for ed in lorawan_results.failed_t if int(getattr(ed, "_sf")) == sf])
        sf_ban_object[sf] = len([ed for ed in lorawan_results.banned_t if int(getattr(ed, "_sf")) == sf])

    result_object['SfSuccXmt'] = str(sf_succ_object)
    result_object['SfFailXmt'] = str(sf_fail_object)
    result_object['SfBanXmt'] = str(sf_ban_object)

    _r_json = json.dumps(result_object)

    with open(Constants.LOG_FILE_DIR + "/LorawanPureAloha", 'a') as the_file:
        the_file.write(_r_json)

    observation_time = 0
    observation_start_time = 0
    succeeded_communications = []
    failed_communications = []
    banned_devices = []
    failed_devices = []
    out_of_simulation_devices = []
    failed_end_device_id_to_active_transmission_time = {}
    recursion_count = 0


def __communicate(lorawan_groups):
    global observation_start_time
    global observation_time
    global succeeded_communications
    global failed_communications
    global banned_devices
    global failed_devices
    global failed_end_device_id_to_active_transmission_time

    if observation_time <= 0:
        return {}

    communication_history = []

    for sf in lorawan_groups:
        toa = __get_time_on_air(sf)
        devices_of_sf = lorawan_groups.get(sf)
        if observation_time < toa:
            failed_devices += devices_of_sf
            continue
        sf_time_usage = __monitor_resource_usages(devices_of_sf)
        sf_com_stt = [PureAlohaCommunicationState(sf, toa, time, observation_start_time, sf_time_usage.get(time))
                                  for time in sf_time_usage]
        sf_com_stt.sort(key=lambda communication_status: communication_status.transmission_time,
                               reverse=False)
        __collision_detection_for_transmitters(sf_com_stt)
        communication_history += sf_com_stt

    communication_history.sort(key=lambda communication_status: communication_status.first_receive_window_time,
                               reverse=False)

    failed_communications = []
    failed_end_device_id_to_active_transmission_time = {}

    if communication_history == []:
        return {}

    status_ok_transmissions = __tag_communication_state(communication_history)
    succeeded_communications += status_ok_transmissions

    total_communications_num = len(status_ok_transmissions) + len(failed_communications)

    if total_communications_num == len(communication_history):
        if len(status_ok_transmissions) == len(communication_history):
            lorawan_groups = {}
        else:
            communication_state = communication_history[total_communications_num - 1]

            observation_start_time = communication_state.transmission_time
            observation_time = Constants.SIMULATION_LIFE_TIME_IN_SECONDS - observation_start_time

            lorawan_groups = __create_lorawan_groups(communication_history[total_communications_num:])
    elif 0 < total_communications_num < len(communication_history):
        communication_state = communication_history[total_communications_num]

        observation_start_time = communication_state.transmission_time
        observation_time = Constants.SIMULATION_LIFE_TIME_IN_SECONDS - observation_start_time

        lorawan_groups = __create_lorawan_groups(communication_history[total_communications_num:])

    elif 0 == total_communications_num:
        lorawan_groups = {}

    return lorawan_groups


def __create_lorawan_groups(communication_history):
    global failed_communications
    global banned_devices
    global out_of_simulation_devices
    global failed_end_device_id_to_active_transmission_time

    lorawan_groups = {}

    for failed_communication in failed_communications:
        will_be_active_transmission_time = failed_communication.will_be_active_transmission_time
        sf = failed_communication.sf
        end_devices = failed_communication.end_devices

        if will_be_active_transmission_time >= Constants.SIMULATION_LIFE_TIME_IN_SECONDS:
            out_of_simulation_devices += failed_communication.end_devices
            continue

        for end_device in end_devices:
            end_device.increment_retransmission_attempt_count()
            if end_device.is_banned():
                banned_devices.append(end_device)
            else:
                failed_end_device_id_to_active_transmission_time[getattr(end_device, "_id")] = \
                    failed_communication.will_be_active_transmission_time
                if lorawan_groups.get(sf) is None:
                    lorawan_groups[sf] = [end_device]
                else:
                    lorawan_groups[sf].append(end_device)

    for communication_state in communication_history:
        sf = communication_state.sf

        if lorawan_groups.get(sf) is None:
            lorawan_groups[sf] = communication_state.end_devices
        else:
            lorawan_groups[sf] += communication_state.end_devices

    return lorawan_groups


def __monitor_resource_usages(lorawan_sf_devices):
    transmission_times = __find_transmission_times(lorawan_sf_devices)
    active_transmitters = __find_active_transmitters(lorawan_sf_devices)
    resource_usage = __compose_resource_usages(transmission_times, active_transmitters)
    return resource_usage


def __find_transmission_times(lorawan_sf_devices):
    global observation_time

    transmission_times = []
    lorawan_sf_devices_count = len(lorawan_sf_devices)
    active_transmitters_count = lorawan_sf_devices_count
    for i in range(0, active_transmitters_count):
        transmission_times.append(float(random.uniform(0.0, float(observation_time))))
    return transmission_times


def __find_active_transmitters(lorawan_sf_devices):
    lorawan_sf_devices_count = len(lorawan_sf_devices)
    active_transmitters_amount = lorawan_sf_devices_count
    active_transmitters_indexes = \
        __select_active_transmitters_index(active_transmitters_amount, lorawan_sf_devices_count)
    active_transmitters = []
    for index in active_transmitters_indexes:
        active_transmitters.append(lorawan_sf_devices.pop(index))

    return active_transmitters


def __select_active_transmitters_index(active_transmitters_amount, lorawan_sf_devices_count):
    _random = random.Random()
    seed = _random.randint(1, 30000)
    _random.seed(seed)
    indexes = _random.sample(range(0, lorawan_sf_devices_count), active_transmitters_amount)
    indexes.sort(reverse=True)
    return indexes


def __compose_resource_usages(transmission_times, active_transmitters):
    global observation_start_time
    global observation_time
    global failed_end_device_id_to_active_transmission_time

    resource_usages = {}
    for index in range(0, len(transmission_times)):
        end_device = active_transmitters[index]
        end_device_id = getattr(end_device, "_id")
        if failed_end_device_id_to_active_transmission_time.get(end_device_id) is not None:
            active_transmission_t = failed_end_device_id_to_active_transmission_time[end_device_id]
            given_time = observation_start_time + transmission_times[index]
            if active_transmission_t > given_time:
                valid_start_time = active_transmission_t - observation_start_time
                if valid_start_time > observation_time:
                    transmission_times[index] = observation_time
                else:
                    transmission_times[index] = random.uniform(valid_start_time, observation_time)
        if resource_usages.get(transmission_times[index]) is None:
            resource_usages[transmission_times[index]] = [end_device]
        else:
            resource_usages[transmission_times[index]].append(end_device)
    return resource_usages


def __collision_detection_for_transmitters(com_list):

    for index in range(1, len(com_list)):
        eott = com_list[index - 1].end_of_transmission_time
        tt = com_list[index].transmission_time

        if eott >= tt:
            com_list[index - 1].is_collision = True
            com_list[index].is_collision = True


def __tag_communication_state(communication_history):
    gateway_active_timestamp = 0
    gateway_passive_timestamp = 0

    gateway_transmission_start_time = 0
    gateway_transmission_end_time = 0

    global failed_communications

    failed_communications = []

    ok = []

    first_failed_transmission_detector = False
    succeeded_transmission_after_first_failure = False

    for communication_status in communication_history:
        if communication_status.is_collision is True:
            if first_failed_transmission_detector is not True:
                first_failed_transmission_detector = True
            failed_communications.append(communication_status)

        else:
            # Communication channel is bidirectional so if there is an UL channel between gw and ed,
            # DL channel should not be connected between them or vice versa.
            if __channel_transmission_state(gateway_transmission_start_time,
                                            gateway_transmission_end_time,
                                            communication_status.transmission_time) \
                    == "DL_ACTIVE_UL_CONTROL_NEEDLESS":
                if first_failed_transmission_detector is not True:
                    first_failed_transmission_detector = True
                failed_communications.append(communication_status)

            elif __channel_transmission_state(gateway_transmission_start_time,
                                              gateway_transmission_end_time,
                                              communication_status.transmission_time) \
                    == "DL_WILL_BE_ACTIVE_UL_CONTROL_NEEDED":
                if communication_status.end_of_transmission_time >= gateway_transmission_start_time:
                    if first_failed_transmission_detector is not True:
                        first_failed_transmission_detector = True
                    failed_communications.append(communication_status)
                else:
                    if gateway_transmission_start_time <= communication_status.first_receive_window_time <= gateway_transmission_end_time:
                        receiving_message_end_time = communication_status.first_receive_window_time + communication_status.receiving_message_toa
                        if receiving_message_end_time > gateway_transmission_end_time:
                            gateway_transmission_end_time = receiving_message_end_time

                            gateway_transmission_duration_time = gateway_transmission_end_time - gateway_transmission_start_time

                            gateway_passive_timestamp = gateway_transmission_end_time
                            gateway_active_timestamp = gateway_transmission_start_time + \
                                                       (gateway_transmission_duration_time * float(
                                                           100 / Constants.DUTY_CYCLE_IN_PERCENTAGE))
                        if first_failed_transmission_detector is True:
                            succeeded_transmission_after_first_failure = True
                        if succeeded_transmission_after_first_failure is not True:
                            ok.append(communication_status)
                    else:
                        if first_failed_transmission_detector is not True:
                            first_failed_transmission_detector = True
                        failed_communications.append(communication_status)

            elif __channel_transmission_state(gateway_transmission_start_time,
                                              gateway_transmission_end_time,
                                              communication_status.transmission_time) \
                    == "DL_PASSIVE_DL_DUTY_CYCLE_CONTROL_NEEDED":
                if gateway_passive_timestamp < communication_status.second_receive_window_time < gateway_active_timestamp:
                    if first_failed_transmission_detector is not True:
                        first_failed_transmission_detector = True
                    failed_communications.append(communication_status)
                else:
                    if communication_status.first_receive_window_time > gateway_active_timestamp:
                        gateway_transmission_start_time = communication_status.first_receive_window_time
                    else:
                        gateway_transmission_start_time = communication_status.second_receive_window_time

                    gateway_transmission_end_time = gateway_transmission_start_time + communication_status.receiving_message_toa

                    gateway_passive_timestamp = gateway_transmission_end_time
                    gateway_active_timestamp = gateway_transmission_start_time + \
                                               (communication_status.receiving_message_toa * float(
                                                   100 / Constants.DUTY_CYCLE_IN_PERCENTAGE))
                    if first_failed_transmission_detector is True:
                        succeeded_transmission_after_first_failure = True
                    if succeeded_transmission_after_first_failure is not True:
                        ok.append(communication_status)

        if succeeded_transmission_after_first_failure is True:
            break

    return ok


def __channel_transmission_state(gw_tstart_t, gw_tend_t, ed_tstart_t):

    if gw_tstart_t <= ed_tstart_t <= gw_tend_t:
        ed_ts = "DL_ACTIVE_UL_CONTROL_NEEDLESS"
    elif ed_tstart_t < gw_tstart_t:
        ed_ts = "DL_WILL_BE_ACTIVE_UL_CONTROL_NEEDED"
    elif gw_tend_t < ed_tstart_t:
        ed_ts = "DL_PASSIVE_DL_DUTY_CYCLE_CONTROL_NEEDED"
    return ed_ts


def __get_time_on_air(sf):
    return LorawanUtil.calculate_time_on_air(
            Constants.BANDWIDTH_IN_HERTZ,
            Constants.NUMBER_OF_PREAMBLE,
            Constants.SYNCHRONIZATION_WORD,
            Constants.SF_TO_MAC_PAYLOAD_IN_BYTE[sf],
            sf,
            Constants.CRC,
            Constants.IH,
            Constants.DE,
            Constants.CODING_RATE)