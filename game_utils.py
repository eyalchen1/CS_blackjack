import random

# --- Colors Helper ---
class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m' # Yellow
    FAIL = '\033[91m'    # Red
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        
    def __repr__(self):
        # Colorize suits: Hearts/Diamonds = Red, Spades/Clubs = Cyan
        if self.suit in ['Hearts', 'Diamonds']:
            color = bcolors.FAIL
        else:
            color = bcolors.CYAN
            
        # Example: "10 of [Red]Hearts[Reset]"
        return f"{self.rank} of {color}{self.suit}{bcolors.ENDC}"
    
    def value(self):
        if self.rank in ['Jack', 'Queen', 'King']:
            return 10
        elif self.rank == 'Ace':
            return 11
        else:
            return int(self.rank)

class deck:
    def __init__(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        self.cards = [card(rank, suit) for suit in suits for rank in ranks]

    def __repr__(self):
        return f"Deck of {len(self.cards)} cards"
    
    def shuffle(self):
        random.shuffle(self.cards)  
    
    def deal(self):
        return self.cards.pop() if self.cards else None
    
    def reset(self):
        self.__init__() # Reinitialize the deck
        
    def count(self):
        return len(self.cards)
    
    def is_empty(self):
        return len(self.cards) == 0
    
    def peek(self):
        return self.cards[-1] if self.cards else None   
    
    def add_card(self, card):
        self.cards.append(card)

class player:
    def __init__(self, name):
        self.name = name
        self.hand = []

    def get_info(self):
        return f"Player: {self.name}, Score: {self.calculate_hand_value()}, Cards: {self.show_hand()}"
    
    def receive_card(self, card):
        self.hand.append(card)
    
    def is_busted(self):
        score = self.calculate_hand_value()
        return score > 21
    
    def get_total_cards(self):
        return len(self.hand)
    
    def show_hand(self):
        return ', '.join(str(card) for card in self.hand)
    
    def reset_hand(self):
        self.hand = []
    
    def calculate_hand_value(self):
        total = 0
        aces = 0
        for card in self.hand:
            val = card.value()
            total += val
            if card.rank == 'Ace':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

class dealer(player):
    def __init__(self, name="Dealer"):
        super().__init__(name)

    def show_initial_card(self):
        if self.hand:
            return f"{self.name} shows: {self.hand[0]}"
        return f"{self.name} has no cards to show."
    
    def should_hit(self):
        return self.calculate_hand_value() < 17
    
    def play_turn(self, deck):
        while self.should_hit():
            card = deck.deal()
            if card:
                self.receive_card(card)
            else:
                break

class game:
    def __init__(self, dealer, player, deck):
        self.dealer = dealer
        self.player = player
        self.deck = deck

    def start_round(self):
        self.deck.reset()
        self.deck.shuffle()
        self.player.reset_hand()
        self.dealer.reset_hand()
        
        for _ in range(2):
                self.player.receive_card(self.deck.deal())
                self.dealer.receive_card(self.deck.deal())
        
    def player_turn(self, action=None):
         while(not self.player.is_busted()):
            action = input(f"{self.player.get_info()}. Do you want to 'hit' or 'stand'? ").strip().lower()
            print(action)
            if action == 'hit':
                card = self.deck.deal()
                if card:
                    self.player.receive_card(card)
                    print(f"You received: {card}. Your total score is now {self.player.calculate_hand_value()}.")
                else:
                    print("No more cards in the deck!")
                    break
            elif action == 'stand':
                print(f"You chose to stand with a score of {self.player.calculate_hand_value()}.")
                break
            else:
                print("Invalid action. Please choose 'hit' or 'stand'.")
            if self.player.is_busted():
                print(f"You busted with a score of {self.player.calculate_hand_value()}!")
    
    def dealer_turn(self):
        print(self.dealer.show_initial_card())
        self.dealer.play_turn(self.deck)
        print(f"{self.dealer.name}'s final score is {self.dealer.calculate_hand_value()}.")
    
    def determine_winner(self):
        if self.player.is_busted():
            return f"{bcolors.FAIL}{self.dealer.name} wins! {self.player.name} busted.{bcolors.ENDC}"
        elif self.dealer.is_busted():
            return f"{bcolors.GREEN}{self.player.name} wins! {self.dealer.name} busted.{bcolors.ENDC}"
        elif self.player.calculate_hand_value() > self.dealer.calculate_hand_value():
            return f"{bcolors.GREEN}{self.player.name} wins with {self.player.calculate_hand_value()} vs {self.dealer.calculate_hand_value()}!{bcolors.ENDC}"
        elif self.player.calculate_hand_value() < self.dealer.calculate_hand_value():
            return f"{bcolors.FAIL}{self.dealer.name} wins with {self.dealer.calculate_hand_value()} vs {self.player.calculate_hand_value()}!{bcolors.ENDC}"
        else:
            return f"{bcolors.WARNING}It's a tie!{bcolors.ENDC}"
        
    def play_game(self):
        self.start_round()
        self.player_turn()
        if not self.player.is_busted():
            self.dealer_turn()
        result = self.determine_winner()
        print(result)