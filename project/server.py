import sys
import asyncio
import aiohttp
import json
import time
import re

API_KEY = 'AIzaSyDIbleGwGlibD6Eq3LSem7sUI_Lpbdclig'

LOCALHOST = '127.0.0.1'

server_communications_dict = {
    'Hill'      : ['Jaquez', 'Smith'],
    'Jaquez'    : ['Hill', 'Singleton'],
    'Smith'     : ['Campbell', 'Singleton', 'Hill'],
    'Campbell'  : ['Smith', 'Singleton'],
    'Singleton' : ['Jaquez', 'Smith', 'Campbell']
}

# server name to portno
server_to_port_dict = {
    'Hill'      : 12230,
    'Jaquez'    : 12231,
    'Smith'     : 12232,
    'Campbell'  : 12233,
    'Singleton' : 12234
}

# client id to client data
client_dict = {}


# to make sure correct format of coordinate
# https://docs.python.org/3/library/re.html
def is_coord(input):
    result = re.match('[+-]\d+\.\d+[+-]\d+\.\d+', input)
    return result

def is_float(input):
    try:
        float(input)
        return True
    except ValueError:
        return False

def is_int(input):
    try:
        int(input)
        return True
    except ValueError:
        return False

# return array holding float values of [latitude, longitude] 
def parse_coord(input):
    index = -1              # index to separate string at
    for i in range(len(input)):
        if i != 1 and (input[i] == '+' or input[i] == '-'):
            index = i

    # don't want to include '+' but do want to include '-'
    latitude = float(input[1:index])
    if input[0] == '-':
        latitude *= -1
    longitude = float(input[index+1:])
    if input[index] == '-':
        longitude *= -1

    return [latitude, longitude]







# return output for IAMAT
def process_iamat(msg_info, input_time):
    server_name = sys.argv[1]

    # get time difference
    time_diff = input_time - float(msg_info[3])
    if time_diff > 0:
        time_diff = '+' + str(time_diff)

    # add IAMAT info to client dict
        # [lat/long, client_time_sent, server_time_rec, og_server_name, time_diff]
    client_data = [msg_info[2], msg_info[3], str(input_time), server_name, time_diff]
    client_dict[msg_info[1]] = client_data

    # send client info to all connected servers
        # send message FLOOD server_name client_id lat/long, client_time_sent, server_time_rec, og_server_name, time_diff
    flood_msg =  "FLOOD {0} {1} {2} {3} {4} {5} {6}".format(server_name, msg_info[1], msg_info[2], msg_info[3], str(input_time), server_name, time_diff)
    asyncio.create_task(flood(flood_msg, server_name))

    # AT Hill +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997
    return "AT {0} {1} {2} {3} {4}".format(server_name, time_diff, msg_info[1], msg_info[2], msg_info[3])



# return output for WHATSAT
async def process_whatsat(msg_info, input):
    client_id = msg_info[1]

    # check have data for given client_id
    if client_id not in client_dict:
        output = "? {}".format(input)
    
    else:
        # get client by their client_id
        client = client_dict[client_id]

        # process coordinates
        coord = parse_coord(client[0])
        latitude = str(coord[0])
        longitude = str(coord[1])
        location = "{0},{1}".format(latitude,longitude)     # convert to format required
        radius = float(msg_info[2]) * 1000                  # since radius param is in METRES

        # AT Hill +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997
        output = "AT {0} {1} {2} {3} {4}\n".format(client[3], client[4], client_id, client[0], client[1])

        # for google API: https://developers.google.com/places/web-service/search
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={0}&location={1}&radius={2}".format(API_KEY, location, radius)

        # for aiohttp https://docs.aiohttp.org/en/stable/
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # for json: https://docs.python.org/3/library/json.html
                res = await response.json()
                num_items = int(msg_info[3])
                res['results'] = res['results'][:num_items]
                # res = re.sub(r'\n+', '\n', res)              
                output += json.dumps(res, indent=4)             # from piazza
                output += '\n\n'
    
    return output



# write appropriate output depending on input (error, IAMAT, WHATSAT)
async def write_output(input, input_time):
    # remove leading and trailing white space, return array of elements delimited by white space
    msg_info = input.strip().split()
    output = ""

    if(not is_valid_input(msg_info)):
        output = "? {}".format(input)
    
    command_name = msg_info[0]

    if command_name == 'IAMAT':
        output = process_iamat(msg_info, input_time)

    if command_name == 'WHATSAT':
        output = await process_whatsat(msg_info, input)

    return output




























