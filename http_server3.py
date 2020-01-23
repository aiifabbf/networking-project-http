import socket
import sys
import os
import json
import traceback

from util import Request, Response

def runForever(port):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) # according to <https://docs.python.org/3/library/socket.html#socket.AF_INET>
    sock.bind(("", port))
    sock.listen(5)
    
    while True:
        try:
            runOnce(sock)
        except KeyboardInterrupt:
            traceback.print_exc()
            print("Keyboard interrupt. Exitting.")
            sock.close()
            break
        except Exception as e:
            sock.close()
            raise e

def runOnce(sock: socket.socket) -> None:
        (connection, (host, port)) = sock.accept()
        header = bytearray()

        while not header.endswith(b"\r\n" * 2):
            chunk = connection.recv(1)
            header.extend(chunk)

        request = Request.fromBytes(header) # parse request
        if "Content-Length" in request.headers:

            while len(request.body) < int(request.headers["Content-Length"]):
                chunk = connection.recv(4096)
                request.body.extend(chunk)

        else: # if browser does not include a Content-Length header, then request has no body
            pass

            # while True:
            #     chunk: bytes = connection.recv(4096)
            #     if chunk:
            #         request.body.extend(chunk)
            #     else:
            #         break

        headers = {
            "Content-Type": "application/json"
        }
        if request.pathname != "/product":
            response = Response(404, body=b"404 Not Found")
        elif request.params == {}:
            response = Response(400, body=b"400 Bad Request")
        else:
            try:
                operands = list(map(float, request.params.values()))
                result = sum(operands)
                body = {
                    "operation": "product",
                    "operands": operands,
                    "result": result
                }
                response = Response(200, headers=headers, body=bytes(json.dumps(body), "utf8"))
            except ValueError:
                response = Response(400, body=b"400 Bad Request")

        connection.sendall(bytes(response))
        connection.close()

helpMessage = "Usage: python3 http_server3.py [port]"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] in {"-h", "--help"}:
            print(helpMessage)
        elif not sys.argv[1].isdecimal():
            raise Exception("Invalid port: {} is not a valid port number".format(sys.argv[1]))
        else:
            port = int(sys.argv[1])
            try:
                runForever(port)
            except:
                traceback.print_exc()
                exit(1)
    else:
        print(helpMessage)