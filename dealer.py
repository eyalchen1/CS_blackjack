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
