import base64
import struct

class BERGCloudConst(object):
    BC_EVENT_PRODUCT_ANNOUNCE   = 0xA000
    BC_COMMAND_SET_BERGCLOUD_ID = 0xB000

    BC_COMMAND_START_BINARY     = 0xC000
    BC_COMMAND_START_PACKED     = 0xC100
    BC_COMMAND_ID_MASK          = 0x00FF
    BC_COMMAND_FORMAT_MASK      = 0xFF00

    BC_COMMAND_DISPLAY_IMAGE    = 0xD000
    BC_COMMAND_DISPLAY_TEXT     = 0xD001

    BC_EVENT_START_BINARY       = 0xE000
    BC_EVENT_START_PACKED       = 0xE100
    BC_EVENT_ID_MASK            = 0x00FF
    BC_EVENT_FORMAT_MASK        = 0xFF00

    BC_COMMAND_FIRMWARE_ARDUINO = 0xF010
    BC_COMMAND_FIRMWARE_MBED    = 0xF020


class DeviceCommandPayload(object):
    COMMANDS = {
        'set_delivery_and_print': 0x0001,
        'set_delivery': 0x0002,
        'set_delivery_and_print_no_face': 0x0011,
        'set_delivery_no_face': 0x0012,
        'set_personality': 0x0102,
        'set_personality_with_message': 0x0101,
        'set_quip': 0x0202,
        'firmware_update': 0xf000
    }

    @classmethod
    def from_base64(cls, base64_payload):
        data = base64.b64decode(base64_payload)

        # encode_command_header and add_length_header_to_payload
        # iare used for all Barringer commands,
        # in lib/berg_cloud/barringer/commands.rb
        offset = 0
        device_type, reserved_byte, command_name_id, file_id, reserved_long, payload_length \
            = struct.unpack_from("<BBHLLL", data, 0)

        # can only unwrap certain commands
        if device_type != 1:
            raise ArgumentError, "Can only unwrap Little Printer commands"
        if command_name_id not in DeviceCommandPayload.COMMANDS.values():
            raise ArgumentError, "Unknown command name ID"
        if command_name_id == DeviceCommandPayload.COMMANDS['firmware_update']:
            raise ArgumentError, "Can't handle firmware_update command"

        # move to payload
        offset += 1 + 1 + 2 + 4 + 4 + 4

        # payloads encoded by printable_command -> encode_files have a
        # similar format: a list of files, each as
        # - length+1 (<L)
        # - 0 for no encryption and no IV (<B)
        # - the file
        files = []
        while offset < len(data):
            file_length_plus_one, reserved_byte = struct.unpack_from("<LB", data, offset)
            offset += 5
            files.append( data[offset:offset+file_length_plus_one-1] )
            offset += file_length_plus_one-1
        # when finished, offset should be the data length
        assert offset == len(data)

        return (device_type, reserved_byte, command_name_id, file_id, reserved_long, payload_length, files)


