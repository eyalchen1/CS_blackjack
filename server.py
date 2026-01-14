import socket
import threading
import struct
import time
# Ensure game_utils.py is in the same folder and has deck, player, dealer, game, bcolors classes
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

# Mappings for protocol
SUIT_MAP = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANK_MAP_INV = {
    'Ace': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
    '8': 8, '9': 9, '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13
}

def card_to_net(c):
    """
    Converts a Card object to protocol integers (Rank, Suit).
    """
    try:
        # Check if suit is string or object and map to index 1-4
        if c.suit in SUIT_MAP:
            s_int = SUIT_MAP.index(c.suit) + 1 # +1 because protocol usually expects 1-4, not 0-3
        else:
            s_int = 1 # Default fallback
            
        r_int = RANK_MAP_INV.get(str(c.rank), 0)
    except Exception as e:
        print(f"Error converting card: {e}")
        return 0, 0
    return r_int, s_int

def send_card(sock, card_obj, result_code=MSG_ONGOING):
    """
    Helper function to send a card packet to the client.
    """
    try:
        r, s = card_to_net(card_obj)
        # Packing: Cookie (4), Type (1), Result (1), Rank (2), Suit (1)
        packet = struct.pack("!IbBHB", MAGIC_COOKIE, PAYLOAD_TYPE, result_code, r, s)
        sock.sendall(packet)
        # Tiny sleep to ensure client processes the packet separately (prevents coalescing)
        time.sleep(0.1) 
    except Exception as e:
        print(f"Error sending card: {e}")

def send_result(sock, result_code):
    """
    Helper function to send just a result (Win/Loss/Tie) without a specific card.
    """
    try:
        packet = struct.pack("!IbBHB", MAGIC_COOKIE, PAYLOAD_TYPE, result_code, 0, 0)
        sock.sendall(packet)
        time.sleep(0.1)
    except Exception as e:
        print(f"Error sending result: {e}")

def handle_client(conn, addr):
    print(f"{bcolors.BLUE}Connected to {addr}{bcolors.ENDC}")
    try:
        conn.settimeout(60.0) 

        # 1. Handshake
        data = conn.recv(1024)
        if len(data) < 38: return
        cookie, mtype, rounds, name_b = struct.unpack("!IbB32s", data[:38])
        if cookie != MAGIC_COOKIE: return
        
        team_name = name_b.decode('utf-8', errors='ignore').strip('\x00')
        print(f"Client {bcolors.CYAN}{team_name}{bcolors.ENDC} wants {rounds} rounds.")

        wins = 0

        # 2. Game Loop
        for r in range(1, rounds + 1):
            print(f"{bcolors.HEADER}Round {r} starting for {team_name}{bcolors.ENDC}")
            
            try:
                # Initialize Game
                current_deck = deck()
                current_player = player(team_name)
                current_dealer = dealer()
                current_game = game(current_dealer, current_player, current_deck)
                current_game.start_round() 
                
                # Deal initial cards
                p_card1 = current_player.hand[0]
                p_card2 = current_player.hand[1]
                d_card1 = current_dealer.hand[0]
                d_card2 = current_dealer.hand[1]

                # Send to client
                send_card(conn, p_card1)
                send_card(conn, p_card2)
                send_card(conn, d_card1) # Dealer shows one card


                # --- Player Turn ---
                player_active = True
                while player_active:
                    # Check for bust immediately
                    if current_player.is_busted():
                        player_active = False
                        break
                    
                    try:
                        data = conn.recv(1024)
                    except socket.timeout:
                        print(f"Client {team_name} timed out.")
                        return

                    if not data: break
                    
                    # Decode move (Expects 10 bytes: Cookie + Type + 5 bytes payload)
                    if len(data) >= 10:
                        _, _, move_b = struct.unpack("!Ib5s", data[:10])
                        move = move_b.decode('utf-8', errors='ignore').strip('\x00').lower()
                    else:
                        move = "stand"

                    print(f"Received move: '{move}'") 

                    # Support both 'hit' and 'hittt' etc.
                    if "hit" in move:
                        new_card = current_deck.deal()
                        current_player.receive_card(new_card)
                        
                        if current_player.is_busted():
                            # Send the card that caused bust, plus LOSS signal
                            send_card(conn, new_card, MSG_LOSS)
                            player_active = False 
                        else:
                            send_card(conn, new_card, MSG_ONGOING)
                    else:
                        # Anything that isn't 'hit' is considered 'stand'
                        player_active = False

                # --- Dealer Turn ---
                # Dealer only plays if player is not busted
                if not current_player.is_busted():
                    send_card(conn, d_card2) # Reveal dealer's second card
                    
                    while current_dealer.should_hit():
                        new_d = current_deck.deal()
                        current_dealer.receive_card(new_d)
                        send_card(conn, new_d)

                    p_val = current_player.calculate_hand_value()
                    d_val = current_dealer.calculate_hand_value()
                    
                    print(f"Results: Player={p_val}, Dealer={d_val}")

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
                
            except Exception as game_err:
                print(f"{bcolors.FAIL}CRASH IN ROUND {r}: {game_err}{bcolors.ENDC}")
                import traceback
                traceback.print_exc() 
                return

        if rounds > 0:
            print(f"Client {team_name} finished. Wins: {wins}")
            
    except Exception as e:
        print(f"{bcolors.FAIL}General Error: {e}{bcolors.ENDC}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        
def get_local_ip():
    """Helper to dynamically get the local LAN IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def udp_broadcast():
    # Dynamically find IP to avoid crashes when IP changes
    MY_IP = get_local_ip()
    BROADCAST_IP = "172.18.255.255" # Keep this, or use '<broadcast>' if supported

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        # Binding to the specific IP is good for filtering interfaces
        sock.bind((MY_IP, 0))
    except Exception as e:
        print(f"Error binding UDP: {e}")
        return

    print(f"{bcolors.GREEN}Server started, listening on IP address {MY_IP}{bcolors.ENDC}")
    
    msg = struct.pack("!IbH32s", MAGIC_COOKIE, OFFER_TYPE, TCP_PORT, SERVER_NAME.encode().ljust(32, b'\x00'))
    
    while True:
        try:
            sock.sendto(msg, (BROADCAST_IP, UDP_PORT))
            time.sleep(1)
        except Exception as e:
            # Silence broadcast errors on shutdown
            time.sleep(1)

if __name__ == "__main__":
    # Start UDP Broadcast in background thread
    t = threading.Thread(target=udp_broadcast, daemon=True)
    t.start()
    
    # Start TCP Server
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.bind(("0.0.0.0", TCP_PORT))
    tcp.listen()
    
    # --- CRITICAL FIX: Set timeout to allow Ctrl+C check ---
    tcp.settimeout(1.0)
    # -------------------------------------------------------

    print(f"TCP server listening on port {TCP_PORT}")
    
    try:
        while True:
            try:
                c, a = tcp.accept()
                threading.Thread(target=handle_client, args=(c, a), daemon=True).start()
            except socket.timeout:
                # Loop back to check for KeyboardInterrupt
                pass
            except Exception as e:
                print(f"Server Error: {e}")
                
    except KeyboardInterrupt:
        print(f"\n{bcolors.WARNING}Server shutting down...{bcolors.ENDC}")
        tcp.close()