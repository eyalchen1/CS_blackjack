import socket
import struct
from game_utils import *

# --- Config ---
TEAM_NAME = "TeamJoker"
MAGIC_COOKIE = 0xabcddcba
UDP_PORT = 13122
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4
MSG_WIN = 0x3
MSG_LOSS = 0x2
MSG_TIE = 0x1
MSG_ONGOING = 0x0

SUIT_MAP = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
def net_to_card(r, s):
    if r == 1: rank_str = 'Ace'
    elif r == 11: rank_str = 'Jack'
    elif r == 12: rank_str = 'Queen'
    elif r == 13: rank_str = 'King'
    else: rank_str = str(r)
    return card(rank_str, SUIT_MAP[s])

def start_client():
    try:
        rounds = int(input("How many rounds to play? "))
    except: rounds = 1

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp.bind(('', UDP_PORT))
    print("Client started, listening for offer requests...")
    
    server_ip = None
    server_port = None
    while True:
        data, addr = udp.recvfrom(1024)
        if len(data) < 39: continue
        cookie, mtype, port, name_b = struct.unpack("!IbH32s", data[:39])
        if cookie == MAGIC_COOKIE and mtype == OFFER_TYPE:
            server_ip = addr[0]
            server_port = port
            s_name = name_b.decode().strip('\x00')
            print(f"Received offer from {s_name} at {server_ip}")
            break
    
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_ip, server_port))
        conn.sendall(struct.pack("!IbB32s", MAGIC_COOKIE, REQUEST_TYPE, rounds, TEAM_NAME.encode().ljust(32, b'\x00')))
        
        wins = 0
        for r in range(1, rounds + 1):
            print(f"\n--- Round {r} ---")
            
            my_p = player("Me") # Local tracker for display
            cards_seen = 0
            
            # FLAG: Are we currently making decisions?
            my_turn = True 
            round_over = False

            while not round_over:
                data = conn.recv(9) # Header + payload (1+1+1+2+1 = 6 bytes? No, struct format: I(4) b(1) B(1) H(2) B(1) = 9 bytes)
                if not data: break
                
                cookie, mtype, res, rank, suit = struct.unpack("!IbBHB", data)
                
                if res != MSG_ONGOING:
                    # End of round logic
                    if rank != 0: # If a card came with the result (e.g. bust card)
                        c_obj = net_to_card(rank, suit)
                        my_p.receive_card(c_obj)
                        print(f"You got: {c_obj}")
                    
                    if res == MSG_WIN: 
                        print("You Won!")
                        wins += 1
                    elif res == MSG_LOSS: 
                        print("You Lost!")
                    else: 
                        print("It's a Tie!")
                    round_over = True
                    continue

                # Normal card received
                c_obj = net_to_card(rank, suit)
                cards_seen += 1
                
                # Display logic
                if cards_seen <= 2:
                    my_p.receive_card(c_obj)
                    print(f"You got: {c_obj}")
                elif cards_seen == 3:
                    print(f"Dealer shows: {c_obj}")
                else:
                    # If it's my turn, it's my card. If I stood, it's dealer's card.
                    if my_turn:
                        my_p.receive_card(c_obj)
                        print(f"You got: {c_obj}")
                    else:
                        print(f"Dealer dealt: {c_obj}")

                # Show Score if it's my turn
                if my_turn and cards_seen >= 2:
                    print(f"Your Hand Value: {my_p.calculate_hand_value()}")
                
                # Decision Point
                # 1. We must have seen initial cards (2 mine + 1 dealer = 3 total)
                # 2. It must be my turn
                # 3. We must not be busted (handled by server sending result code, but good to check)
                if cards_seen >= 3 and my_turn:
                    choice = input("Action (hit/stand): ").strip().lower()
                    if choice == 'hit':
                        conn.sendall(struct.pack("!Ib5s", MAGIC_COOKIE, PAYLOAD_TYPE, b"Hittt"))
                    else:
                        conn.sendall(struct.pack("!Ib5s", MAGIC_COOKIE, PAYLOAD_TYPE, b"Stand"))
                        my_turn = False # STOP ASKING FOR INPUT
                        print("Waiting for dealer...")

        print(f"\nFinished playing {rounds} rounds, win rate: {wins/rounds}")
        conn.close()
        start_client()
        
    except Exception as e:
        print(f"Error: {e}")
        start_client()

if __name__ == "__main__":
    try:
        start_client()
    except KeyboardInterrupt:
        print(f"\n{bcolors.WARNING}Game terminated by user. Goodbye!{bcolors.ENDC}")
    except Exception as e:
        print(f"\n{bcolors.FAIL}Unexpected error: {e}{bcolors.ENDC}")