class DeviceEventPayload(object):
    # Barringer protocol
    EVENT_HEADER_SIZE = 10

    EVENT_HEARTBEAT = 1
    EVENT_DID_PRINT = 2
    EVENT_DID_POWER_ON = 3

    EVENT_HEARTBEAT_SIZE = 4
    EVENT_DID_PRINT_SIZE = 5
    EVENT_DID_POWER_ON_SIZE_LONG = 74  # Using fragmentation
    EVENT_DID_POWER_ON_SIZE_SHORT = 58 # No fragmentation

    resetDict = {
                 0x0000 : "Undeterminable cause",
                 0x0100 : "FIB bootloader",
                 0x0200 : "Ember bootloader",
                 0x0300 : "External reset",
                 0x0400 : "Power on",
                 0x0500 : "Watchdog",
                 0x0600 : "Software triggered",
                 0x0700 : "Software crash",
                 0x0800 : "Flash failure",
                 0x0900 : "Fatal error",
                 0x0a00 : "Access fault"}

    @classmethod
    def from_base64(cls, base64_payload):
        data = base64.b64decode(base64_payload)

        return_hash = {}

        offset = 0
        eventCode, commandInvocationId, eventPayloadLength = \
                struct.unpack_from("<HII", data, offset)

        return_hash['event_code'] = eventCode
        return_hash['command_invocation_id'] = commandInvocationId
        return_hash['event_payload_length'] = eventPayloadLength

        # Move on to the actual payload and switch
        offset += 2 + 4 + 4

        if len(data) != (DeviceEventPayload.EVENT_HEADER_SIZE + eventPayloadLength):
            return_hash['error'] = 'Invalid event payload length of %d. Should be %d' % (len(data), DeviceEventPayload.EVENT_HEADER_SIZE + eventPayloadLength)
            return return_hash

        #
        # Barringer protocol events
        #
        if eventCode & BERGCloudConst.BC_EVENT_FORMAT_MASK == BERGCloudConst.BC_EVENT_START_BINARY:
            return_hash['name'] = "event_binary"
            return_hash['event_id'] = eventCode & BERGCloudConst.BC_EVENT_ID_MASK
            return_hash['data'] = data[offset:]
        elif eventCode & BERGCloudConst.BC_EVENT_FORMAT_MASK == BERGCloudConst.BC_EVENT_START_PACKED:
            return_hash['name'] = "event_packed"
            return_hash['event_id'] = eventCode & BERGCloudConst.BC_EVENT_ID_MASK
            return_hash['data'] = data[offset:]
        elif eventCode == DeviceEventPayload.EVENT_DID_POWER_ON:
            if eventPayloadLength == DeviceEventPayload.EVENT_DID_POWER_ON_SIZE_LONG:
                deviceType, firmwareBuildVersion, loaderBuildVersion, protocolVersion, resetDescription \
                    = struct.unpack_from("<I32s32sIH", data, offset)
            elif eventPayloadLength == DeviceEventPayload.EVENT_DID_POWER_ON_SIZE_SHORT:
                deviceType, firmwareBuildVersion, loaderBuildVersion, protocolVersion, resetDescription \
                    = struct.unpack_from("<I24s24sIH", data, offset)
            else:
                return_hash['error'] = 'Invalid did_power_on payload length of %d. Should be %d or %d.' % \
                    (eventPayloadLength, DeviceEventPayload.EVENT_DID_POWER_ON_SIZE_SHORT, DeviceEventPayload.EVENT_DID_POWER_ON_SIZE_LONG)
                return return_hash

            return_hash['name'] = "did_power_on"
            return_hash['device_type'] = deviceType
            return_hash['firmware_build_version'] = firmwareBuildVersion
            return_hash['loader_build_version'] = loaderBuildVersion
            return_hash['protocol_version'] = protocolVersion

            # High byte of resetDescription is the reset 'base type', low byte gives
            # extended information about the reset cause.
            if (resetDescription & 0xff00) in DeviceEventPayload.resetDict:
                return_hash['reset_text'] = DeviceEventPayload.resetDict[resetDescription & 0xff00]
            else:
                return_hash['reset_text'] = "Unknown"

            return_hash['reset_description'] = resetDescription

        elif eventCode == BERGCloudConst.BC_EVENT_PRODUCT_ANNOUNCE:
            if eventPayloadLength != 20:
                return_hash['error'] = 'Invalid product announce payload length of %d. Should be 20' % eventPayloadLength
                return return_hash

            id0, id1, id2, id3, version =  struct.unpack_from(">LLLLL", data, offset)
            return_hash['name'] = "product_announce"
            return_hash['product_id'] = "%08x%08x%08x%08x" % (id0, id1, id2, id3)
            return_hash['product_version'] = version

        elif eventCode == DeviceEventPayload.EVENT_HEARTBEAT:
            if eventPayloadLength != DeviceEventPayload.EVENT_HEARTBEAT_SIZE:
                return_hash['error'] = 'Invalid heartbeat payload length of %d. Should be %d' % (eventPayloadLength, DeviceEventPayload.EVENT_HEARTBEAT_SIZE)
                return return_hash

            uptime =  struct.unpack_from("<I", data, offset)
            return_hash['name'] = "heartbeat"
            return_hash['uptime'] = uptime

        elif eventCode == DeviceEventPayload.EVENT_DID_PRINT:
            if eventPayloadLength != DeviceEventPayload.EVENT_DID_PRINT_SIZE:
                return_hash['error'] = 'Invalid did_print payload length of %d. Should be %d' % (eventPayloadLength, DeviceEventPayload.EVENT_DID_PRINT_SIZE)
                return return_hash

            print_type, print_id = struct.unpack_from("<BI", data, offset)
            return_hash['name'] = "did_print"
            return_hash['type'] = print_type
            return_hash['id'] = print_id

        else:
            return_hash['name'] = "unknown"
            return_hash['code'] = eventCode

        return return_hash


        #init_params = {}
        # fill in here

        #instance = cls(**init_params)
        #return instance