# write to all servers in server_communications_dict
async def flood(flood_msg, server_name):
    for s in server_communications_dict[server_name]:
        log_file.write("Connecting: FLOOD from {0} to {1}... \n".format(server_name, s))
        try:
            reader, writer = await asyncio.open_connection(LOCALHOST, server_to_port_dict[s], loop=event_loop)
            writer.write(flood_msg.encode())
            await writer.drain()
            writer.close()
            log_file.write("Sent: {}\n".format(flood_msg))
        except Exception as e:
            # print(e)
            log_file.write("FAIL -- could not connect to {}\n".format(s))
            pass        # should still continue even if one server goes down




# passed in array of all white-space separated elements in list, return bool
    # IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997
    # WHATSAT kiwi.cs.ucla.edu 10 5
def is_valid_input(msg_info):
    length = len(msg_info)
    command_name = msg_info[0]
    if length < 1:
        return False
    
    if command_name == 'IAMAT':
        return (length == 4 and is_coord(msg_info[2]) and is_float(msg_info[3]) )
    
    if command_name == 'WHATSAT':
        if length == 4 and is_int(msg_info[2]) and is_int(msg_info[3]):
            radius = int(msg_info[2])
            num = int(msg_info[3])
            return not (radius <= 0 or radius > 50 or num <= 0 or num > 20)
        return False
    
    # should always be correct unless someone sent a message starting with "FLOOD", so just surface-lvl check
    if command_name == 'FLOOD':
        return length == 8

    return False




# starting server adapted from TA slides and https://asyncio.readthedocs.io/en/latest/tcp_echo.html
async def handle_connection(reader, writer):
    # wait until recieve input
    data = await reader.read(1000000)          # 1e6 cuz not guaranteed EOF -> from piazza
    server_name = sys.argv[1]

    # process input
    input_time = time.time()
    input = data.decode()
    log_file.write("Received: {}\n".format(input))

    msg_info = input.strip().split()
    
    # server-server -> update and flood
    if is_valid_input(msg_info) and msg_info[0] == 'FLOOD':
        # FLOOD server_name client_id lat/long, client_time_sent, server_time_rec, og_server_name, time_diff
        client_id = msg_info[2]
        flood_msg =  "FLOOD {0} {1} {2} {3} {4} {5} {6}".format(server_name, msg_info[2], msg_info[3], msg_info[4], msg_info[5], msg_info[6], msg_info[7])

        if client_id not in client_dict:
            # in client_dict: [lat/long, client_time_sent, server_time_rec, og_server_name, time_diff]
            client_dict[client_id] = msg_info[3:]
            # send w/ updated server name (first arg, the one being sent from)
            asyncio.create_task(flood(flood_msg, server_name))
        
        # only if this is more recent update for given client, otherwise don't call flood if is second time received msg
        else:
            # if is more recent instance of given client_id i.e. client_time_send > in current call
            if msg_info[4] > client_dict[client_id][1]:
                client_dict[client_id] = msg_info[3:]
                asyncio.create_task(flood(flood_msg, server_name))


    # server-client -> write output
    else:
        output = await write_output(input, input_time)
        writer.write(output.encode())
        await writer.drain()
        log_file.write("Sent: {}\n".format(output))







# starting server adapted from TA slides and https://asyncio.readthedocs.io/en/latest/tcp_echo.html
# main() is not asyncio cuz want to get event_loop outside of event loop
def main():
    # check valid command-line args
    if len(sys.argv) != 2:
        print("Error: Invalid arguments")
        print("Usage: python3 server.py <server_name>")
        sys.exit(1)
    if sys.argv[1] not in server_to_port_dict:
        print("Error: Invalid server_name")
        print("Usage: python3 server.py <server_name>")
        sys.exit(1)

    server_name = sys.argv[1]
    portno = server_to_port_dict[server_name]

    # init event loop and server (coroutine) (need to init global here cuz of python scope issues)
    global event_loop 
    event_loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_connection, LOCALHOST, portno, loop=event_loop)
    server = event_loop.run_until_complete(coro)

     # init log file
    global log_file
    log_file = open(server_name + "_log.txt", "a+", 1)
    log_file.write("Initialized server {0} at port {1}\n".format(server_name, portno))

    # stop event loop when keyboard interrupt
    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        pass
    
    server.close()
    event_loop.run_until_complete(server.wait_closed())
    event_loop.close()

    log_file.write("Shutting down server {0}\n".format(server_name))
    log_file.close()



if __name__ == '__main__':
    main()