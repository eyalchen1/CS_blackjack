class card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        
    def __repr__(self):
        return f"{self.rank} of {self.suit}"
    
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
        import random
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
        