from deck import deck
from player import player
from dealer import dealer

# --- Game Class ---
class Game:
    def __init__(self, dealer, player, deck):
        self.dealer = dealer
        self.player = player
        self.deck = deck

    def start_round(self):
        print("\n--- New Round ---")
        self.deck.reset()
        self.deck.shuffle()
        self.player.reset_hand()
        self.dealer.reset_hand()
        
        # Initial Deal
        for _ in range(2):
            self.player.receive_card(self.deck.deal())
            self.dealer.receive_card(self.deck.deal())
            
        # Display Initial State (Crucial for seeing "sum so far")
        print(self.dealer.show_initial_card())
        print(self.player.get_info())

    def player_turn(self):
         while not self.player.is_busted():
            # Check for instant Blackjack (21)
            if self.player.calculate_hand_value() == 21:
                print("You have 21!")
                break

            action = input(f"\n{self.player.get_info()}. Do you want to 'hit' or 'stand'? ").strip().lower()
            
            if action == 'hit':
                card = self.deck.deal()
                if card:
                    self.player.receive_card(card)
                    print(f"You received: {card}")
                    # Ensure busted check happens immediately after receiving card
                    if self.player.is_busted():
                        print(f"You busted with a score of {self.player.calculate_hand_value()}!")
                        break
                else:
                    print("No more cards in the deck!")
                    break
            elif action == 'stand':
                print(f"You chose to stand with a score of {self.player.calculate_hand_value()}.")
                break
            else:
                print("Invalid action. Please choose 'hit' or 'stand'.")
    
    def dealer_turn(self):
        print(f"\n--- Dealer's Turn ---")
        # Reveal full hand first
        print(f"{self.dealer.name}'s full hand: {self.dealer.show_hand()} (Score: {self.dealer.calculate_hand_value()})")
        self.dealer.play_turn(self.deck)
        print(f"{self.dealer.name}'s final score is {self.dealer.calculate_hand_value()}.")
    
    def determine_winner(self):
        print("\n--- Final Result ---")
        p_score = self.player.calculate_hand_value()
        d_score = self.dealer.calculate_hand_value()
        
        if self.player.is_busted():
            return f"{self.dealer.name} wins! {self.player.name} busted."
        elif self.dealer.is_busted():
            return f"{self.player.name} wins! {self.dealer.name} busted."
        elif p_score > d_score:
            return f"{self.player.name} wins with {p_score} against {d_score}!"
        elif p_score < d_score:
            return f"{self.dealer.name} wins with {d_score} against {p_score}!"
        else:
            return "It's a tie!"
        
    def play_game(self):
        self.start_round()
        self.player_turn()
        
        # Only play dealer turn if player didn't bust
        if not self.player.is_busted():
            self.dealer_turn()
            
        result = self.determine_winner()
        print(result)

# --- Execution ---
if __name__ == "__main__":
    # Create instances
    my_deck = deck()
    my_dealer = dealer()
    my_player = player("Alice")
    
    # Start game
    current_game = Game(my_dealer, my_player, my_deck)
    current_game.play_game()