import re
import random 
import matplotlib.pyplot as plt
import pandas as pd
import util

with open('words') as f:
    wordbank = f.read().splitlines()

random.seed(0)
wordbank_mini = random.sample(wordbank, 50)

def letters(words):
    letters_dict = {'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 
                    'f': 0, 'g': 0, 'h': 0, 'i': 0, 'j': 0, 
                    'k': 0, 'l': 0, 'm': 0, 'n': 0, 'o': 0, 
                    'p': 0, 'q': 0, 'r': 0, 's': 0, 't': 0, 
                    'u': 0, 'v': 0, 'w': 0, 'x': 0, 'y': 0, 
                    'z': 0}


    df = pd.DataFrame.from_dict(letters_dict, orient='index', columns=['Score'])

    for word in words:
        for letter in word:
            df.loc[letter, 'Score'] = df.loc[letter, 'Score'] + 1

    normalized_df = (df-df.mean())/df.std()

    return normalized_df

# set global variables
best_letters = letters(wordbank)
word_info = {}
epsilon = .5
alpha = 1
gamma = .99 
qvals = util.Counter()

def user_play(goal, words):
    # print(goal)
    # user enters a word
    guesses = 1 
    guess = input("Enter word: ") 
    win = False

    # until they run out of guesses or guess the correct word
    while not win and guesses < 6:

        information, guess = inform(goal, guess.lower())
        
        if information == "Correct":
            print('Correct!!')
            print(goal)
            win = True

        elif information != "Invalid guess":
            print(information)
            random_agent(words, guess, information)
            guess = input("Enter word for guess #{0}: ".format(guesses+1))
            guesses += 1

    print(goal)

def inform(goal, guess):
    '''
    Evaluates if the word is a valid guess. Will be valid for all agent play.
    Returns an info string (ex. 'GYXXY') and the original guess
    '''
    # improper word
    if len(guess) != 5:
        print("Invalid guess")
        return "Invalid guess", input("Enter new word: ")

    # not a valid 5-letter word
    if guess not in wordbank:
        print("Invalid guess")
        return "Invalid guess", input("Enter new word: ")

    if len(guess) != 5:
        print("Invalid guess")
        return 'Invalid guess', input("Enter new word: ")

    if goal == guess:
        return 'Correct', goal

    else:
        info = evaluate(goal, guess)
        return info, guess

def evaluate(goal, guess):
    '''
    Compares a player's guess to the goal word in order to determine the correct information string (ex. 'GYXXY')
    '''
    colors = [[guess[i], '0'] for i in range(len(goal))]

    yellow = {}
    yellow_goal = {}
    for i in range(len(guess)):
        letter = guess[i]
        if letter not in goal:
            colors[i][1] = 'X'
        if letter == goal[i]:
            colors[i][1] = 'G'
        elif letter in goal: # if the letter is in the goal
            if letter not in yellow:
                yellow[letter] = [i]
            else:
                yellow[letter].append(i)

    # handle double letters
    for letter in yellow:
        goal_loc = []
        for i in range(len(goal)):
            if goal[i] == letter:
                goal_loc.append(i)
        yellow_goal[letter] = goal_loc

        for i in yellow_goal[letter]:
            j = 0
            if i in yellow[letter]:

                colors[i][1] = 'G' 
            elif len(yellow[letter]) > 0:
                loc = yellow[letter].pop(0)
                colors[loc][1] = 'Y'

    for i in range(len(colors)):
        if colors[i][1] == '0':
            colors[i][1] = 'X'
    return  "".join([str(colors[i][1]) for i in range(len(colors))])

def random_agent(words, guess, info):
    possible_words = prune(words, guess, info)

    return random.choice(possible_words), possible_words

