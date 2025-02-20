import socket
import threading


def receive_messages(sock):
    while True:
        try:
            # Receive messages from the server
            data = sock.recv(48)
            if not data:
                # If no data is received, break out of the loop
                print("Disconnected from server.")
                break
            print(f"\nReceived from server: {data.decode()}\n> ", end='')
        except Exception as e:
            print(f"Error receiving data: {e}")
            sock.close()
            break


def tcp_client(server_ip, server_port):
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the client to the server
    client_socket.connect((server_ip, server_port))

    print(f"Connected to server {server_ip} on port {server_port}")

    # Start the receiving thread
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    try:
        while True:
            # Send data to the server
            message = input("> ")
            if message.lower() == 'quit':
                break
            message += '\r'
            client_socket.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection when done
        client_socket.close()
        print("Connection closed.")


# Example usage
if __name__ == "__main__":
    SERVER_IP = "127.0.0.1"  # Server IP address
    SERVER_PORT = 8300  # Server port number
    tcp_client(SERVER_IP, SERVER_PORT)
