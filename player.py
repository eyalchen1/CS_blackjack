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
