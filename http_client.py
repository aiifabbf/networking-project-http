import sys
import socket

from util import Request, Response

def get(url, headers=None):
    """Naive GET, does not handle any error or redirect"""
    request = Request(url) # Your client must include a "Host: " header
    ip = socket.gethostbyname(request.hostname)
    port = request.port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.send(bytes(request))

    # use Content-Length to decide when the response has been fully transferred
    header = bytearray()

    while not header.endswith(b"\r\n" * 2):
        chunk = sock.recv(1)
        header.extend(chunk)

    response = Response.fromBytes(header) # construct response from header
    if "Content-Length" in response.headers:
        contentLength = int(response.headers["Content-Length"]) # get Content-Length field. If none, no body

        while len(response.body) < contentLength: # keep reading body until reaching Content-Length
            chunk = sock.recv(4096)
            response.body.extend(chunk)

    else: # if there is no Content-Length field in header, then assume server would close the stream when finishing

        while True: # keep reading until stream is closed
            chunk = sock.recv(4096)
            if chunk: # stream has been closed
                response.body.extend(chunk)
            else:
                break

    sock.close()

    return response

if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: python3 http_client.py URL")
        exit(0)

    url = sys.argv[1]
    depth = 0

    while depth <= 10:
        try:
            response = get(url)
        except:
            print("Invalid protocol: only HTTP is currently supported")
            exit(1)

        if response.statusCode in {301, 302}: # redirect
            url = response.headers.get("Location", None) # new url
            if not url:
                raise Exception("Indirect failure: no target specified")
            print("Redirected to: {}".format(url), file=sys.stderr) # Your client should also print a message to stderr explaining what happened
            depth += 1
        elif response.statusCode >= 400: # >= 400
            print(response.body.decode("utf8")) # but also print the response body
            exit(1) # should return a non-zero exit code
        else:
            if "text/html" in response.headers["Content-Type"]: # some sites put "charset" in "Content-Type"
                if "charset" in response.headers["Content-Type"]:
                    segments = [v.strip() for v in response.headers["Content-Type"].split(";")]
                    
                    for v in segments:
                        if v.startswith("charset"):
                            charset = v.split("=")[1]
                            break
                    else:
                        charset = "utf8"

                else:
                    charset = "utf8"
                print(response.body.decode(charset))
                exit(0) # Your program should return a unix exit code of 0 on success
            else:
                print("Content type not understood: Content-Type is not text/html", file=sys.stderr)
                exit(1)

    print("Too many redirects", file=sys.stderr) # give up after 10 redirects
    exit(1)