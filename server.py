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

SUIT_MAP = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANK_MAP_INV = {
    'Ace': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
    '8': 8, '9': 9, '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13
}

def card_to_net(c):
    try:
        s_int = SUIT_MAP.index(c.suit)
        r_int = RANK_MAP_INV[c.rank]
    except: 
        return 0, 0
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
        if len(data) < 38: 
            print("Invalid handshake")
            return
        cookie, mtype, rounds, name_b = struct.unpack("!IbB32s", data[:38])
        if cookie != MAGIC_COOKIE: 
            print("Invalid magic cookie")
            return
        
        team_name = name_b.decode().strip('\x00')
        print(f"Client {team_name} wants {rounds} rounds.")

        wins = 0

        # 2. Game Loop
        for r in range(1, rounds + 1):
            print(f"Round {r} starting for {team_name}")
            
            # --- Initialize Game Object ---
            current_deck = deck()
            current_player = player(team_name)
            current_dealer = dealer()
            current_game = game(current_dealer, current_player, current_deck)
            
            current_game.start_round() 
            
            # Extract cards from hands
            p_card1 = current_player.hand[0]
            p_card2 = current_player.hand[1]
            d_card1 = current_dealer.hand[0]
            d_card2 = current_dealer.hand[1] # Hidden card

            # Send Initial Cards
            send_card(conn, p_card1)
            send_card(conn, p_card2)
            send_card(conn, d_card1)

            # --- Player Turn ---
            player_active = True
            
            while player_active:
                if current_player.is_busted():
                    player_active = False
                    break
                
                # Wait for input
                data = conn.recv(1024)
                if not data: 
                    print(f"Client {team_name} disconnected")
                    return
                
                _, _, move_b = struct.unpack("!Ib5s", data[:10])
                move = move_b.decode().strip('\x00')

                if move == "Hittt":
                    new_card = current_deck.deal()
                    if new_card is None:
                        print("Deck empty! Ending round as tie.")
                        send_result(conn, MSG_TIE)
                        player_active = False
                        break
                    
                    current_player.receive_card(new_card)
                    
                    if current_player.is_busted():
                        send_card(conn, new_card, MSG_LOSS) # Send card + Loss result
                        player_active = False
                    else:
                        send_card(conn, new_card, MSG_ONGOING)
                else:
                    # Player Stands
                    player_active = False

            # --- Dealer Turn ---
            # Only proceeds if player didn't bust
            if not current_player.is_busted():
                # Reveal hidden card
                send_card(conn, d_card2)
                
                # Dealer draws cards
                while current_dealer.should_hit():
                    new_d = current_deck.deal()
                    if new_d is None:
                        print("Deck empty during dealer turn! Ending round.")
                        break
                    
                    current_dealer.receive_card(new_d)
                    send_card(conn, new_d)
                    
                    # Check if dealer busted
                    if current_dealer.is_busted():
                        break

                # Determine Winner
                p_val = current_player.calculate_hand_value()
                d_val = current_dealer.calculate_hand_value()
                
                if current_dealer.is_busted():
                    wins += 1
                    send_result(conn, MSG_WIN)
                elif p_val > d_val:
                    wins += 1
                    send_result(conn, MSG_WIN)
                elif d_val > p_val:
                    send_result(conn, MSG_LOSS)
                else:
                    send_result(conn, MSG_TIE)

            print(f"Round {r} done.")
        
        print(f"Client {team_name} finished {rounds} rounds with {wins} wins ({wins/rounds:.2%} win rate)")
            
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        conn.close()
        print(f"Connection closed with {addr}")

def udp_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except: 
        ip = "127.0.0.1"
    print(f"Server started, listening on IP address {ip}")
    msg = struct.pack("!IbH32s", MAGIC_COOKIE, OFFER_TYPE, TCP_PORT, SERVER_NAME.encode().ljust(32, b'\x00'))
    while True:
        sock.sendto(msg, ('<broadcast>', UDP_PORT))
        time.sleep(1)

if __name__ == "__main__":
    t = threading.Thread(target=udp_broadcast, daemon=True)
    t.start()
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.bind(("0.0.0.0", TCP_PORT))
    tcp.listen()
    print(f"TCP server listening on port {TCP_PORT}")
    while True:
        c, a = tcp.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()