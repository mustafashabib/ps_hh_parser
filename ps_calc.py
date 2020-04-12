#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import getopt
import csv
import re
import os
from itertools import groupby

# keep track of player's total winnings/losses/rake share
player_details = {}
init_pd_keys = ['num_wins', 'num_all_in_wins', 'num_all_in', 'rake', 'win', 'expense']
hands_seen = set()

# helpers to add to the global player tracker
def add_player_all_in(p_name):
    global player_details
    if p_name not in player_details:
        player_details[p_name] = dict.fromkeys(init_pd_keys, 0)

    player_details[p_name]['num_all_in'] += 1

def add_player_all_in_win(p_name):
    global player_details
    if p_name not in player_details:
        player_details[p_name] = dict.fromkeys(init_pd_keys, 0)
    player_details[p_name]['num_all_in_wins'] += 1

def add_player_win(p_name):
    global player_details
    if p_name not in player_details:
        player_details[p_name] = dict.fromkeys(init_pd_keys, 0)

    player_details[p_name]['num_wins'] += 1

def add_player_rake_share(p_name, amount):
    global player_details
    if p_name not in player_details:
        player_details[p_name] = dict.fromkeys(init_pd_keys, 0)

    player_details[p_name]['rake'] += amount


def add_player_profit(p_name, amount):
    global player_details
    if p_name not in player_details:
        player_details[p_name] = dict.fromkeys(init_pd_keys, 0)

    player_details[p_name]['win'] += amount


def add_player_expense(p_name, amount):
    global player_details
    if p_name not in player_details:
        player_details[p_name] = dict.fromkeys(init_pd_keys, 0)

    player_details[p_name]['expense'] += amount


# helper to get command line args for input file path and destination output file
def get_inputfiles_path_and_outputfile_path(argv):
    inputfile_path = ''
    outputfile_path = ''
    expected_format = 'ps_calc.py -i "<inputfile_path>" -o "<outputfile_path>"'
    try:
        opts, _ = getopt.getopt(argv, "hi:o:", ["ifilepath=", "ofilepath="])
    except getopt.GetoptError:
        print(expected_format)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(expected_format)
            sys.exit()
        elif opt in ("-i", "--ifilepath"):
            inputfile_path = arg
        elif opt in ("-o", "--ofilepath"):
            outputfile_path = arg
    if inputfile_path == '' or outputfile_path == '':
        print(expected_format)
        sys.exit(2)
    return (inputfile_path, outputfile_path)

# process a hand
# track blinds, people who post even not in blind position, and current bet/action for each player
# throughout the hand
# also capture the hand winner(s) and the rake shares for each player that won
# if the sum of all bets doesn't match the total reported by the hand history, print an error
# this likely hits on a new scenario that we haven't encountered before


