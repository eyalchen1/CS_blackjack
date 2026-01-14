import socket
import struct
import sys # Added for flush
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
        rounds = int(input(f"{bcolors.BOLD}How many rounds to play? {bcolors.ENDC}"))
    except: rounds = 1

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp.bind(('', UDP_PORT))
    
    # --- VITAL: Timeout for UDP so Ctrl+C works while waiting ---
    udp.settimeout(1.0)
    
    print(f"{bcolors.BLUE}Client started, listening for offer requests...{bcolors.ENDC}")
    
    server_ip = None
    server_port = None
    
    while True:
        try:
            data, addr = udp.recvfrom(1024)
            if len(data) < 39: continue
            cookie, mtype, port, name_b = struct.unpack("!IbH32s", data[:39])
            if cookie == MAGIC_COOKIE and mtype == OFFER_TYPE:
                server_ip = addr[0]
                server_port = port
                s_name = name_b.decode().strip('\x00')
                print(f"Received offer from {bcolors.CYAN}{s_name}{bcolors.ENDC} at {server_ip}")
                break
        except socket.timeout:
            # Just loop back to check for Ctrl+C
            pass
    
    udp.close() # Close UDP before moving to TCP
    
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_ip, server_port))
        
        # --- Safety Timeout: If server dies, don't hang forever ---
        conn.settimeout(15.0) 
        
        conn.sendall(struct.pack("!IbB32s", MAGIC_COOKIE, REQUEST_TYPE, rounds, TEAM_NAME.encode().ljust(32, b'\x00')))
        
        wins = 0
        for r in range(1, rounds + 1):
            print(f"\n{bcolors.HEADER}--- Round {r} ---{bcolors.ENDC}")
            
            my_p = player("Me") 
            cards_seen = 0
            
            my_turn = True 
            round_over = False

            while not round_over:
                try:
                    data = conn.recv(9) 
                except socket.timeout:
                    print(f"{bcolors.FAIL}Server timed out. Game over.{bcolors.ENDC}")
                    return

                if not data: 
                    print("Connection closed by server")
                    return
                
                cookie, mtype, res, rank, suit = struct.unpack("!IbBHB", data)
                
                if res != MSG_ONGOING:
                    if rank != 0: 
                        c_obj = net_to_card(rank, suit)
                        my_p.receive_card(c_obj)
                        print(f"You got: {c_obj}")
                    
                    if res == MSG_WIN: 
                        print(f"{bcolors.GREEN}{bcolors.BOLD}You Won!{bcolors.ENDC}")
                        wins += 1
                    elif res == MSG_LOSS: 
                        print(f"{bcolors.FAIL}{bcolors.BOLD}You Lost!{bcolors.ENDC}")
                    else: 
                        print(f"{bcolors.WARNING}{bcolors.BOLD}It's a Tie!{bcolors.ENDC}")
                    round_over = True
                    continue

                c_obj = net_to_card(rank, suit)
                cards_seen += 1
                
                if cards_seen <= 2:
                    my_p.receive_card(c_obj)
                    print(f"You got: {c_obj}")
                elif cards_seen == 3:
                    print(f"Dealer shows: {c_obj}")
                elif cards_seen == 4 and not my_turn:
                    print(f"Dealer reveals: {c_obj}")
                else:
                    if my_turn:
                        my_p.receive_card(c_obj)
                        print(f"You got: {c_obj}")
                    else:
                        print(f"Dealer draws: {c_obj}")

                if my_turn and cards_seen >= 2:
                    print(f"Your Hand Value: {bcolors.BOLD}{my_p.calculate_hand_value()}{bcolors.ENDC}")
                
                if cards_seen >= 3 and my_turn:
                    # Force print to appear immediately
                    print(f"Action ({bcolors.GREEN}hit{bcolors.ENDC}/{bcolors.FAIL}stand{bcolors.ENDC}): ", end='', flush=True)
                    choice = sys.stdin.readline().strip().lower()
                    
                    if choice == 'hit':
                        conn.sendall(struct.pack("!Ib5s", MAGIC_COOKIE, PAYLOAD_TYPE, b"Hittt"))
                    else:
                        conn.sendall(struct.pack("!Ib5s", MAGIC_COOKIE, PAYLOAD_TYPE, b"Stand"))
                        my_turn = False 
                        print(f"{bcolors.WARNING}Waiting for dealer...{bcolors.ENDC}")

        print(f"\n{bcolors.BOLD}Finished playing {rounds} rounds, win rate: {wins/rounds:.2%}{bcolors.ENDC}")
        conn.close()
        
    except Exception as e:
        print(f"{bcolors.FAIL}Error: {e}{bcolors.ENDC}")

def main():
    while True:
        try:
            start_client()
            time.sleep(2)  
        except KeyboardInterrupt:
            print(f"\n{bcolors.WARNING}Game terminated by user. Goodbye!{bcolors.ENDC}")
            break
        except Exception as e:
            print(f"\n{bcolors.FAIL}Unexpected error: {e}{bcolors.ENDC}")
            print("Restarting client in 3 seconds...")
            time.sleep(3)

if __name__ == "__main__":
    main()