import socket
import struct
import sys
import time
# Ensure game_utils.py is in the same directory
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
    # Convert protocol rank to string
    if r == 1: rank_str = 'Ace'
    elif r == 11: rank_str = 'Jack'
    elif r == 12: rank_str = 'Queen'
    elif r == 13: rank_str = 'King'
    else: rank_str = str(r)
    
    # --- FIX: s is 1-4, but list index is 0-3 ---
    if 1 <= s <= 4:
        suit_str = SUIT_MAP[s-1]
    else:
        suit_str = "Unknown"
        
    return card(rank_str, suit_str)

def start_client():
    try:
        # Prompt for rounds
        print(f"{bcolors.BOLD}How many rounds to play? (Enter 0 to quit): {bcolors.ENDC}", end='', flush=True)
        rounds_input = sys.stdin.readline().strip()
        
        if not rounds_input:
            rounds = 1
        else:
            rounds = int(rounds_input)
            
        # --- EXIT CONDITION ---
        if rounds == 0:
            print("Exiting game. Goodbye!")
            return False # Signal to main loop to stop
            
    except ValueError: 
        print(f"{bcolors.WARNING}Invalid input. Defaulting to 1 round.{bcolors.ENDC}")
        rounds = 1

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp.bind(('', UDP_PORT))
    
    # Timeout for UDP so we can check for Ctrl+C
    udp.settimeout(1.0)
    
    print(f"\n{bcolors.BLUE}Client started, listening for offer requests...{bcolors.ENDC}")
    
    server_ip = None
    server_port = None
    
    # UDP Listening Loop
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
            pass # Loop back to allow Ctrl+C check
        except KeyboardInterrupt:
            return False
    
    udp.close()
    
    # TCP Connection
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_ip, server_port))
        
        # --- VALIDATION: Confirm connection ---
        print(f"{bcolors.GREEN}TCP connection established successfully with {server_ip}:{server_port}{bcolors.ENDC}")
        
        conn.settimeout(15.0) 
        
        # Send Request
        conn.sendall(struct.pack("!IbB32s", MAGIC_COOKIE, REQUEST_TYPE, rounds, TEAM_NAME.encode().ljust(32, b'\x00')))
        conn.sendall(b'\n') # Requirement mentions a line break
        
        wins = 0
        for r in range(1, rounds + 1):
            print(f"\n{bcolors.HEADER}--- Round {r} ---{bcolors.ENDC}")
            
            my_p = player("Me") 
            cards_seen = 0
            my_turn = True 
            round_over = False

            while not round_over:
                try:
                    # Expecting exactly 9 bytes for a message
                    data = conn.recv(9) 
                except socket.timeout:
                    print(f"{bcolors.FAIL}Server timed out. Game over.{bcolors.ENDC}")
                    return True

                if not data: 
                    print("Connection closed by server")
                    return True
                
                cookie, mtype, res, rank, suit = struct.unpack("!IbBHB", data)
                
                # --- CASE 1: Game Over (Win/Loss/Tie) ---
                if res != MSG_ONGOING:
                    # If server sent a card along with the result (e.g., the bust card)
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
                    continue # Break inner loop, go to next round in for loop

                # --- CASE 2: Ongoing Game (Receive Card) ---
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
                
                # --- Player Decision ---
                if cards_seen >= 3 and my_turn:
                    # Check if we didn't just bust on the received card
                    if my_p.calculate_hand_value() > 21:
                         # We rely on server to send the Loss message next, so we don't ask for input
                         pass 
                    else:
                        print(f"Action ({bcolors.GREEN}hit{bcolors.ENDC}/{bcolors.FAIL}stand{bcolors.ENDC}): ", end='', flush=True)
                        choice = sys.stdin.readline().strip().lower()
                        
                        if choice == 'hit':
                            conn.sendall(struct.pack("!Ib5s", MAGIC_COOKIE, PAYLOAD_TYPE, b"Hittt"))
                        else:
                            conn.sendall(struct.pack("!Ib5s", MAGIC_COOKIE, PAYLOAD_TYPE, b"Stand"))
                            my_turn = False 
                            print(f"{bcolors.WARNING}Waiting for dealer...{bcolors.ENDC}")

        # Summary
        if rounds > 0:
            print(f"\n{bcolors.BOLD}Finished playing {rounds} rounds, win rate: {wins/rounds:.2%}{bcolors.ENDC}")
        else:
            print("\nNo rounds played.")
            
        conn.close()
        return True # Continue main loop
        
    except Exception as e:
        print(f"{bcolors.FAIL}Error: {e}{bcolors.ENDC}")
        return True # Continue main loop

def main():
    while True:
        try:
            # If start_client returns False, it means user wants to quit
            should_continue = start_client()
            if not should_continue:
                break
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{bcolors.WARNING}Game terminated by user. Goodbye!{bcolors.ENDC}")
            break
        except Exception as e:
            print(f"\n{bcolors.FAIL}Unexpected error: {e}{bcolors.ENDC}")
            break

if __name__ == "__main__":
    main()