END_DEVICE_NUMBER = 1000

MIN_SF = 7
MAX_SF = 12
SFs = [sf for sf in range(MIN_SF, MAX_SF+1)]

EXPONENTIAL_DIST_SIZE = MAX_SF - MIN_SF + 1
EXPONENTIAL_DIST_SCALE = 1

SUPER_GROUP_LENGTH_IN_SECONDS = 15
GROUP_ID_LENGTH_IN_BIT = 8
DEVICE_ADDRESS_LENGTH_IN_BIT = 32
SUBSCRIPTION_ID_LENGTH_IN_BIT = 24

# their sum should be equal to 1.
GROUP_UPLINK_PERIOD_PERCENTAGE = 0.5
GROUP_MIDLINK_PERIOD_PERCENTAGE = 0
GROUP_DOWNLINK_PERIOD_PERCENTAGE = 0.5

# they are for calculation of the time on air
BANDWIDTH_IN_HERTZ = 125
NUMBER_OF_PREAMBLE = 8
SYNCHRONIZATION_WORD = 8
SF_TO_MAC_PAYLOAD_IN_BYTE = {}
CRC = 1
IH = 0
DE = 0
CODING_RATE = 1

