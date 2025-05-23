import msgpack

with open("response.msgpack", "rb") as f:
    msg = f.read()

data = msgpack.unpackb(msg, raw=False)
print(data)