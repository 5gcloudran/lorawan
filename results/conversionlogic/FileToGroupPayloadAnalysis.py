from results.matchcase.SfGroupId import SfGroupId
from results.model.GroupPayloadAnalysis import GroupPayloadAnalysis
import util.ListUtil as ListUtil
import parameters.Constants as Constants


class FileToGroupPayloadAnalysis(object):
    def __init__(self, sf_to_group_ids):
        self.sf_to_group_ids = sf_to_group_ids

    def convert(self, output):
        splitter = '|'
        match_cases = []
        sf_to_converted_cases = {}

        for sf in self.sf_to_group_ids:
            group_ids = self.sf_to_group_ids[sf]
            match_cases += [SfGroupId(sf, group_id) for group_id in group_ids]

        for case in match_cases:
            sf = getattr(case, 'sf')
            group_id = getattr(case, 'group_id')

            attempts = []
            current_payloads = []
            maximum_payload_capacities = []

            for line in output:
                if case.match_case() in line:
                    values = line.split(splitter)
                    attempt = int(values[1].split(':')[1].lstrip().rstrip())
                    current_payload = float(values[4].split(':')[1].lstrip().rstrip())
                    maximum_payload_capacity = int(values[6].split(':')[1].lstrip().rstrip())

                    attempts.append(attempt)
                    current_payloads.append(current_payload)
                    maximum_payload_capacities.append(maximum_payload_capacity)

            if len(attempts) == 0:
                max_attemp = int( \
                    Constants.SIMULATION_LIFE_TIME_IN_SECONDS / \
                    Constants.SF_TO_SUPER_GROUP_PERIOD_IN_SEC.get(int(sf)))
                attempts = [x for x in range(1, max_attemp+1)]
                current_payloads = ListUtil.zero_list(max_attemp)
                maximum_payload_capacities = ListUtil.zero_list(max_attemp)

            group_payload_analysis = \
                GroupPayloadAnalysis(sf, group_id, attempts, current_payloads, maximum_payload_capacities)

            if sf_to_converted_cases.get(sf) is None:
                sf_to_converted_cases[sf] = [group_payload_analysis]
            else:
                sf_to_converted_cases[sf].append(group_payload_analysis)

        return sf_to_converted_cases



