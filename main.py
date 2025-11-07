import pygame
import random
import sys
import math
from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_SPACING = -7  # Negative value for overlapping cards in hand

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (30, 144, 255)
GREEN = (50, 205, 50)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
GOLD = (255, 215, 0)
DARK_BLUE = (25, 25, 112)
PURPLE = (75, 0, 130)

# suit colors
SPADE = BLACK
HEART = (230, 15, 46)
DIAMOND = (255, 39, 7)
CLUB = (5, 31, 0)
STAR = (207, 203, 0)

## keep these lines as they will be refactored later
POTS = ["Side Pot", "Main Pot", "Bomb Pot"]
LEVELS = ["Tulsa", "Dallas", "Macau", ]

CURRENCY_TICKER = ["₱","¥","₪","₩"]



class Suit(Enum):
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    STARS = "X"

class Rank(Enum):
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

@dataclass
class Card:
    suit: Suit
    rank: Rank
    selected: bool = False
    
    def __str__(self):
        rank_str = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(self.rank.value, str(self.rank.value))
        return f"{rank_str}{self.suit.value}"
    
    def get_color(self):
        if self.suit == Suit.STARS:
            return STAR
        return RED if self.suit in [Suit.HEARTS, Suit.DIAMONDS] else BLACK

class HandType(Enum):
    HIGH_CARD = ("High Card", 0)
    PAIR = ("Pair", 1)
    TWO_PAIR = ("Two Pair", 2)
    THREE_OF_A_KIND = ("Three of a Kind", 3)
    STRAIGHT = ("Straight", 4)
    FLUSH = ("Flush", 5)
    FULL_HOUSE = ("Full House", 6)
    FOUR_OF_A_KIND = ("Four of a Kind", 7)
    STRAIGHT_FLUSH = ("Straight Flush", 8)
    ROYAL_FLUSH = ("Royal Flush", 9)
    FIVE_OF_A_KIND = ("Five of a Kind", 10)

