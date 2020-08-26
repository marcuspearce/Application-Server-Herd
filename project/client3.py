# client for testing purposes

import asyncio

LOCALHOST = '127.0.0.1'

# adapted from TA slides
async def echo(event_loop):

    # connect to server JAQUEZ (portno = 12231)
    reader, writer = await asyncio.open_connection(LOCALHOST, 12231, loop=event_loop)

    # msg = 'IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997'
    msg = 'WHATSAT kiwi.cs.ucla.edu 2 5'
    # msg = 'NOTVALID kiwi.cs.ucla.edu 8 21'

    print("Sent: {}\n".format(msg) )
    writer.write(msg.encode())

    data = await reader.read(1000000)
    print("Received: {}\n".format(data.decode()) )

    writer.close()


# separate to init event_loop
def main():
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(echo(event_loop))
    event_loop.close()


if __name__ == '__main__':
    main()