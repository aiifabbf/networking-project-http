import socket
import sys
import os

from util import Request, Response

def runForever(port):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) # according to <https://docs.python.org/3/library/socket.html#socket.AF_INET>
    sock.bind(("", port))
    sock.listen(5)
    
    while True:
        try:
            (connection, (host, port)) = sock.accept()
        except:
            print("Keyboard interrupt. Exitting.")
            sock.close()
            break

        header = bytearray()

        while not header.endswith(b"\r\n" * 2): # read the header only
            chunk = connection.recv(1)
            header.extend(chunk)

        request = Request.fromBytes(header) # parse request

        path = "." + request.pathname
        if os.path.exists(path):
            if path.endswith(".html") or path.endswith(".htm"):
                response = Response(200, headers={"Content-Type": "text/html"})
                with open(os.path.join(".", path), "rb") as f:
                    response.body.extend(f.read())
            else:
                response = Response(403, body=b"<h1>403 Forbidden</h1>")
        else:
            response = Response(404, body=b"<h1>404 Not Found</h1>")

        connection.sendall(bytes(response))
        print("{} {} {}".format(request.method, request.pathname, response.statusCode))
        connection.close()

helpMessage = "Usage: python3 http_server1.py [port]"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] in {"-h", "--help"}:
            print(helpMessage)
        elif not sys.argv[1].isdecimal():
            raise Exception("Invalid port: {} is not a valid port number".format(sys.argv[1]))
        else:
            port = int(sys.argv[1])
            runForever(port)
    else:
        print(helpMessage)