def process_hand(hand_log):
    header = hand_log[0].strip()
    header_re = r'PokerStars Home Game Hand #(\d+):'
    match_obj = re.search(header_re, header)
    hand_id = match_obj.group(1)
    
    if hand_id in hands_seen:
        return None 
    else: 
        hands_seen.add(hand_id)
    
    summary_idx = hand_log.index('*** SUMMARY ***\n')
    hand_summary = hand_log[summary_idx+1:]
    pot_details = hand_summary[0]
    pot_total_and_rake = pot_details.split(' | ')
    total = re.search(r'(\d+)', pot_total_and_rake[0]).group(1)
    rake = re.search(r'(\d+)', pot_total_and_rake[1]).group(1)
    winner_details = hand_summary[1:]
    winners = []
    pre_summary = hand_log[:summary_idx]

    all_in_players = set()

    player_action = {}
    hand_blinds = []
    player_seats = []

    # capture the blinds for the hand
    blinds = re.search(r'\((\d+)/(\d+)\)', pre_summary[0])
    small = int(blinds.group(1))
    big = int(blinds.group(2))
    # add all seated players to the action tracker for this hand
    for details in pre_summary:
        if details.lower().startswith('seat'):
            p_match_obj = re.search(r'^Seat (\d+): ([^\s]+) (.*)$', details)

            p_name = p_match_obj.group(2).strip()
            player_action[p_name] = [0]
            player_seats.append({'num': p_match_obj.group(1), 'name': p_name})

    # figure out who the small and big blind positions are
    for details in pre_summary:
        if details.lower().startswith('table'):
            button_mo = re.search(r'.*#(\d+).*', details)
            button_num = int(button_mo.group(1))
            i = 0
            for x in player_seats:
                if int(x['num']) == int(button_num):
                    small_blind = player_seats[(
                        i+1) % len(player_seats)]['name'].strip()
                    big_blind = player_seats[(i+2) %
                                             len(player_seats)]['name'].strip()

                    hand_blinds.append(small_blind)
                    hand_blinds.append(big_blind)
                    break
                i += 1
            break


    for details in pre_summary:
        # handle the case where someone raised and nobody called them for the full amount
        # so give them back that money since it isn't counted as part of the winnings for the hand
        if ' returned ' in details.lower():
            amount = [int(s.replace('(', '').replace(')', '')) for s in details.split(
            ) if s.replace('(', '').replace(')', '').isdigit()][-1]
            last_space = details.rindex(' ')
            player_name = details[last_space+1:]
            player_action[player_name.strip()].append(-1 * amount)
        # when a new round of betting starts, reset everyone's current bet on the table to zero
        elif '*** show' in details.lower() or '*** flop' in details.lower() or '*** turn' in details.lower() or '*** river' in details.lower():
            # reset last bet for all players
            for pname, actions in player_action.items():
                player_action[pname].append(0)
        # when you post a blind, add that as part of your bets on the table
        # if you're posting out of blind position because you left and missed a
        # blind, then don't count your small blind bet as a part of the money
        # you have on the table, instead just deduct it from your total money
        # and act as though you haven't yet bet on this hand's action
        elif ' posts ' in details.lower():
            # handle blinds for people not in small or big position
            last_space = details.rindex(' ')
            amount = [int(s.replace('(', '').replace(')', '')) for s in details.split(
            ) if s.replace('(', '').replace(')', '').isdigit()][-1]
            first_colon = details.index(':')
            player_name = details[:first_colon]

            if player_name.strip() not in hand_blinds:
                if amount == big + small:
                    # if they had to post more than the big blind, their actual last bet is only the big
                    player_action[player_name.strip()].append(small)
                    player_action[player_name.strip()].append(0)
                    player_action[player_name.strip()].append(big)
                elif amount == small:
                    # if you only posted the small blind, then you pay it and your active bet is zero
                    player_action[player_name.strip()].append(amount)
                    player_action[player_name.strip()].append(0)
                else:
                    # you are paying the big blind, which counts towards your bet this hand
                    player_action[player_name.strip()].append(amount)
            else:
                # player is a blind so just apply the blind as part of your active bets this hand
                player_action[player_name.strip()].append(amount)
        # if someone bets or calls then capture the amount they made the total bet minus the sum of
        # all previous bets they had on this round of betting to determine how many chips that player
        # had to throw in to bet or call
        elif ' bets ' in details.lower() or ' calls ' in details.lower():
            last_space = details.rindex(' ')
            amount = [int(s.replace('(', '').replace(')', '')) for s in details.split(
            ) if s.replace('(', '').replace(')', '').isdigit()][-1]
            first_colon = details.index(':')
            player_name = details[:first_colon]
            is_all_in = False
            if 'all-in' in details.lower():
                is_all_in = True
            
            if is_all_in:
                add_player_all_in(player_name.strip())
                all_in_players.add(player_name.strip())

            player_action[player_name.strip()].append(amount)
            
        # if you raise the bet then sum all previous bets on this round and subtract from what you raised to
        # to figure out how many chips you threw in to raise the bet
        elif ' raises ' in details.lower():
            last_space = details.rindex(' ')
            is_all_in = False
            amount = [int(s.replace('(', '').replace(')', '')) for s in details.split(
            ) if s.replace('(', '').replace(')', '').isdigit()][-1]
            if 'all-in' in details.lower():
                is_all_in = True

            first_colon = details.index(':')
            player_name = details[:first_colon]
            #latest_bet_amount = player_action[player_name.strip()][-1]
            last_bets = player_action[player_name.strip()]
            last_zero_idx = len(last_bets) - 1 - last_bets[::-1].index(0)

            latest_bet_amount = sum(last_bets[last_zero_idx:])
            if is_all_in:
                add_player_all_in(player_name.strip())
                all_in_players.add(player_name.strip())

            player_action[player_name.strip()].append(
                amount - latest_bet_amount)

    total_action = 0
    # for each player, count up all the chips they had in play minus any money returned to them
    # and add that as a recorded total expenditure on their chip count for the entire game
    for name, actions in player_action.items():
        sum_actions = sum(actions)
        total_action += sum_actions
        add_player_expense(name, sum_actions)

    # validate that all chips counted in play for the hand match what
    # the hand history says the total chips were
    if int(total_action) != int(total):
        print("\n\n**********ERROR**********\n\n")
        print("ACTION SUM DOESN'T EQUAL EXPECTATIONS FOR HAND " + hand_id)
        print('total action', total_action)
        print('total', total)
        print('rake', rake)
        print('actions', player_action)
        print("\n\n**********ERROR**********\n\n")

    # parse the hand history's "summary" section to capture all winners in the hand
    # and add it to the player's global history of total chips won for the game
    for details in winner_details:
        if ' collected ' in details.lower() or ' win ' in details.lower() or ' won ' in details.lower():
            winner_match_obj = re.search(r'^Seat \d+: ([^\s]+) (.*)$', details)
            winner_name = winner_match_obj.group(1)
           
            add_player_win(winner_name)
            if winner_name.strip() in all_in_players:
                add_player_all_in_win(winner_name)

            rest_of_details = winner_match_obj.group(2)
            winner_amount_won = re.search(
                r'\((\d+)\)', rest_of_details).group(1)
            winners.append({'name': winner_name, 'amount': winner_amount_won})
            add_player_profit(winner_name, int(winner_amount_won))

    # give back the rake to the winners
    # we just split it evenly between all winners which
    # results in fractional chips being awarded in split pot situations sometimes
    # split_rake = float(rake)/len(winners)
    one_minus_rake_pct = 1 - float(rake)/int(total)
    for w in winners:
        split_rake = (float(w['amount'])/one_minus_rake_pct) - float(w['amount'])
        if (split_rake > 0):
            add_player_rake_share(w['name'], float(split_rake))

    # if we had multiple winners, don't populate the "first_winner_*" keys
    # of our hand tracker and instead just record all winners semicolon delimited
    # as PLAYER1_NAME|PLAYER1_WIN_AMOUNT;PLAYER2_NAME|PLAYER2_WIN_AMOUNT...
    winners_collapsed = ';'.join(
        [f"{x['name']}|{x['amount']}" for x in winners])
    has_multiple_winners = len(winners) > 1
    winner_name = ''
    winner_amount = ''

    # if there's only one winner then record them in the first_winner_name and _amount
    # keys of the hand tracker
    if not has_multiple_winners:
        winner_name = winners[0]['name']
        winner_amount = winners[0]['amount']

    return {
        'hand_id': hand_id,
        'has_multiple_winners': has_multiple_winners,
        'first_winner_name': winner_name,
        'first_winner_amount': winner_amount,
        'all_winners': winners_collapsed,
        'total': total,
        'rake': rake
    }


