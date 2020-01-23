"""
Some helper classes to ease constructing request and response bytes
"""

class Request:
    def __init__(self, url, method="GET", headers=None, body=None, version="HTTP/1.0"):
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
        if not suffix: # if port is omited
            port = 80 # default to 80
        else: # port is specified
            port = int(suffix[0]) # "8080" -> 8080

        self.protocol = protocol # http:
        self.hostname = hostname # somewebsite.com (no port)
        self.port = port # 8080

        if "?" not in pathname:
            self.pathname = pathname # /path/page.html, no query string
            self.params = {} # ?a=b&c=d
        else:
            self.pathname, search = pathname.split("?")
            self.params = {}

            for entry in search.split("&"):
                if "=" in entry:
                    k, v, *_ = entry.split("=")
                else:
                    k, v = entry, None
                self.params[k] = v
            
        self.method = method # GET
        self.headers = headers or {}
        self.body = body or bytearray()
        self.version = version

    @property
    def url(self): # get original url
        return "{}//{}:{}{}".format(self.protocol, self.hostname, self.port, self.pathname)

    @property
    def host(self): # get somewebsite.com:8080
        return "{}:{}".format(self.hostname, self.port)

    @staticmethod
    def fromBytes(raw): # decode HTTP request bytes
        message, body = raw.split(b"\r\n" * 2, 1)
        requestLine, header = message.decode("utf8").split("\r\n", 1) # request message header is guaranteed text
        method, pathname, version = requestLine.split(maxsplit=2) # GET /doc/test.html HTTP/1.0
        headers = dict(tuple(v.split(": ", 1)) for v in header.split("\r\n"))
        return Request("http://" + headers["Host"] + pathname, method, headers, body, version)

    def __bytes__(self): # construct the request bytes from Request object
        requestLine = "{} {} {}".format(self.method, self.pathname, self.version)
        self.headers.update({
            "Host": self.host
        }) # Your client must include a "Host: " header
        header = "\r\n".join(": ".join(map(str, v)) for v in self.headers.items()) # genereate header
        message = "\r\n".join([requestLine, header]) + "\r\n" * 2 # concatenate request message header
        return bytes(message, "utf8") + self.body

    def __repr__(self): # for debug usage
        requestLine = "{} {} {}".format(self.method, self.pathname, self.version)
        self.headers.update({
            "Host": self.host,
            "Content-Length": len(self.body),
        }) # Your client must include a "Host: " header
        header = "\r\n".join(": ".join(map(str, v)) for v in self.headers.items()) # genereate header
        message = "\r\n".join([requestLine, header]) + "\r\n" * 2 # concatenate request message header
        return message + "[{} bytes body]".format(len(self.body))

class Response:
    codeMessageMapping = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
        403: "Forbidden",
    } # HTTP status code to message

    def __init__(self, statusCode, headers=None, body=None, version="HTTP/1.0"):
        self.statusCode = statusCode
        self.headers = headers or {}
        self.body = body or bytearray()
        self.version = version

    @staticmethod
    def fromBytes(raw): # decode HTTP response bytes
        message, body = raw.split(b"\r\n" * 2, 1)
        statusLine, header = message.decode("utf8").split("\r\n", 1) # response message header is guaranteed text
        version, statusCode, statusMessage = statusLine.split(maxsplit=2) # HTTP/1.1 200 OK -> HTTP/1.1, 200, OK
        statusCode = int(statusCode)
        headers = dict(tuple(v.split(": ", 1)) for v in header.split("\r\n"))
        return Response(statusCode, headers, body, version)

    def __bytes__(self): # construct the response bytes from Response object
        statusLine = "{} {} {}".format(self.version, self.statusCode, self.codeMessageMapping.get(self.statusCode, "OK"))
        self.headers.update({
            "Content-Length": len(self.body),
        })
        header = "\r\n".join(": ".join(map(str, v)) for v in self.headers.items()) # genereate header
        message = "\r\n".join([statusLine, header]) + "\r\n" * 2 # concatenate response message header
        return bytes(message, "utf8") + self.body

    def __repr__(self): # for debug usage
        statusLine = "{} {} {}".format(self.version, self.statusCode, self.codeMessageMapping.get(self.statusCode, "OK"))
        header = "\n".join(": ".join(map(str, v)) for v in self.headers.items()) # genereate header
        message = "\n".join([statusLine, header]) + "\n" * 2 # concatenate response message header
        return message + "[{} bytes body]".format(len(self.body))