def prune(words, guess, info):
    yellows = []
    green_loc = {}
    grays = []
    # build a regex pattern that checks for gray and green letter
    regex_pattern = '^'
    for i, char in enumerate(info):
        if char == 'G':
            regex_pattern += guess[i] # has to have the letter at this point
            green_loc[char] = i
        else: 
            regex_pattern += f'[^{guess[i]}]' #  cannot have the letter here
            if char == 'Y':
                yellows.append(guess[i])
            else:
                grays.append(guess[i])
    regex_pattern += '$'

    possible_words = [w for w in words if re.match(regex_pattern, w)]

    possible_words2 = []
    for i, word in enumerate(possible_words):
        add_word = True
        for letter in word:
            if letter in grays or check_yellow(word, yellows, green_loc) != 0:
                add = False # remove words with grays; if not all the yellow letters appear elsewhere in the word, remove from list
        if add_word:
            possible_words2.append(word)
    return possible_words2

def agent_play(goal, words):
    guesses = 1 
    guess = random.choice(wordbank) # agent picks a random word to start
    win = False

    # until they guess the correct word
    while not win:

        information, guess = inform(goal, guess)
        if information == "Correct":
            win = True

        elif information != "Invalid guess":
            guess, words = random_agent(words, guess, information)
            guesses += 1

    return guesses

def check_yellow(word, yellow, green_loc): # just needs to be in a spot other than where it is green
    possible = {}
    for letter in yellow:
        possible[letter] = 1
    for i, letter in enumerate(word):
        if letter in possible:
            if letter in green_loc:
                    if i != green_loc[letter]: 
                        possible[letter] = 0
            else: # exists in a spot that is not the green 
                possible[letter] = 0

    return sum(possible.values()) # return if all the yellow letters appear in the word somewhere other than the green spots, 0 means they do

def elimination_word(words, letters_considered):
    scores = util.Counter()
    
    for word in words:
        for letter in word:
            if letter not in letters_considered:
                scores[word] += 1

    return max(scores, key = scores.get)

def commonsense_agent(words, guess, info, guess_number):
    letters_considered = ['s', 'a', 'l', 'e', 't']
    letters_considered.extend([char for char in guess])

    if guess_number == 1:
        return 'minor' # uses i,o, r (next three most common letters)

    if guess_number in (2, 3):
        scores = {}
        # print(words)
        words = prune(words, guess, info)
        # create a list of words with variety of vowels and letters , randomly choose among them (or choose one with the most frequent letters)
        for word in words: # incentivize vowels and different letters , not duplicates
            scores[word] = 0
            letters = []
            for letter in word:
                if letter in letters:
                    scores[word] -= 1
                if letter in 'aeiouy' and letter not in letters_considered:
                    scores[word] += 1
                else:
                    scores[word] += best_letters.loc[letter, 'Score']
                letters.append(letter)
        return max(scores, key = scores.get)

    elif guess_number == 4 and len(words) > 100: # if there is are a of words left at step 4, eliminate a lot of letters 
        return elimination_word(words, letters_considered)

    else:
        return random.choice(words)
    

def agent_play2(goal, words):
    guesses = 1 
    guess = 'salet' 
    win = False

    # until they guess the correct word
    while not win:
        information, guess = inform(goal, guess)
        if information == "Correct":
            win = True
            return guesses

        elif information != "Invalid guess":
            words = prune(words, guess, information)
            guess = commonsense_agent(words, guess, information, guesses)
            guesses += 1
    
    return guesses

def test_random_agent(words):
    guesses_til_win = []
    for i in range(10000):
        print(i)
        # randomly select a word from the list
        goal =random.choice(words)
        
        guesses_til_win.append(agent_play(goal, words))

    print('Average Guesses for Random Agent:', sum(guesses_til_win)/len(guesses_til_win))

    plt.hist(guesses_til_win, bins=range(min(guesses_til_win), max(guesses_til_win) + 1, 1))
    plt.axvline(x=6, linestyle = '--', color = 'red')
    plt.axvline(x=(sum(guesses_til_win) / len(guesses_til_win)), linestyle = '-', color = 'gray')
    plt.xlabel('Number of Guesses Until Correct')
    plt.ylabel('Frequency')
    plt.title('10000 Random Agent Wordle Games')
    plt.show() 

