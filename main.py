from deck import deck
from deck import card
from player import player
from dealer import dealer
from game import game


def main():
    # יצירת מרכיבי המשחק
    deck_obj = deck()  # Deck
    player_obj = player("Alice")
    dealer_obj = dealer()

    # יצירת משחק
    game_obj = game(dealer_obj, player_obj, deck_obj)

    # לולאת משחק
    while True:
        print("\n=== Starting a new round ===\n")
        game_obj.play_game()  # כל הסיבוב כולל Hit/Stand + Dealer + Winner

        again = input("\nDo you want to play again? (y/n) ").strip().lower()
        if again != 'y':
            print("Thanks for playing! Goodbye.")
            break

if __name__ == "__main__":
    main()
