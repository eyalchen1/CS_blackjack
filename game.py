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
        
    def player_turn(self,action=None):
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
            return f"{self.dealer.name} wins! {self.player.name} busted."
        elif self.dealer.is_busted():
            return f"{self.player.name} wins! {self.dealer.name} busted."
        elif self.player.calculate_hand_value() > self.dealer.calculate_hand_value():
            return f"{self.player.name} wins with a score of {self.player.calculate_hand_value()} against {self.dealer.calculate_hand_value()}!"
        elif self.player.calculate_hand_value() < self.dealer.calculate_hand_value():
            return f"{self.dealer.name} wins with a score of {self.dealer.calculate_hand_value()} against {self.player.calculate_hand_value()}!"
        else:
            return "It's a tie!"
        
    def play_game(self):
        self.start_round()
        self.player_turn()
        if not self.player.is_busted():
            self.dealer_turn()
        result = self.determine_winner()
        print(result)
    
