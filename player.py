class Player:
    def __init__(self, name, score=0):
        self.name = name
        self.score = score
        self.hand = []

    def update_score(self, points):
        self.score += points

    def get_info(self):
        return f"Player: {self.name}, Score: {self.score}"
    
    def receive_card(self, card):
        self.update_score(card.value())
        self.hand.append(card)
    
    def is_busted(self):
        return self.score > 21
    
    def get_total_cards(self):
        return len(self.hand)
    
    def show_hand(self):
        return ', '.join(str(card) for card in self.hand)
    
    def reset_hand(self):
        self.hand = []
        self.score = 0