def process_log(argv):
    (inputfile_path, outputfile_path) = get_inputfiles_path_and_outputfile_path(argv)
    all_hands = []

    for _, _, inputfiles in os.walk(inputfile_path):
        for inputfile in inputfiles:
            with open(os.path.join(inputfile_path, inputfile), 'r', encoding='utf-8') as ps_summary:
                try:
                    all_lines = ps_summary.readlines()
                    all_hands.extend(all_lines)
                except Exception as e:
                    print(f"ERROR: Skipping file {inputfile}", e)

    # divide list grouping on non empty/new lines
    # this effectively creates a list of lists where each element
    # of the parent list is a list of all the details for each hand
    each_hand = [list(sub) for ele, sub in groupby(
        all_hands, key=lambda x: x != '\n') if ele]
    final_summary = []
    hand = 1
    # process each hand in the history
    for current_hand in each_hand:
        hand_details = process_hand(current_hand)
        if hand_details:
            final_summary.append(hand_details)
            hand += 1

    # write out the hand raw output
    keys = final_summary[0].keys()
    hand_by_hand_file = os.path.join(outputfile_path, 'hand_by_hand.csv')
    with open(hand_by_hand_file, 'w') as output_csv:
        dict_writer = csv.DictWriter(output_csv, keys)
        dict_writer.writeheader()
        dict_writer.writerows(final_summary)

    # write out the summary to a file called "summary.csv" where
    summary_file = os.path.join(outputfile_path, 'summary.csv')
    with open(summary_file, 'w') as output_summary:
        global player_details
        output_summary.write(
            "player,hands_won,all_in_hands_count,all_in_hands_won,won,lost,rake_share,net,net including rake\n")
        for (player_name, summary) in player_details.items():
            output_summary.write(
                f"{player_name},{summary['num_wins']},{summary['num_all_in']},{summary['num_all_in_wins']},{summary['win']},{summary['expense']},{summary['rake']},{summary['win']-summary['expense']},{(summary['win']+summary['rake'])-summary['expense']}\n")

    print(f"Wrote all output to {outputfile_path}")


"""main function
"""
if __name__ == "__main__":
    # kick off the script and parse args
    process_log(sys.argv[1:])
