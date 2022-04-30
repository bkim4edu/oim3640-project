from flask import Flask, render_template, redirect, request
import random
app = Flask(__name__)

class card:
    def __init__(self, value, color, cardset):
        self.value = value
        self.color = color
        self.cardset = cardset
        if value == 1:
            self.truevalue = 11
        elif value > 10:
            self.truevalue = 10
        else:
            self.truevalue = value

def carddeck(): # creating playing deck of cards
    colors = ['D', 'H', 'C', 'S'] # diamonds, hearts, clubs, spades
    carddeck = []
    for sets in range(4): #4 cardsets
        for col in colors:
            for val in range(13):
                createdcard = card((val + 1), col, (sets + 1))
                carddeck.append(createdcard)
    random.shuffle(carddeck)
    return carddeck

class dealer:
    def __init__(self):
        self.name = 'Dealer'
        self.hand = []
        self.handvalue = 0
        self.chips = 0

    def drawcard(self, card): #adds card to the player
        self.hand.append(card)
        acecount = 0
        self.handvalue = 0
        for x in range(len(self.hand)):
            cardvalue = self.hand[x].truevalue
            if cardvalue == 11:
                acecount += 1
            self.handvalue += cardvalue
            if self.handvalue > 21 and acecount > 0:
                while acecount > 0:
                    self.handvalue -= 10
                    acecount -= 1

    def paramReset(self):
        self.hand = []
        self.handvalue = 0
        self.bet = 0

def check_winner_after_deal(user, dealer):
    # if user has blackjack with two cards
    if user.handvalue == 21:
        # player ties blackjacks with dealer
        if dealer.handvalue == 21:
            user.wins(False, True)
            return 'tied'
        # player wins with a blackjack
        else:
            user.wins(True)
            return 'blackjack'
    elif dealer.handvalue == 21:
        return 'dealerblackjack'
    else:
        return 'no'

def check_winner(user, dealer):
    if dealer.handvalue > 21:
        user.wins()
        return 'toomuchdealer'
    elif dealer.handvalue == user.handvalue:
        user.wins(False, True)
        return 'tied'
    elif dealer.handvalue < user.handvalue:
        user.wins()
        return 'user'
    elif dealer.handvalue > user.handvalue:
        return 'dealer'

# calculate chips to be displayed
def chips_calculate(chips, bet):
    while bet > 0:
        for x in [10, 5, 1]:
            if x <= bet:
                chips.append(x)
                bet -= x
                break
    return

class player(dealer):
    def __init__(self, name = 'no_name', chips = 10):
        dealer.__init__(self)
        self.name = name
        self.chips = float(chips)

    def set_bet(self, bet, double = False):
        if double is False:
            self.bet = bet
            self.chips -= bet
        if double is True:
            self.bet *= 2
            self.chips -= bet

    def wins(self, blackjack = False, tie = False): #blackjack parameter for chips calculation
        if blackjack is True:
            self.chips += self.bet * 2.5
        elif tie is True:
            self.chips += self.bet
        else:
            self.chips += self.bet * 2
# global variables
bet = 0
# player's chip count, set at index.html 
chips = 5
# name placeholder (if someone accesses /game directly)
name = 'Brandon Kim'
winner = ''

# possible actions for player as dict
actions = {
    'card':False,
    'hold':False,
    'double':False,
}

# list of chips to be displayed
chips_display = []

user = player()
dealer = dealer()
deck = carddeck()

@app.route('/', methods = ['GET', 'POST'])
    # starting application / opening page
def index():
    # start game and get name & chips amount
    if request.method == 'POST':
        # modifiy global variables and redirect to the game
        global name, chips
        name = request.form.get('name')
        chips = float(request.form.get('chips'))
        return redirect('/game')
    else:
        return render_template('index.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    #get access to global actions-dict
    global actions, user, dealer, deck, bet, winner, chips_display
    # render game and ask for bet
    if request.method == 'GET':
        # create deck and update properties incl. deleting cards in hand, game options
        global name, chips
        user.name = name
        user.chips = chips
        chips_display = []
        user.paramReset()
        dealer.paramReset()
        actions['card'] = False
        actions['hold'] = False
        actions['double'] = False
        return render_template('game.html', chips = chips_display, user = user, actions = actions, dealer = dealer)
    
    else:
        try:
            # set user's bet
            bet = int(request.form.get('bet'))
            user.set_bet(bet)
            # calculate chips to be displayed
            chips_calculate(chips_display, bet)
            # draw first two cards for user and dealer
            for x in range(2):
                user.drawcard(deck[-1])
                deck.pop()
                dealer.drawcard(deck[-1])
                deck.pop()

            # check if any of players has won
            winner = check_winner_after_deal(user, dealer)
            if winner != 'no':
                return redirect('/gameresult')

            # choose which actions are available for player
            actions['card'] = True
            actions['hold'] = True
            actions['double'] = True
            
            return render_template('game.html', chips = chips_display, user = user, actions = actions, dealer = dealer)
        
        # if bet has not been posted, instead user has requested another card
        except:
            user.drawcard(deck[-1])
            deck.pop()
            actions['double'] = False
            if user.handvalue > 21:
                winner = 'toomuchuser'
                return redirect('/gameresult')
            else:
                return render_template('game.html', chips = chips_display, user = user, actions = actions, dealer = dealer)


@app.route('/hold', methods = ['GET', 'POST'])
def hold():
    global user, dealer, winner
    # blackjack rules - dealer draws when < 17
    while dealer.handvalue < 17:
        dealer.drawcard(deck[-1])
        deck.pop()
    # when dealer > 18, check winner
    winner = check_winner(user, dealer)
    return redirect('/gameresult')
    

@app.route('/double', methods = ['GET', 'POST'])
def double():
    global user, bet, winner
    user.drawcard(deck[-1])
    deck.pop()
    #double bet amount
    user.set_bet(bet, True)
    if user.handvalue > 21:
        winner = 'toomuchuser'
        return redirect('/gameresult')
    # if user is < 21 then dealer needs to draw his cards
    else:
        return redirect('/hold')

@app.route('/gameresult', methods = ['GET', 'POST'])
def gameresult():
    global user, dealer, bet, chips, winner, chips_display
    # update user chips to chips after game has ended
    chips = user.chips
    return render_template('gameresult.html', chips = chips_display, winner = winner, bet = bet, user = user, dealer = dealer)

app.run(debug=True) 