class HandEvaluator:
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[HandType, int]:
        
        ranks = [card.rank.value for card in cards]
        suits = [card.suit for card in cards]
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        is_flush = len(set(suits)) == 1
        sorted_ranks = sorted(set(ranks))
        is_straight = False
        
        # Safety check: ensure counts is not empty
        if len(counts) == 0:
            return HandType.HIGH_CARD, 0
        
        # Check for straight
        if len(sorted_ranks) == 5:
            if sorted_ranks[-1] - sorted_ranks[0] == 4:
                is_straight = True
        
        # Royal Flush
        if is_straight and is_flush and len(sorted_ranks) >= 5 and sorted_ranks[-1] == 14 and sorted_ranks[0] == 10:
            return HandType.ROYAL_FLUSH, 9
        
        # Straight Flush
        if is_straight and is_flush:
            return HandType.STRAIGHT_FLUSH, 8
        
        # Five of a Kind (possible with wildcards or special rules)
        if counts[0] == 5:
            return HandType.FIVE_OF_A_KIND, 10
        
        # Four of a Kind
        if counts[0] == 4:
            return HandType.FOUR_OF_A_KIND, 7
        
        # Full House
        if len(counts) >= 2 and counts[0] == 3 and counts[1] == 2:
            return HandType.FULL_HOUSE, 6
        
        # Flush
        if is_flush and len(cards)==5:
            return HandType.FLUSH, 5
        
        # Straight
        if is_straight:
            return HandType.STRAIGHT, 4
        
        # Three of a Kind
        if counts[0] == 3:
            return HandType.THREE_OF_A_KIND, 3
        
        # Two Pair
        if len(counts) >= 2 and counts[0] == 2 and counts[1] == 2:
            return HandType.TWO_PAIR, 2
        
        # Pair
        if counts[0] == 2:
            return HandType.PAIR, 1
        
        # High Card
        return HandType.HIGH_CARD, 0

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Short Deck")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 72)  # Large font for Game Over text
        
        self.deck = []
        self.hand = []
        self.discard_pile = []
        self.score = 0
        self.points = 0
        self.round = 1
        self.hand_type = None
        self.hands_remaining = 5  # Starting hands remaining
        self.base_points_required = 100  # Base points required (increases each round)
        self.points_remaining = 100  # Minimum points required
        self.game_over = False
        
        # Pot and level tracking
        self.pot_index = 0  # Current pot index (0=Side Pot, 1=Main Pot, 2=Bomb Pot)
        self.level_index = 0  # Current level index (0=Tulsa, 1=Dallas, 2=Macau)
        self.spiral_angle = 0.0  # Animation angle for spiral
        
        # Discard limit
        self.max_discards_per_round = 3  # Maximum discards allowed per round
        self.discards_remaining = self.max_discards_per_round  # Current discards remaining
        self.max_hand_size = 8  # Maximum number of cards in hand
        
        # Scoring animation state
        self.scoring_animation = False
        self.animated_cards = []  # List of (card, start_x, start_y, target_x, target_y)
        self.animation_progress = 0.0  # 0.0 to 1.0 for movement
        self.animation_start_time = 0
        self.fade_alpha = 255  # 255 to 0 for fade out
        
        # Round completion animation state
        self.round_complete_animation = False
        self.round_complete_start_time = 0
        self.flying_components = []  # List of component data with positions and velocities
        self.show_round_recap = False
        self.round_complete = False  # Track if round has been completed
        
        # Money system (persists across rounds)
        self.money = 0.0  # Store as float for cents precision
        self.money_earned_this_round = 0.0  # Money earned from completing this round
        self.interest_earned_this_round = 0.0  # Interest earned during round recap
        
        # Shop menu state
        self.show_shop_menu = False
        
        # Sound effects
        try:
            self.sound_potion = pygame.mixer.Sound("res/potion.wav")
            self.sound_coin = pygame.mixer.Sound("res/coin.wav")
            self.sound_warning = pygame.mixer.Sound("res/warning.wav")
            self.sound_game_over = pygame.mixer.Sound("res/dshit.mp3")
        except pygame.error as e:
            print(f"Warning: Could not load sound files: {e}")
            self.sound_potion = None
            self.sound_coin = None
            self.sound_warning = None
            self.sound_game_over = None
        
        # Track coin sound for round recap
        self.round_recap_start_time = None
        self.coin_sound_played = False
        
        self.create_deck()
        self.deal_hand()
    
    def draw_spiral_background(self):
        """Draw a slow-moving animated dark blue and purple spiral background"""
        # Fill with dark background first
        self.screen.fill((15, 15, 30))  # Very dark blue-gray background
        
        # Create a surface for the spiral with alpha for blur effect
        spiral_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Draw multiple overlapping spirals for blur effect
        for layer in range(5):
            layer_alpha = 40 - layer * 6  # Low alpha for subtle blur effect
            layer_angle = self.spiral_angle + layer * 0.3
            
            # Draw spiral with gradient colors using circles for smooth blur
            for i in range(0, 300, 2):  # Step by 2 for performance
                angle = i * 0.08 + layer_angle
                radius = i * 2.0
                
                x = int(center_x + radius * math.cos(angle))
                y = int(center_y + radius * math.sin(angle))
                
                # Keep points within screen bounds
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    # Blend between dark blue and purple based on position
                    blend = (i / 300.0) % 1.0
                    if blend < 0.5:
                        r = int(DARK_BLUE[0] * (1 - blend * 2) + PURPLE[0] * (blend * 2))
                        g = int(DARK_BLUE[1] * (1 - blend * 2) + PURPLE[1] * (blend * 2))
                        b = int(DARK_BLUE[2] * (1 - blend * 2) + PURPLE[2] * (blend * 2))
                    else:
                        r = int(PURPLE[0] * (2 - blend * 2) + DARK_BLUE[0] * ((blend - 0.5) * 2))
                        g = int(PURPLE[1] * (2 - blend * 2) + DARK_BLUE[1] * ((blend - 0.5) * 2))
                        b = int(PURPLE[2] * (2 - blend * 2) + DARK_BLUE[2] * ((blend - 0.5) * 2))
                    
                    color = (r, g, b, layer_alpha)
                    # Draw circles for smooth blur effect
                    size = 10 - layer * 2
                    pygame.draw.circle(spiral_surface, color, (x, y), size)
        
        # Blit the spiral surface onto the main screen
        self.screen.blit(spiral_surface, (0, 0))
        
        # Update animation angle slowly
        self.spiral_angle += 0.0005
    
    def create_deck(self):
        self.deck = [Card(suit, rank) for suit in Suit for rank in Rank]
        random.shuffle(self.deck)
    
    def deal_hand(self, discard_all: bool = False, cards_to_discard: List[Card] = None):
        """
        Deal cards up to max_hand_size.
        If discard_all is True, discard all current cards first (legacy, not used anymore).
        If cards_to_discard is provided, discard only those cards and keep the rest.
        If both are False/None, keep existing cards and only deal new ones (used after playing hand).
        """
        # When discarding specific cards
        if cards_to_discard is not None:
            # Remove selected cards from hand and add to discard pile
            for card in cards_to_discard:
                if card in self.hand:
                    self.hand.remove(card)
                    self.discard_pile.append(card)
        # Legacy: When discarding all (shouldn't be used anymore)
        elif discard_all and len(self.hand) > 0:
            self.discard_pile.extend(self.hand)
            self.hand = []
        
        # Deal cards up to max_hand_size (keeping any existing cards)
        cards_to_deal = min(self.max_hand_size - len(self.hand), len(self.deck))
        for _ in range(cards_to_deal):
            if self.deck:
                self.hand.append(self.deck.pop())
        
        # Reshuffle if needed
        if len(self.deck) < 5:
            self.deck = self.discard_pile.copy()
            self.discard_pile = []
            random.shuffle(self.deck)
    
    def toggle_card_selection(self, index: int):
        if 0 <= index < len(self.hand):
            # Count currently selected cards
            selected_count = sum(1 for card in self.hand if card.selected)
            
            # If trying to select a card and already have 5 selected, don't allow it
            if not self.hand[index].selected and selected_count >= 5:
                return
            
            # Toggle selection
            self.hand[index].selected = not self.hand[index].selected
    
    def calculate_hand_score(self, cards: List[Card]) -> Tuple[Optional[HandType], int]:
        """Calculate the hand type and score for a set of cards"""
        if len(cards) == 0:
            return None, 0
        
        hand_type, hand_value = HandEvaluator.evaluate_hand(cards)
        
        # Calculate points (base score for hand type)
        base_points = {
            HandType.HIGH_CARD: 5,
            HandType.PAIR: 10,
            HandType.TWO_PAIR: 20,
            HandType.THREE_OF_A_KIND: 30,
            HandType.STRAIGHT: 30,
            HandType.FLUSH: 35,
            HandType.FULL_HOUSE: 40,
            HandType.FOUR_OF_A_KIND: 60,
            HandType.STRAIGHT_FLUSH: 100,
            HandType.ROYAL_FLUSH: 100,
            HandType.FIVE_OF_A_KIND: 150,
        }.get(hand_type, 0)
        
        # Add points from card ranks
        for card in cards:
            base_points += max(0, card.rank.value - 10)
        
        return hand_type, base_points
    
    def play_hand(self):
        selected = [card for card in self.hand if card.selected]
        if len(selected) == 0:
            return False
        
        hand_type, score = self.calculate_hand_score(selected)
        self.hand_type = hand_type
        self.points = score
        self.score += self.points
        
        # Deduct the hand score from points_remaining
        self.points_remaining = max(0, self.points_remaining - self.points)
        
        # Check if round is complete (points_remaining <= 0)
        if self.points_remaining <= 0 and not self.round_complete_animation and not self.round_complete:
            self.round_complete = True
            # Award $1 for each remaining hand
            self.money_earned_this_round = float(self.hands_remaining)
            self.money = round(self.money + self.money_earned_this_round, 2)
            self.start_round_complete_animation()
        
        # Decrease hands remaining
        self.hands_remaining -= 1
        
        # Play warning sound if one hands remaining
        if self.hands_remaining == 1:
            if self.sound_warning:
                self.sound_warning.play()
        
        # Check for game over condition
        if self.hands_remaining == 0 and self.score < self.points_remaining:
            self.game_over = True
            # Play game over sound
            if self.sound_game_over:
                self.sound_game_over.play()
        
        # Start scoring animation instead of immediately removing cards
        self.start_scoring_animation(selected)
        
        return True
    
    def start_scoring_animation(self, cards: List[Card]):
        """Start the scoring animation for the played cards"""
        self.scoring_animation = True
        self.animation_progress = 0.0
        self.fade_alpha = 255
        self.animation_start_time = pygame.time.get_ticks()
        self.animated_cards = []
        
        # Calculate starting positions (current card positions in hand)
        hand_start_x = (SCREEN_WIDTH - (len(self.hand) * (CARD_WIDTH + CARD_SPACING) - CARD_SPACING)) // 2
        hand_y = SCREEN_HEIGHT - 200
        
        # Calculate target positions (centered with spacing)
        # Use positive spacing (10) for scoring animation, not the overlapping spacing
        SCORING_CARD_SPACING = 10
        num_cards = len(cards)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * SCORING_CARD_SPACING
        center_start_x = (SCREEN_WIDTH - total_width) // 2
        target_y = SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2
        
        # Find the selected cards in the hand and store their positions
        card_index = 0
        for i, card in enumerate(self.hand):
            if card.selected:
                start_x = hand_start_x + i * (CARD_WIDTH + CARD_SPACING)
                start_y = hand_y
                target_x = center_start_x + card_index * (CARD_WIDTH + SCORING_CARD_SPACING)
                target_y_pos = target_y
                
                self.animated_cards.append((card, start_x, start_y, target_x, target_y_pos))
                card_index += 1
        
        # Remove selected cards from hand (they're now in animation)
        self.hand = [card for card in self.hand if not card.selected]
    
    def start_round_complete_animation(self):
        """Start the round completion animation where all components fly off"""
        self.round_complete_animation = True
        self.round_complete_start_time = pygame.time.get_ticks()
        self.flying_components = []
        
        # Capture all UI component positions and assign random velocities
        # Title
        self.flying_components.append({
            'type': 'text',
            'text': POTS[self.pot_index],
            'font': self.font,
            'color': WHITE,
            'x': 20,
            'y': 20,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Score text
        self.flying_components.append({
            'type': 'text',
            'text': f"Score: {self.score}",
            'font': self.small_font,
            'color': WHITE,
            'x': 20,
            'y': 70,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Points text
        self.flying_components.append({
            'type': 'text',
            'text': f"Points scored last hand: {self.points}",
            'font': self.small_font,
            'color': GOLD,
            'x': 20,
            'y': 100,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Hands remaining
        self.flying_components.append({
            'type': 'text',
            'text': f"Hands Remaining: {self.hands_remaining}",
            'font': self.small_font,
            'color': WHITE,
            'x': 20,
            'y': 190,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Points remaining
        self.flying_components.append({
            'type': 'text',
            'text': f"Points Remaining: {self.points_remaining}",
            'font': self.small_font,
            'color': GREEN,
            'x': 20,
            'y': 220,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Discards remaining
        self.flying_components.append({
            'type': 'text',
            'text': f"Discards Remaining: {self.discards_remaining}",
            'font': self.small_font,
            'color': WHITE,
            'x': 20,
            'y': 250,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Last hand type if available
        if self.hand_type:
            self.flying_components.append({
                'type': 'text',
                'text': f"Last Hand: {self.hand_type.value[0]}",
                'font': self.small_font,
                'color': WHITE,
                'x': 20,
                'y': 280,
                'vx': random.uniform(-800, 800),
                'vy': random.uniform(-800, 800)
            })
        
        # Instructions
        instructions = [
            "Click cards to select them (max 5)",
            "Click 'Play Hand' to score",
            "Click 'Discard' to get new cards"
        ]
        for i, instruction in enumerate(instructions):
            self.flying_components.append({
                'type': 'text',
                'text': instruction,
                'font': self.small_font,
                'color': LIGHT_GRAY,
                'x': SCREEN_WIDTH - 300,
                'y': 70 + i * 30,
                'vx': random.uniform(-800, 800),
                'vy': random.uniform(-800, 800)
            })
        
        # Cards in hand
        hand_start_x = (SCREEN_WIDTH - (len(self.hand) * (CARD_WIDTH + CARD_SPACING) - CARD_SPACING)) // 2
        hand_y = SCREEN_HEIGHT - 200
        
        # Check if there's a hand display text (real-time hand evaluation)
        selected_cards = [card for card in self.hand if card.selected]
        if len(selected_cards) > 0:
            hand_type, hand_score = self.calculate_hand_score(selected_cards)
            if hand_type:
                hand_name = hand_type.value[0]
                hand_display_text = f"{hand_name} - {hand_score}"
                text_x = hand_start_x + (len(self.hand) * (CARD_WIDTH + CARD_SPACING) - CARD_SPACING) // 2
                text_y = hand_y - 40
                self.flying_components.append({
                    'type': 'text',
                    'text': hand_display_text,
                    'font': self.font,
                    'color': GOLD,
                    'x': text_x,
                    'y': text_y,
                    'vx': random.uniform(-800, 800),
                    'vy': random.uniform(-800, 800)
                })
        
        for i, card in enumerate(self.hand):
            card_x = hand_start_x + i * (CARD_WIDTH + CARD_SPACING)
            self.flying_components.append({
                'type': 'card',
                'card': card,
                'x': card_x,
                'y': hand_y,
                'vx': random.uniform(-800, 800),
                'vy': random.uniform(-800, 800)
            })
        
        # Buttons
        play_button_x = SCREEN_WIDTH // 2 - 100
        play_button_y = SCREEN_HEIGHT - 50
        self.flying_components.append({
            'type': 'button',
            'text': "Play Hand",
            'x': play_button_x,
            'y': play_button_y,
            'width': 200,
            'height': 40,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        discard_button_x = SCREEN_WIDTH // 2 + 120
        discard_button_y = SCREEN_HEIGHT - 50
        self.flying_components.append({
            'type': 'button',
            'text': "Discard",
            'x': discard_button_x,
            'y': discard_button_y,
            'width': 200,
            'height': 40,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Deck visualization
        deck_x = SCREEN_WIDTH - CARD_WIDTH - 20
        deck_y = SCREEN_HEIGHT - CARD_HEIGHT - 20
        self.flying_components.append({
            'type': 'deck',
            'x': deck_x,
            'y': deck_y,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
        
        # Deck count text
        deck_count = len(self.deck)
        deck_count_text = f"Deck: {deck_count}"
        self.flying_components.append({
            'type': 'text',
            'text': deck_count_text,
            'font': self.small_font,
            'color': WHITE,
            'x': deck_x - 100,
            'y': deck_y + CARD_HEIGHT // 2 - 10,
            'vx': random.uniform(-800, 800),
            'vy': random.uniform(-800, 800)
        })
    
    def update_round_complete_animation(self):
        """Update the round completion animation"""
        if not self.round_complete_animation:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.round_complete_start_time) / 1000.0  # Convert to seconds
        
        # Update positions of all flying components
        # Use elapsed time for consistent animation speed
        if hasattr(self, '_last_animation_time'):
            dt = (current_time - self._last_animation_time) / 1000.0
        else:
            dt = 1.0 / 60.0
        self._last_animation_time = current_time
        
        for component in self.flying_components:
            component['x'] += component['vx'] * dt
            component['y'] += component['vy'] * dt
        
        # After 1.5 seconds, show round recap
        if elapsed >= 1.5:
            self.round_complete_animation = False
            self.show_round_recap = True
            self.round_recap_start_time = pygame.time.get_ticks()
            self.coin_sound_played = False
            # Calculate and apply 20% interest on current money
            self.interest_earned_this_round = round(self.money * 0.20, 2)
            self.money = round(self.money + self.interest_earned_this_round, 2)
            if hasattr(self, '_last_animation_time'):
                delattr(self, '_last_animation_time')
    
    def update_scoring_animation(self):
        """Update the scoring animation state"""
        if not self.scoring_animation:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.animation_start_time) / 1000.0  # Convert to seconds
        
        # Movement phase: 0.5 seconds to move to center
        if elapsed < 0.5:
            # Smooth easing function (ease-out)
            t = elapsed / 0.5
            self.animation_progress = 1 - (1 - t) ** 3  # Cubic ease-out
        else:
            self.animation_progress = 1.0
        
        # After 2 seconds total, start fading
        if elapsed >= 2.0:
            fade_duration = 0.5  # 0.5 seconds to fade
            fade_progress = min(1.0, (elapsed - 2.0) / fade_duration)
            self.fade_alpha = int(255 * (1 - fade_progress))
            
            # After fade completes, deal next hand
            if elapsed >= 3.5:
                self.scoring_animation = False
                self.deal_hand()
    
    def draw_suit(self, screen: pygame.Surface, suit: Suit, x: int, y: int, size: int):
        """Draw suit symbol as a shape"""
        if suit == Suit.SPADES:
            # Draw spade: triangle + stem
            # Top triangle
            points = [(x + size//2, y), (x, y + size//2), (x + size, y + size//2)]
            pygame.draw.polygon(screen, SPADE, points)
            # Stem
            pygame.draw.rect(screen, SPADE, (x + size//2 - size//10, y + size//2, size//5, size//2))
        elif suit == Suit.HEARTS:
            # Draw heart: two circles + triangle
            pygame.draw.circle(screen, HEART, (x + size//3, y + size//3), size//6)
            pygame.draw.circle(screen, HEART, (x + 2*size//3, y + size//3), size//6)
            points = [(x, y + size//3), (x + size//2, y + size), (x + size, y + size//3)]
            pygame.draw.polygon(screen, HEART, points)
        elif suit == Suit.DIAMONDS:
            # Draw diamond: rotated square
            points = [(x + size//2, y), (x + size, y + size//2), (x + size//2, y + size), (x, y + size//2)]
            pygame.draw.polygon(screen, DIAMOND, points)
        elif suit == Suit.CLUBS:
            # Draw club: three circles + stem
            pygame.draw.circle(screen, CLUB, (x + size//3, y + size//3), size//4)
            pygame.draw.circle(screen, CLUB, (x + 2*size//3, y + size//3), size//4)
            pygame.draw.circle(screen, CLUB, (x + size//2, y+ (size//2*0.1)), size//4)
            pygame.draw.rect(screen, CLUB, (x + size//2 - size//14, y + size//2, size//7, size//3))
        elif suit == Suit.STARS:
            # Draw star: 5-pointed star shape
            center_x = x + size // 2
            center_y = y + size // 2
            outer_radius = size // 2 - 2
            inner_radius = outer_radius // 2
            
            # Calculate points for 5-pointed star
            points = []
            for i in range(10):
                angle = (i * math.pi / 5) - math.pi / 2  # Start from top
                if i % 2 == 0:
                    # Outer point
                    radius = outer_radius
                else:
                    # Inner point
                    radius = inner_radius
                px = center_x + int(radius * math.cos(angle))
                py = center_y + int(radius * math.sin(angle))
                points.append((px, py))
            pygame.draw.polygon(screen, STAR, points)
    
    def draw_card(self, screen: pygame.Surface, card: Card, x: int, y: int, scale: float = 1.0, alpha: int = 255):
        width = int(CARD_WIDTH * scale)
        height = int(CARD_HEIGHT * scale)
        
        # Create a surface for the card if we need alpha
        if alpha < 255:
            card_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            draw_target = card_surface
            offset_x, offset_y = 0, 0
        else:
            draw_target = screen
            offset_x, offset_y = x, y
        
        # Card background
        color = WHITE if not card.selected else GOLD
        border_color = BLACK if not card.selected else RED
        border_width = 2 if not card.selected else 4
        border_radius = 10  # Rounded corners
        
        if alpha < 255:
            # Apply alpha to colors
            color = (*color[:3], alpha) if len(color) == 3 else (*color[:3], min(alpha, color[3]))
            border_color_alpha = (*border_color[:3], alpha) if len(border_color) == 3 else (*border_color[:3], min(alpha, border_color[3]))
            pygame.draw.rect(draw_target, color, (0, 0, width, height), width=0, border_radius=border_radius)
            pygame.draw.rect(draw_target, border_color_alpha, (0, 0, width, height), width=border_width, border_radius=border_radius)
        else:
            pygame.draw.rect(draw_target, color, (offset_x, offset_y, width, height), width=0, border_radius=border_radius)
            pygame.draw.rect(draw_target, border_color, (offset_x, offset_y, width, height), width=border_width, border_radius=border_radius)
        
        # Rank in top-left corner
        rank_text = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(card.rank.value, str(card.rank.value))
        rank_surface = self.font.render(rank_text, True, card.get_color())
        
        if alpha < 255:
            rank_surface.set_alpha(alpha)
            draw_target.blit(rank_surface, (5, 5))
            # Suit in top-left (below rank)
            self.draw_suit(draw_target, card.suit, 5, 25, 20)
            # Large suit symbol in center
            self.draw_suit(draw_target, card.suit, width//2 - 15, height//2 - 15, 30)
            # Rank in bottom-right corner (upside down)
            rank_surface_flipped = pygame.transform.rotate(rank_surface, 180)
            rank_surface_flipped.set_alpha(alpha)
            draw_target.blit(rank_surface_flipped, (width - rank_surface.get_width() - 5, height - rank_surface.get_height() - 5))
            # Suit in bottom-right (upside down)
            suit_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            self.draw_suit(suit_surface, card.suit, 0, 0, 30)
            suit_surface.set_alpha(alpha)
            suit_surface_flipped = pygame.transform.rotate(suit_surface, 180)
            draw_target.blit(suit_surface_flipped, (width - 30 - 5, height - 30 - 25))
            # Blit the card surface to screen
            screen.blit(card_surface, (x, y))
        else:
            draw_target.blit(rank_surface, (offset_x + 5, offset_y + 5))
            # Suit in top-left (below rank)
            self.draw_suit(draw_target, card.suit, offset_x + 5, offset_y + 25, 20)
            # Large suit symbol in center
            self.draw_suit(draw_target, card.suit, offset_x + width//2 - 15, offset_y + height//2 - 15, 30)
            # Rank in bottom-right corner (upside down)
            rank_surface_flipped = pygame.transform.rotate(rank_surface, 180)
            draw_target.blit(rank_surface_flipped, (offset_x + width - rank_surface.get_width() - 5, offset_y + height - rank_surface.get_height() - 5))
            # Suit in bottom-right (upside down)
            suit_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            self.draw_suit(suit_surface, card.suit, 0, 0, 30)
            suit_surface_flipped = pygame.transform.rotate(suit_surface, 180)
            draw_target.blit(suit_surface_flipped, (offset_x + width - 30 - 5, offset_y + height - 30 - 25))
    
    def draw_card_back(self, screen: pygame.Surface, x: int, y: int, scale: float = 1.0):
        """Draw the backside of a card"""
        width = int(CARD_WIDTH * scale)
        height = int(CARD_HEIGHT * scale)
        border_radius = 10  # Rounded corners
        
        # Card back color (dark blue/purple to match theme)
        card_back_color = (40, 20, 60)
        border_color = (80, 40, 120)
        
        # Draw card back
        pygame.draw.rect(screen, card_back_color, (x, y, width, height), width=0, border_radius=border_radius)
        pygame.draw.rect(screen, border_color, (x, y, width, height), width=2, border_radius=border_radius)
        
        # Draw a simple pattern on the back (diamond/star pattern)
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Draw a simple geometric pattern
        pattern_color = (60, 30, 90)
        # Draw a diamond shape
        diamond_points = [
            (center_x, center_y - height // 4),
            (center_x + width // 4, center_y),
            (center_x, center_y + height // 4),
            (center_x - width // 4, center_y)
        ]
        pygame.draw.polygon(screen, pattern_color, diamond_points, width=2)
        
        # Draw small corner decorations
        corner_size = 8
        pygame.draw.circle(screen, pattern_color, (x + corner_size, y + corner_size), 3)
        pygame.draw.circle(screen, pattern_color, (x + width - corner_size, y + corner_size), 3)
        pygame.draw.circle(screen, pattern_color, (x + corner_size, y + height - corner_size), 3)
        pygame.draw.circle(screen, pattern_color, (x + width - corner_size, y + height - corner_size), 3)
    
    def draw_button(self, screen: pygame.Surface, text: str, x: int, y: int, width: int, height: int, enabled: bool = True):
        color = GREEN if enabled else GRAY
        hover_color = (100, 255, 100) if enabled else GRAY
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        is_hovered = x <= mouse_x <= x + width and y <= mouse_y <= y + height
        
        button_color = hover_color if is_hovered and enabled else color
        pygame.draw.rect(screen, button_color, (x, y, width, height))
        pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
        
        text_surface = self.small_font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(text_surface, text_rect)
        
        return is_hovered
    
    def draw_game_over(self):
        """Draw the Game Over screen"""
        # First draw the main game screen (static background when game_over is True)
        self.draw()
        
        # Then add semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text (much bigger)
        game_over_text = self.large_font.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, text_rect)
        
        # Final score
        final_score_text = self.small_font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(final_score_text, score_rect)
        
        # Points required
        required_text = self.small_font.render(f"Points Required: {self.points_remaining}", True, WHITE)
        required_rect = required_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(required_text, required_rect)
        
        # Play Again button
        restart_button_x = SCREEN_WIDTH // 2 - 100
        restart_button_y = SCREEN_HEIGHT // 2 + 50
        self.draw_button(self.screen, "Play Again", restart_button_x, restart_button_y, 200, 40, True)
        
        pygame.display.flip()
    
    def handle_click(self, pos: Tuple[int, int]):
        x, y = pos
        
        # If game over, only handle restart button
        if self.game_over:
            restart_button_x = SCREEN_WIDTH // 2 - 100
            restart_button_y = SCREEN_HEIGHT // 2 + 50
            if restart_button_x <= x <= restart_button_x + 200 and restart_button_y <= y <= restart_button_y + 40:
                self.restart_game()
            return
        
        # Handle shop menu clicks
        if self.show_shop_menu:
            # Shop items
            shop_items = [
                {"name": "Extra Discard", "cost": 5, "description": "Add 1 discard per round"},
                {"name": "Larger Hand", "cost": 10, "description": "Increase max hand size by 1"},
                {"name": "Bonus Points", "cost": 15, "description": "Start with +20 points next round"},
            ]
            
            item_start_y = 180
            item_spacing = 100
            for i, item in enumerate(shop_items):
                item_y = item_start_y + i * item_spacing
                buy_button_x = SCREEN_WIDTH // 2 + 100
                buy_button_y = item_y
                
                # Check buy button clicks
                if buy_button_x <= x <= buy_button_x + 100 and buy_button_y <= y <= buy_button_y + 40:
                    if self.money >= item['cost']:
                        self.money = round(self.money - item['cost'], 2)
                        # Play potion sound when purchasing
                        if self.sound_potion:
                            self.sound_potion.play()
                        # TODO: Apply item effects (for now just deduct money)
                        # In the future, these would modify game state
                        if item['name'] == "Extra Discard":
                            self.max_discards_per_round += 1
                        elif item['name'] == "Larger Hand":
                            self.max_hand_size += 1
                        elif item['name'] == "Bonus Points":
                            # This would be applied at start of next round
                            pass
                    return
            
            # Continue button (to start next round)
            continue_button_x = SCREEN_WIDTH // 2 - 100
            continue_button_y = SCREEN_HEIGHT - 80
            if continue_button_x <= x <= continue_button_x + 200 and continue_button_y <= y <= continue_button_y + 40:
                self.start_next_round()
                return
        
        # Handle round recap clicks
        if self.show_round_recap:
            # Shop button
            shop_button_x = SCREEN_WIDTH // 2 - 100
            shop_button_y = SCREEN_HEIGHT // 2 + 80
            if shop_button_x <= x <= shop_button_x + 200 and shop_button_y <= y <= shop_button_y + 40:
                self.show_shop_menu = True
                return
        
        # Check card clicks
        hand_start_x = (SCREEN_WIDTH - (len(self.hand) * (CARD_WIDTH + CARD_SPACING) - CARD_SPACING)) // 2
        hand_y = SCREEN_HEIGHT - 200
        
        for i, card in enumerate(self.hand):
            card_x = hand_start_x + i * (CARD_WIDTH + CARD_SPACING)
            if card_x <= x <= card_x + CARD_WIDTH and hand_y <= y <= hand_y + CARD_HEIGHT:
                self.toggle_card_selection(i)
                return
        
        # Check Play Hand button
        play_button_x = SCREEN_WIDTH // 2 - 100
        play_button_y = SCREEN_HEIGHT - 50
        if play_button_x <= x <= play_button_x + 200 and play_button_y <= y <= play_button_y + 40:
            self.play_hand()
            return
        
        # Check Discard button
        discard_button_x = SCREEN_WIDTH // 2 + 120
        discard_button_y = SCREEN_HEIGHT - 50
        if discard_button_x <= x <= discard_button_x + 200 and discard_button_y <= y <= discard_button_y + 40:
            if self.discards_remaining > 0:
                # Get selected cards to discard
                selected_to_discard = [card for card in self.hand if card.selected]
                if len(selected_to_discard) > 0:
                    self.discards_remaining -= 1
                    self.deal_hand(cards_to_discard=selected_to_discard)
                    # Clear selection after discarding
                    for card in self.hand:
                        card.selected = False
            return
    
    def draw_round_recap(self):
        """Draw the round recap screen"""
        # Play coin sound 1 second after round recap appears
        if self.round_recap_start_time is not None and not self.coin_sound_played:
            elapsed = (pygame.time.get_ticks() - self.round_recap_start_time) / 1000.0
            if elapsed >= 1.0:
                if self.sound_coin:
                    self.sound_coin.play()
                self.coin_sound_played = True
        
        self.screen.fill((15, 15, 30))  # Dark background
        
        # Round Recap title
        recap_title = self.font.render("ROUND COMPLETE!", True, WHITE)
        title_rect = recap_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        self.screen.blit(recap_title, title_rect)
        
        # Round statistics
        stats_y = SCREEN_HEIGHT // 2 - 70
        stats = [
            f"Final Score: {self.score}",
            f"Hands Remaining: {self.hands_remaining}",
            f"Round: {self.round}",
            f"Money Earned: ${self.money_earned_this_round:.2f}",
        ]
        # Add interest line if interest was earned
        if self.interest_earned_this_round > 0:
            stats.append(f"Interest Earned: ${self.interest_earned_this_round:.2f}")
        stats.append(f"Total Money: ${self.money:.2f}")
        for i, stat in enumerate(stats):
            stat_text = self.small_font.render(stat, True, LIGHT_GRAY)
            stat_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, stats_y + i * 30))
            self.screen.blit(stat_text, stat_rect)
        
        # Shop button
        shop_button_x = SCREEN_WIDTH // 2 - 100
        shop_button_y = SCREEN_HEIGHT // 2 + 80
        self.draw_button(self.screen, "Shop", shop_button_x, shop_button_y, 200, 40, True)
        
        pygame.display.flip()
    
    def draw_shop_menu(self):
        """Draw the shop menu screen"""
        self.screen.fill((15, 15, 30))  # Dark background
        
        # Shop title
        shop_title = self.font.render("SHOP", True, GOLD)
        title_rect = shop_title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(shop_title, title_rect)
        
        # Display current money
        money_text = self.small_font.render(f"Money: ${self.money:.2f}", True, GOLD)
        money_rect = money_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(money_text, money_rect)
        
        # Shop items (placeholder for now)
        shop_items = [
            {"name": "Extra Discard", "cost": 5, "description": "Add 1 discard per round"},
            {"name": "Larger Hand", "cost": 10, "description": "Increase max hand size by 1"},
            {"name": "Bonus Points", "cost": 15, "description": "Start with +20 points next round"},
        ]
        
        # Draw shop items
        item_start_y = 180
        item_spacing = 100
        for i, item in enumerate(shop_items):
            item_y = item_start_y + i * item_spacing
            
            # Item name and cost
            item_text = f"{item['name']} - ${item['cost']:.2f}"
            item_surface = self.small_font.render(item_text, True, WHITE)
            self.screen.blit(item_surface, (SCREEN_WIDTH // 2 - 150, item_y))
            
            # Item description
            desc_surface = self.small_font.render(item['description'], True, LIGHT_GRAY)
            self.screen.blit(desc_surface, (SCREEN_WIDTH // 2 - 150, item_y + 25))
            
            # Buy button
            buy_button_x = SCREEN_WIDTH // 2 + 100
            buy_button_y = item_y
            can_afford = self.money >= item['cost']
            self.draw_button(self.screen, "Buy", buy_button_x, buy_button_y, 100, 40, can_afford)
        
        # Continue button (to start next round)
        continue_button_x = SCREEN_WIDTH // 2 - 100
        continue_button_y = SCREEN_HEIGHT - 80
        self.draw_button(self.screen, "Continue", continue_button_x, continue_button_y, 200, 40, True)
        
        pygame.display.flip()
    
    def start_next_round(self):
        """Start the next round, resetting round-specific variables"""
        self.round += 1
        self.score = 0
        self.points = 0
        self.hand_type = None
        self.hands_remaining = 5
        # Increase difficulty: multiply points required by 1.5x each round
        self.base_points_required = int(self.base_points_required * 1.5)
        self.points_remaining = self.base_points_required
        self.discards_remaining = self.max_discards_per_round
        self.round_complete = False
        self.show_round_recap = False
        self.show_shop_menu = False
        self.money_earned_this_round = 0.0
        self.interest_earned_this_round = 0.0
        self.scoring_animation = False
        self.animated_cards = []
        self.animation_progress = 0.0
        self.animation_start_time = 0
        self.fade_alpha = 255
        self.round_recap_start_time = None
        self.coin_sound_played = False
        
        # Update pot name after each round
        self.pot_index = (self.pot_index + 1) % len(POTS)
        # If pot cycles back to Side Pot (index 0), increase level
        if self.pot_index == 0:
            self.level_index = (self.level_index + 1) % len(LEVELS)
        
        self.create_deck()
        self.deal_hand()
    
    def draw(self):
        # Update animations
        self.update_scoring_animation()
        self.update_round_complete_animation()
        
        # Show shop menu if needed
        if self.show_shop_menu:
            self.draw_shop_menu()
            return
        
        # Show round recap screen if needed
        if self.show_round_recap:
            self.draw_round_recap()
            return
        
        # Don't animate background if game is over
        if not self.game_over:
            # Draw animated spiral background
            self.draw_spiral_background()
        else:
            # Draw static background when game is over
            self.screen.fill((15, 15, 30))
        
        # If round complete animation is active, draw flying components
        if self.round_complete_animation:
            # Draw background
            self.draw_spiral_background()
            
            # Draw all flying components
            for component in self.flying_components:
                if component['type'] == 'text':
                    text_surface = component['font'].render(component['text'], True, component['color'])
                    self.screen.blit(text_surface, (int(component['x']), int(component['y'])))
                elif component['type'] == 'card':
                    self.draw_card(self.screen, component['card'], int(component['x']), int(component['y']))
                elif component['type'] == 'button':
                    self.draw_button(self.screen, component['text'], int(component['x']), int(component['y']), 
                                    component['width'], component['height'], True)
                elif component['type'] == 'deck':
                    self.draw_card_back(self.screen, int(component['x']), int(component['y']))
            
            pygame.display.flip()
            return
        
        # Draw title (pot name and level)
        pot_name = POTS[self.pot_index]
        level_name = LEVELS[self.level_index]
        title_text = f"{pot_name} - {level_name}"
        title = self.font.render(title_text, True, WHITE)
        self.screen.blit(title, (20, 20))
        
        # Draw score info
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 70))
        
        points_text = self.small_font.render(f"Points scored last hand: {self.points}", True, GOLD)
        self.screen.blit(points_text, (20, 100))
        
        # Draw hands remaining and points remaining
        hands_text = self.small_font.render(f"Hands Remaining: {self.hands_remaining}", True, WHITE)
        self.screen.blit(hands_text, (20, 190))
        
        points_remaining_text = self.small_font.render(f"Points Remaining: {self.points_remaining}", True, RED if self.score < self.points_remaining else GREEN)
        self.screen.blit(points_remaining_text, (20, 220))
        
        # Draw discards remaining
        discards_text = self.small_font.render(f"Discards Remaining: {self.discards_remaining}", True, WHITE)
        self.screen.blit(discards_text, (20, 250))
        
        # Draw hand type if available
        if self.hand_type:
            hand_type_text = self.small_font.render(f"Last Hand: {self.hand_type.value[0]}", True, WHITE)
            self.screen.blit(hand_type_text, (20, 280))
        
        # Draw instructions
        instructions = [
            "Click cards to select them (max 5)",
            "Click 'Play Hand' to score",
            "Click 'Discard' to get new cards"
        ]
        for i, instruction in enumerate(instructions):
            inst_text = self.small_font.render(instruction, True, LIGHT_GRAY)
            self.screen.blit(inst_text, (SCREEN_WIDTH - 300, 70 + i * 30))
        
        # Draw animated cards if in scoring animation
        if self.scoring_animation:
            for card, start_x, start_y, target_x, target_y in self.animated_cards:
                # Interpolate position based on animation progress
                current_x = int(start_x + (target_x - start_x) * self.animation_progress)
                current_y = int(start_y + (target_y - start_y) * self.animation_progress)
                self.draw_card(self.screen, card, current_x, current_y, alpha=self.fade_alpha)
        else:
            # Draw hand normally
            hand_start_x = (SCREEN_WIDTH - (len(self.hand) * (CARD_WIDTH + CARD_SPACING) - CARD_SPACING)) // 2
            hand_y = SCREEN_HEIGHT - 200
            
            # Evaluate and display selected hand in real-time
            selected_cards = [card for card in self.hand if card.selected]
            if len(selected_cards) > 0:
                hand_type, hand_score = self.calculate_hand_score(selected_cards)
                if hand_type:
                    # Display hand name and score above the hand
                    hand_name = hand_type.value[0]
                    hand_display_text = f"{hand_name} - {hand_score}"
                    hand_text_surface = self.font.render(hand_display_text, True, GOLD)
                    text_x = hand_start_x + (len(self.hand) * (CARD_WIDTH + CARD_SPACING) - CARD_SPACING) // 2 - hand_text_surface.get_width() // 2
                    text_y = hand_y - 40
                    self.screen.blit(hand_text_surface, (text_x, text_y))
            
            for i, card in enumerate(self.hand):
                card_x = hand_start_x + i * (CARD_WIDTH + CARD_SPACING)
                self.draw_card(self.screen, card, card_x, hand_y)
        
        # Draw buttons (disabled during animation)
        selected_count = sum(1 for card in self.hand if card.selected)
        can_play = selected_count > 0 and selected_count <= 5 and not self.scoring_animation
        
        play_button_x = SCREEN_WIDTH // 2 - 100
        play_button_y = SCREEN_HEIGHT - 50
        self.draw_button(self.screen, "Play Hand", play_button_x, play_button_y, 200, 40, can_play)
        
        discard_button_x = SCREEN_WIDTH // 2 + 120
        discard_button_y = SCREEN_HEIGHT - 50
        # Enable discard button if there are selected cards and discards remaining
        can_discard = not self.scoring_animation and self.discards_remaining > 0 and selected_count > 0
        self.draw_button(self.screen, "Discard", discard_button_x, discard_button_y, 200, 40, can_discard)
        
        # Draw deck visualization in bottom right
        deck_x = SCREEN_WIDTH - CARD_WIDTH - 20
        deck_y = SCREEN_HEIGHT - CARD_HEIGHT - 20
        self.draw_card_back(self.screen, deck_x, deck_y)
        
        # Draw deck count next to the deck
        deck_count = len(self.deck)
        deck_count_text = self.small_font.render(f"Deck: {deck_count}", True, WHITE)
        self.screen.blit(deck_count_text, (deck_x - 100, deck_y + CARD_HEIGHT // 2 - 10))
        
        pygame.display.flip()
    
    def restart_game(self):
        """Reset the game to initial state (including money)"""
        self.round = 1
        self.round_complete = False
        self.deck = []
        self.hand = []
        self.discard_pile = []
        self.score = 0
        self.points = 0
        self.hand_type = None
        self.hands_remaining = 5
        self.base_points_required = 100  # Reset to base value
        self.points_remaining = 100
        self.game_over = False
        self.pot_index = 0  # Reset to Side Pot
        self.level_index = 0  # Reset to Tulsa
        self.spiral_angle = 0.0
        self.max_discards_per_round = 3
        self.max_hand_size = 8
        self.discards_remaining = self.max_discards_per_round
        self.scoring_animation = False
        self.animated_cards = []
        self.animation_progress = 0.0
        self.animation_start_time = 0
        self.fade_alpha = 255
        self.money = 0.0  # Reset money on full game restart
        self.money_earned_this_round = 0.0
        self.interest_earned_this_round = 0.0
        self.show_round_recap = False
        self.show_shop_menu = False
        self.round_recap_start_time = None
        self.coin_sound_played = False
        
        self.create_deck()
        self.deal_hand()
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_0:
                        # Immediately terminate the program
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos)
            
            if self.game_over:
                self.draw_game_over()
            else:
                self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

