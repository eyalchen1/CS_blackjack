from deck import deck
from deck import card
from player import player
from dealer import dealer
from game import game


def main():
    deck_obj = deck()  # Deck
    player_obj = player("Alice")
    dealer_obj = dealer()

    game_obj = game(dealer_obj, player_obj, deck_obj)

    while True:
        print("\n=== Starting a new round ===\n")
        game_obj.play_game()
        again = input("\nDo you want to play again? (y/n) ").strip().lower()
        if again != 'y':
            print("Thanks for playing! Goodbye.")
            break

if __name__ == "__main__":
    main()