def test_commonsense_agent():
    guesses_til_win = []

    for i in range(10000):
        print(i)
        # randomly select a word from the list
        goal = random.choice(wordbank)
        guesses_til = agent_play2(goal, wordbank)
        guesses_til_win.append(guesses_til)

    print('Average Guesses for Common Sense Agent:', sum(guesses_til_win)/len(guesses_til_win))

    plt.hist(guesses_til_win, bins=range(min(guesses_til_win), max(guesses_til_win) + 1, 1))
    plt.axvline(x=6, linestyle = '--', color = 'red')
    plt.axvline(x=(sum(guesses_til_win) / len(guesses_til_win)), linestyle = '-', color = 'gray') # average guesses til win 
    plt.xlabel('Number of Guesses Until Correct')
    plt.ylabel('Frequency')
    plt.title('10000 Common Sense Agent Wordle Games')
    plt.show()

def reward(info):
    # score a word based on the number of greens
    # +1 for all greens
    score = 0
    for character in info:
        if character == 'G':
            score += 1
    return score

def computeAction(guess, info): # there are 50*243*50 combinations
    possible_actions = {}
    if info == 'GGGGG':
        return None
    for next_word in prune(wordbank_mini, guess, info):
        possible_actions[next_word] = qvals[(guess, info), next_word]
    return max(possible_actions) # returns best next word

def epsilon_greedy(guess, info):
    if util.flipCoin(epsilon):
        word = random.choice(wordbank_mini)
    else:
        word = computeAction(guess, info)
    return word

def qlearn():
    guesses_til_win = []
    iter = []
    for i in range(10000):
        goal = random.choice(wordbank_mini)
        guesses = 1
        if i == 0:
            guess = random.choice(wordbank_mini)
        info = evaluate(goal, guess)
        while info != 'GGGGG':
            prev_guess = guess
            prev_info = info
            guess = epsilon_greedy(prev_guess, prev_info) # choose a from s using epsilon greedy policy, get Action
            guesses += 1

            info = evaluate(goal, guess) 
            if info == 'GGGGG':
                guesses_til_win.append(guesses)
                iter.append(i)

            r = reward(info)
            if guesses == 6:
                r = r - 100
            if r == 5:
                r = 100
            q_prev = qvals[(prev_guess, prev_info), guess]
            best_action = epsilon_greedy(guess, info)
            q_next = qvals[(guess, info), best_action]

            qvals[(guess, info), best_action] = q_prev + (alpha*(r + gamma*q_next - q_prev))

    print('Average Guesses for Q-Learning Agent', sum(guesses_til_win)/len(guesses_til_win))

    # sorted_qvals = sorted(qvals.items(), key = lambda x: x[1], reverse = True)

    # # print the top 3 highest values
    # for key, value in sorted_qvals[:15]:
    #     print(key, value)

    # for key, value in sorted_qvals[-15:]:
    #     print(key, value)

    plt.hist(guesses_til_win)
    plt.axvline(x=6, linestyle = '--', color = 'red')
    plt.axvline(x=(sum(guesses_til_win) / len(guesses_til_win)), linestyle = '-', color = 'pink') # average guesses til win 
    plt.xlabel('Number of Guesses Until Correct')
    plt.ylabel('Frequency')
    plt.title('10000 Q-Learning Agent Wordle Games')
    plt.show()

    plt.scatter(iter, guesses_til_win)
    plt.xlabel('Iterations')
    plt.ylabel('Guesses Until Correct')
    plt.title('10000 Q-Learning Agent Wordle Games')
    plt.show()


def main():
    # evaluate the most frequent letters in the dataset
    print('Word bank length:', len(wordbank))
    for w in sorted(best_letters, key=best_letters.get):
        print(w, best_letters[w])

    random.seed(0)
    print('---------- Test Random Agent ----------')
    test_random_agent(wordbank) # success on a small wordbank

    random.seed(0)
    print('---------- Test Common Sense Agent ----------')
    test_commonsense_agent()

    random.seed(0)
    print('---------- Test Random Agent (Wordbank Mini) ----------')
    test_random_agent(wordbank_mini)

    print('---------- Test Q-Learning Agent (Wordbank Mini) ----------')
    random.seed(0)
    qlearn()
    
    sorted_qvals = sorted(qvals.items(), key=lambda x: x[1], reverse=True)

    for key, value in sorted_qvals[:60]:
        print(key, value)






main()