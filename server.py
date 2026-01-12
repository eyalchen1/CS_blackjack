import socket
import threading
import struct
import time
from game_utils import *

# --- Network Constants ---
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4

MSG_WIN = 0x3
MSG_LOSS = 0x2
MSG_TIE = 0x1
MSG_ONGOING = 0x0

UDP_PORT = 13122
TCP_PORT = 5555
SERVER_NAME = "TeamTzion"

# --- Mapping Helpers (Class <-> Protocol) ---
SUIT_MAP = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANK_MAP_INV = {
    'Ace': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
    '8': 8, '9': 9, '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13
}

def card_to_net(c):
    # Converts your card object to (rank_int, suit_int)
    s_int = SUIT_MAP.index(c.suit)
    r_int = RANK_MAP_INV[c.rank]
    return r_int, s_int

def send_card(sock, card_obj, result_code=MSG_ONGOING):
    r, s = card_to_net(card_obj)
    packet = struct.pack("!IbBHB", MAGIC_COOKIE, PAYLOAD_TYPE, result_code, r, s)
    sock.sendall(packet)

def send_result(sock, result_code):
    packet = struct.pack("!IbBHB", MAGIC_COOKIE, PAYLOAD_TYPE, result_code, 0, 0)
    sock.sendall(packet)

def handle_client(conn, addr):
    print(f"Connected to {addr}")
    try:
        # 1. Handshake
        data = conn.recv(1024)
        if len(data) < 38: return
        cookie, mtype, rounds, name_b = struct.unpack("!IbB32s", data[:38])
        if cookie != MAGIC_COOKIE: return
        
        team_name = name_b.decode().strip('\x00')
        print(f"Client {team_name} wants {rounds} rounds.")

        # 2. Setup Game Objects
        srv_deck = deck()
        srv_player = player(team_name)
        srv_dealer = dealer()
        
        wins = 0

        # 3. Game Loop
        for r in range(1, rounds+1):
            print(f"Round {r} starting...")
            srv_deck.reset()
            srv_deck.shuffle()
            srv_player.reset_hand()
            srv_dealer.reset_hand()

            # Deal Initial
            p1 = srv_deck.deal()
            p2 = srv_deck.deal()
            d1 = srv_deck.deal()
            d2 = srv_deck.deal() # Hidden

            srv_player.receive_card(p1)
            srv_player.receive_card(p2)
            srv_dealer.receive_card(d1)
            srv_dealer.receive_card(d2)

            # Send initial cards to client
            send_card(conn, p1)
            send_card(conn, p2)
            send_card(conn, d1)

            # Player Turn
            while not srv_player.is_busted():
                # Wait for input
                data = conn.recv(1024)
                if not data: break
                _, _, move_b = struct.unpack("!Ib5s", data[:10])
                move = move_b.decode().strip('\x00')

                if move == "Hittt":
                    new_c = srv_deck.deal()
                    srv_player.receive_card(new_c)
                    
                    if srv_player.is_busted():
                        send_card(conn, new_c, MSG_LOSS)
                    else:
                        send_card(conn, new_c, MSG_ONGOING)
                else:
                    break # Stand

            # Dealer Turn (if player didn't bust)
            if not srv_player.is_busted():
                # Reveal hidden
                send_card(conn, d2)
                
                # Dealer plays
                while srv_dealer.should_hit():
                    new_d = srv_deck.deal()
                    srv_dealer.receive_card(new_d)
                    send_card(conn, new_d)

                # Determine Winner
                p_score = srv_player.calculate_hand_value()
                d_score = srv_dealer.calculate_hand_value()
                
                if srv_dealer.is_busted():
                    wins += 1
                    send_result(conn, MSG_WIN)
                elif p_score > d_score:
                    wins += 1
                    send_result(conn, MSG_WIN)
                elif d_score > p_score:
                    send_result(conn, MSG_LOSS)
                else:
                    send_result(conn, MSG_TIE)
            
            print(f"Round {r} done.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def udp_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except: ip = "127.0.0.1"

    print(f"Server started, listening on IP address {ip}")
    
    msg = struct.pack("!IbH32s", MAGIC_COOKIE, OFFER_TYPE, TCP_PORT, SERVER_NAME.encode().ljust(32, b'\x00'))
    
    while True:
        sock.sendto(msg, ('<broadcast>', UDP_PORT))
        time.sleep(1)

if __name__ == "__main__":
    t = threading.Thread(target=udp_broadcast, daemon=True)
    t.start()
    
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("0.0.0.0", TCP_PORT))
    tcp.listen()
    
    while True:
        c, a = tcp.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()