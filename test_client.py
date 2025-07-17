import socketio

sio = socketio.Client()

@sio.on("reply")
def handle_reply(data):
    print("Billy replied:", data['response'])

sio.connect("http://localhost:5001")

while True:
    prompt = input("You: ").strip()
    if prompt in ("exit", "quit"):
        break
    sio.emit("ask", {"prompt": prompt})
