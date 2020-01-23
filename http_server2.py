import socket
import sys
import os
import select

from util import Request, Response

import traceback

# Safely serve a local file. Reject any file in ancestor directories
def staticFile(pathname, base=".") -> Response:
    base = os.path.abspath(base)
    path = os.path.join(base, pathname[1: ])

    if not path.startswith(base): # unsafe! if absolute path of the requested file does not start with base, then it is requesting something like /../../../../boot/vmlinuz
        return Response(403, body=b"<h1>403 Forbidden</h1>")

    if os.path.exists(path):
        if path.endswith(".html") or path.endswith(".htm"):
            response = Response(200, headers={"Content-Type": "text/html"})
            with open(os.path.join(".", path), "rb") as f:
                response.body.extend(f.read())
        else:
            response = Response(403, body=b"<h1>403 Forbidden</h1>")
    else:
        response = Response(404, body=b"<h1>404 Not Found</h1>")

    return response

def runForever(port):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) # according to <https://docs.python.org/3/library/socket.html#socket.AF_INET>
    sock.bind(("", port))
    sock.listen(5)
    readers = {
        sock: None,
    }
    
    while True:
        try:
            readables, *_ = select.select(readers, [], [])
        except:
            print("Keyboard interrupt. Exitting.")

            for v in readers.keys(): # clean up
                v.close()

            break
        
        for readable in readables:
            if readable is sock: # new connection coming in
                (connection, (ip, port)) = sock.accept()
                readers[connection] = {
                    "state": "header",
                    "header": bytearray()
                }
            else: # other clients
                if readers[readable]["state"] == "header": # in the state of reading header
                    chunk = readable.recv(1)
                    readers[readable]["header"].extend(chunk)
                    if readers[readable]["header"].endswith(b"\r\n" * 2): # request header fully transferred
                        try:
                            request = Request.fromBytes(readers[readable]["header"]) # parse request header
                        except: # fail to parse header
                            traceback.print_exc()
                            response = Response(403, body=b"HTTP request is invalid: <pre>" + readers[readable]["header"] + b"</pre>")
                            readable.sendall(bytes(response))
                            readable.close()
                            print("{} {} {}".format(request.method, request.pathname, response.statusCode))
                            readers.pop(readable)
                            continue

                        if ("Content-Length" in request.headers and request.headers["Content-Length"] == 0) or "Content-Length" not in request.headers: # if Content-Length: 0 or Content-Length not available, serve immediately
                            response = staticFile(request.pathname) # generate response
                            readable.sendall(bytes(response)) # serve response
                            readable.close()
                            print("{} {} {}".format(request.method, request.pathname, response.statusCode))
                            del readers[readable]
                        else: # need to read the whole request body
                            readers[readable]["state"] = "body"
                            readers[readable]["request"] = request
                            readers[readable].pop("header")
                            continue
                    else: # request header not fully transferred
                        continue # keep reading in the next iteration
                else: # in the state of reading body
                    chunk = readable.recv(4096)
                    request = readers[readable]["request"]
                    request.body.extend(chunk)
                    if len(request.body) >= int(request.headers["Content-Length"]): # there is a Content-Length, guaranteed, because we have served all requests that do not have one already
                        response = staticFile(request.pathname)
                        readable.sendall(bytes(response))
                        readable.close()
                        print("{} {} {}".format(request.method, request.pathname, response.statusCode))
                        readers.pop(readable)
                    else:
                        continue

helpMessage = "Usage: python3 http_server2.py [port]"

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