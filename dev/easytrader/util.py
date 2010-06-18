def recv_n(conn, n):
    left = n
    content = []
    while 1:
        if left <= 0:
            break
        buf = conn.recv(left)
        content.append(buf)
        left = left - len(buf)

    return "".join(content)
