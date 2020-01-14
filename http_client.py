from typing import *
import sys
import socket

def get(url: str, headers: Dict[str, Any]=None) -> Tuple[int, Dict[str, str], bytearray]:
    """Naive GET, does not handle any error or redirect"""
    # name of each part in the url from MDN <https://developer.mozilla.org/en-US/docs/Web/API/Location>
    protocol, *suffix = url.split("//", 1) # http:, ...
    if not suffix or suffix[0] == "":
        if protocol.endswith(":"): # http://
            raise Exception("Invalid url: no host")
        else: # cs.northwestern.edu
            raise Exception("Invalid url: no protocol specified")
    if protocol != "http:":
        raise Exception("Invalid protocol: only HTTP is currently supported")

    host, *suffix = suffix[0].split("/", 1) # somewebsite.com:8080, ...
    pathname = "/" + "".join(suffix) # /path/page.html
    hostname, *suffix = host.split(":") # somewebsite.com, 8080
    if not suffix: # if port is ommited
        port = 80 # default to 80
    else: # port is specified
        port = int(suffix[0]) # "8080" -> 8080

    ip = socket.gethostbyname(hostname)

    sock = socket.create_connection((ip, port))
    requestLine: str = "GET {} HTTP/1.1".format(pathname)
    if not headers:
        headers = {}
    headers.update({
        "Host": host
    }) # Your client must include a "Host: " header
    header: str = "\r\n".join(": ".join(map(str, v)) for v in headers.items())
    message: str = "\r\n".join([requestLine, header]) + "\r\n" * 2

    sock.send(bytes(message, "utf8"))
    raw = bytearray()
    receiveing = True

    while receiveing:
        chunk: bytes = sock.recv(1024)
        if len(chunk) == 0: # no more data
            receiveing = False
        raw.extend(chunk)

    sock.close()
    # start decoding HTTP response
    responseMessage, responseBody = raw.split(b"\r\n" * 2, 1)
    responseStatusLine, responseHeader = responseMessage.decode("utf8").split("\r\n", 1) # response message header is guaranteed text
    version, statusCode, statusMessage = responseStatusLine.split(maxsplit=2) # HTTP/1.1 200 OK -> HTTP/1.1, 200, OK
    statusCode = int(statusCode)
    responseHeaders = dict(tuple(v.split(": ", 1)) for v in responseHeader.split("\r\n"))

    return (statusCode, responseHeaders, responseBody)

if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: python3 http_client.py URL")
        exit(0)

    url = sys.argv[1]
    depth = 0

    while depth <= 10:
        statusCode, headers, body = get(url)
        if statusCode in {301, 302}: # redirect
            url = headers.get("Location", None) # new url
            if not url:
                raise Exception("Indirect failure: no target specified")
            print("Redirected to: {}".format(url), file=sys.stderr) # Your client should also print a message to stderr explaining what happened
            depth += 1
        elif statusCode >= 400: # >= 400
            print(body.decode("utf8")) # but also print the response body
            exit(1) # should return a non-zero exit code
        else:
            if "text/html" in headers["Content-Type"]: # some sites put "charset" in "Content-Type"
                print(body.decode("utf8"))
                exit(0) # Your program should return a unix exit code of 0 on success
            else:
                raise Exception("Content type not understood: Content-Type is not text/html")

    raise Exception("Too many redirects") # give up after 10 redirects