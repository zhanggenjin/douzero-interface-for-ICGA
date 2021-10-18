###############################################################################
# 叫地主部分
###############################################################################
import os
import torch
from torch import nn


def EnvToOnehot(cards):
    Env2IdxMap = {3:0,4:1,5:2,6:3,7:4,8:5,9:6,10:7,11:8,12:9,13:10,14:11,17:12,20:13,30:14}
    cards = [Env2IdxMap[i] for i in cards]
    Onehot = torch.zeros((4,15))
    for i in range(0, 15):
        Onehot[:cards.count(i),i] = 1
    return Onehot

def RealToOnehot(cards):
    RealCard2EnvCard = {'3': 0, '4': 1, '5': 2, '6': 3, '7': 4,
                        '8': 5, '9': 6, 'T': 7, 'J': 8, 'Q': 9,
                        'K': 10, 'A': 11, '2': 12, 'X': 13, 'D': 14}
    cards = [RealCard2EnvCard[c] for c in cards]
    Onehot = torch.zeros((4,15))
    for i in range(0, 15):
        Onehot[:cards.count(i),i] = 1
    return Onehot


class Net(nn.Module):
    def __init__(self):
        super().__init__()

        self.fc1 = nn.Linear(60, 512)
        self.fc2 = nn.Linear(512, 512)
        self.fc3 = nn.Linear(512, 512)
        self.fc4 = nn.Linear(512, 512)
        self.fc5 = nn.Linear(512, 512)
        self.fc6 = nn.Linear(512, 1)
        self.dropout5 = nn.Dropout(0.5)
        self.dropout3 = nn.Dropout(0.3)
        self.dropout1 = nn.Dropout(0.1)

    def forward(self, input):
        x = self.fc1(input)
        x = torch.relu(self.dropout1(self.fc2(x)))
        x = torch.relu(self.dropout3(self.fc3(x)))
        x = torch.relu(self.dropout5(self.fc4(x)))
        x = torch.relu(self.dropout5(self.fc5(x)))
        x = self.fc6(x)
        return x


UseGPU = False
device = torch.device('cuda:0')
net = Net()
net.eval()
if UseGPU:
    net = net.to(device)
if os.path.exists("./bid_weights.pkl"):
    if torch.cuda.is_available():
        net.load_state_dict(torch.load('./bid_weights.pkl'))
    else:
        net.load_state_dict(torch.load('./bid_weights.pkl', map_location=torch.device("cpu")))

def predict(cards):
    input = RealToOnehot(cards)
    if UseGPU:
        input = input.to(device)
    input = torch.flatten(input)
    win_rate = net(input)
    return win_rate[0].item() * 100



########################################################################################
# 接口部分
########################################################################################


import requests
import json
port_message = ''         #平台发送的消息
action_set = {}
NAME = 'doudizhu'
TURNID = 0                # 当前轮序号
TURNCOUNT = 0             # 总轮数
ROUNDID = 0               # 当前局序号
ROUNDCOUNT = 0            # 每轮总局数
UPCOUNT = 0               # 本轮可晋级到下一轮的选手数
MAXSCORE = 0              # 封顶分数
TIME = 0                  # AI引擎应答时间限制，单位秒
MY_POSITION = ''           # 我的位置
MY_HANDCARD = [0, 0, 0, 0, 0,
               0, 0, 0, 0, 0,
               0, 0, 0, 0, 0,
               0, 0, 0, 0, 0]
BID_POOL = [0, 0, 0]
WHO_BOSS = ''
THREE_BOSS_CARD = [0, 0, 0]
PORT_BOSS_UP = ''
PORT_BOSS_DOWN = ''
PORT_NUM_BOSS_CARD = 20
PORT_BOSS_DOWN_CARD = 17
PORT_BOSS_UP_CARD = 17
"""
  红桃 方片 黑桃 梅花
0  3
1  4
2  5
3  6
4  7
5  8
6  9
7  T
8  J
9  Q
10  K
11  A
12  2
"""
all_poker = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0]
]

"""
AI可以发出的指令
"""
ai_name = 'doudizhu'
ai_bid = ''
ai_play = ''
ai_ok = ''
ai_position = -1

"""
AI决策参数
"""
bomb_num = '0'
card_play_action_seq = ''
last_move_landlord = ''
last_move_landlord_down = ''
last_move_landlord_up = ''
num_cards_left_landlord = '20'
num_cards_left_landlord_down = '17'
num_cards_left_landlord_up = '17'
played_cards_landlord = ''
played_cards_landlord_down = ''
played_cards_landlord_up = ''
other_hand_cards = ''
player_hand_cards = ''
player_position = ''
three_landlord_cards = ''

"""
平台牌编码转化为牌
"""
def port_code_into_card1(c:int):
    if c<=51 and c>=48:
        card = '2'
    elif c<=47 and c>=44:
        card = 'A'
    elif c<=43 and c>=40:
        card = 'K'
    elif c<=39 and c>=36:
        card = 'Q'
    elif c<=35 and c>=32:
        card = 'J'
    elif c<=31 and c>=28:
        card = 'T'
    elif c == 52:
        card = 'X'
    elif c == 53:
        card = 'D'
    elif c<=3 and c>=0:
        card = '3'
    elif c<=7 and c>=4:
        card = '4'
    elif c<=11 and c>=8:
        card = '5'
    elif c<=15 and c>=12:
        card = '6'
    elif c<=19 and c>=16:
        card = '7'
    elif c<=23 and c>=20:
        card = '8'
    elif c<=27 and c>=24:
        card = '9'
    return str(card)

def port_code_into_card(c:int):
    if c<=51 and c>=48:
        all_poker[12][c-48] = 1
        card = '2'
    elif c<=47 and c>=44:
        all_poker[11][c - 44] = 1
        card = 'A'
    elif c<=43 and c>=40:
        all_poker[10][c - 40] = 1
        card = 'K'
    elif c<=39 and c>=36:
        all_poker[9][c - 36] = 1
        card = 'Q'
    elif c<=35 and c>=32:
        all_poker[8][c - 32] = 1
        card = 'J'
    elif c<=31 and c>=28:
        all_poker[7][c - 28] = 1
        card = 'T'
    elif c == 52:
        card = 'X'
    elif c == 53:
        card = 'D'
    elif c<=3 and c>=0:
        all_poker[0][c - 0] = 1
        card = '3'
    elif c<=7 and c>=4:
        all_poker[1][c - 4] = 1
        card = '4'
    elif c<=11 and c>=8:
        all_poker[2][c - 8] = 1
        card = '5'
    elif c<=15 and c>=12:
        all_poker[3][c - 12] = 1
        card = '6'
    elif c<=19 and c>=16:
        all_poker[4][c - 16] = 1
        card = '7'
    elif c<=23 and c>=20:
        all_poker[5][c - 20] = 1
        card = '8'
    elif c<=27 and c>=24:
        all_poker[6][c - 24] = 1
        card = '9'
    return card


"""
AI编码转化为平台编码
"""
def card_into_port_code(card:str):
    index_x = -1
    index_y = -1
    c = -1
    if card == '3':
        index_x = 0
    elif card == '4':
        index_x = 1
    elif card == '5':
        index_x = 2
    elif card == '6':
        index_x = 3
    elif card == '7':
        index_x = 4
    elif card == '8':
        index_x = 5
    elif card == '9':
        index_x = 6
    elif card == 'T':
        index_x = 7
    elif card == 'J':
        index_x = 8
    elif card == 'Q':
        index_x = 9
    elif card == 'K':
        index_x = 10
    elif card == 'A':
        index_x = 11
    elif card == '2':
        index_x = 12
    elif card == 'X':
        c = 52
    else:
        c = 53
    if index_x<=12 and index_x>=0 :
        for i in range(4):
            if all_poker[index_x][i] == 1:
                all_poker[index_x][i] = 0
                index_y = i
                break
        c = index_x*4 + index_y
    else:
        c = c
    return int(c)

"""
牌:23456789TJQKAXD
bomb_num:出现炸弹的数量
card_play_action_seq:出牌顺序
last_move_landlord:地主最后出的牌
last_move_landlord_down:地主下家最后出的牌
last_move_landlord_up:地主上家最后出的牌
num_cards_left_landlord:地主剩余牌的数量
num_cards_left_landlord_down:地主下家剩余牌的数量
num_cards_left_landlord_up:地主上家剩余牌的数量
played_cards_landlord:地主玩家已经出的牌
played_cards_landlord_down:地主下家已经出的牌
played_cards_landlord_up:地主上家已经出的牌
other_hand_cards:其他家剩余的牌
player_hand_cards:我自己的牌
player_position:我的位置
three_landlord_cards:三张地主牌  0:地主 1:下家 2:上家
"""
"""
pyload:
'bomb_num=4&' \
              'card_play_action_seq=JT9876%2C%2C4444%2C5555%2C%2C%2CQQQ8%2C%2C3333%2C%2C%2CT896J7%2C%2C%2C22%2CXD&' \
              'last_move_landlord=XD&' \
              'last_move_landlord_down=&' \
              'last_move_landlord_up=22&' \
              'num_cards_left_landlord=4&' \
              'num_cards_left_landlord_down=17&' \
              'num_cards_left_landlord_up=1&' \
              'played_cards_landlord=JT98765555QQQ8XD&' \
              'played_cards_landlord_down=&' \
              'played_cards_landlord_up=44443333T896J722&' \
              'other_hand_cards=JTKK2&' \
              'player_hand_cards=6677899TJQKKAAAA2&' \
              'player_position=1&' \
              'three_landlord_cards='
"""
def AI_decision(bomb_num:str, card_play_action_seq:str, last_move_landlord:str, last_move_landlord_down:str, last_move_landlord_up:str,
                num_cards_left_landlord:str, num_cards_left_landlord_down:str, num_cards_left_landlord_up:str, played_cards_landlord:str,
                played_cards_landlord_down:str, played_cards_landlord_up:str, other_hand_cards:str, player_hand_cards:str, player_position:str,
                three_landlord_cards:str):
    url = "http://localhost:5000/predict"

    payload = 'bomb_num=' + bomb_num + '&' +\
              'card_play_action_seq=' + card_play_action_seq + '&' +\
              'last_move_landlord=' + last_move_landlord + '&' +\
              'last_move_landlord_down=' + last_move_landlord_down + '&' +\
              'last_move_landlord_up=' + last_move_landlord_up + '&' +\
              'num_cards_left_landlord=' + num_cards_left_landlord + '&' +\
              'num_cards_left_landlord_down=' + num_cards_left_landlord_down + '&' +\
              'num_cards_left_landlord_up=' + num_cards_left_landlord_up + '&' +\
              'played_cards_landlord=' + played_cards_landlord + '&' +\
              'played_cards_landlord_down=' + played_cards_landlord_down + '&' +\
              'played_cards_landlord_up=' + played_cards_landlord_up + '&' +\
              'other_hand_cards=' + other_hand_cards + '&' +\
              'player_hand_cards=' + player_hand_cards + '&' +\
              'player_position=' + player_position + '&' +\
              'three_landlord_cards=' + three_landlord_cards

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    message = response.text
    message = json.loads(message)
    global action_set
    for k, v in message.items():
        if k == 'win_rates':
            action_set = v
    for k, v in action_set.items():
        action_set[k] = float(v)
    if len(action_set) == 1:
        for k, v in action_set.items():
            action = k
    else:
        action = max(action_set, key=action_set.get)
    #print("action:" + action)
    lion = '指令:\n' + payload + '\n' + '返回:\n' + \
           '地主上家:' + last_move_landlord_up + '\t' +\
            '地主动作' + last_move_landlord + '\t' +\
           '地主下家' + last_move_landlord_down + '\n' +\
            '我的动作' + action + '\n'
    with open("./request", "a", encoding='utf-8') as f:
        f.write(str(lion))
        f.close()
    return action


def get_port_message():
    """
    接收输入指令
    :return:
    """
    global port_message
    port_message = input()
    return port_message.split(' ')[0], port_message.split(' ')[1]


def look_boom(hand_card_tmp: list):
    num_s = 0
    avt = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(12):
        avt[i] = hand_card_tmp.count(i)
    for i in range(12):
        if avt[i] == 4:
            num_s += 1
    if hand_card_tmp.count(12) == 4:
        num_t = 0
    else:
        num_t = hand_card_tmp.count(12)
    return num_s, num_t


def eval_hand_call(MY_HANDCARD:list):
    hand_card = MY_HANDCARD[0:17]
    my_card = ''
    for i in range(17):
        my_card += port_code_into_card1(hand_card[i])
    win_rate = predict(my_card)
    if win_rate >= 80:
        return 3
    else:
        return 0



def port_message_deal(flag: str, action: str):
    global TURNID, TURNCOUNT, ROUNDID, ROUNDCOUNT, UPCOUNT, MAXSCORE, TIME, MY_POSITION, MY_HANDCARD, BID_POOL, WHO_BOSS, THREE_BOSS_CARD, PORT_BOSS_UP, PORT_BOSS_DOWN
    global three_landlord_cards, player_position, player_hand_cards, other_hand_cards, played_cards_landlord_up, played_cards_landlord_down
    global played_cards_landlord, num_cards_left_landlord, num_cards_left_landlord_up,num_cards_left_landlord_down, last_move_landlord_up
    global last_move_landlord_down, last_move_landlord, card_play_action_seq, bomb_num, PORT_NUM_BOSS_CARD, PORT_BOSS_DOWN_CARD, PORT_BOSS_UP_CARD
    if flag == 'DOUDIZHUVER':
        print('NAME '+NAME)
    elif flag == 'INFO':
        action = action.split(',')
        TURNID = int(action[0])
        TURNCOUNT = int(action[1])
        ROUNDID = int(action[2])
        ROUNDCOUNT = int(action[3])
        UPCOUNT = int(action[4])
        MAXSCORE = int(action[5])
        #TIME = int(action[6])
        print('OK INFO')
    elif flag == 'DEAL':
        action = action.split(',')
        MY_POSITION = action[0][0]
        a = list(action[0])
        a.remove(a[0])
        a = ''.join(a)
        action[0] = a
        MY_HANDCARD[0] = int(action[0])
        for i in range(1, 17):
            MY_HANDCARD[i] = int(action[i])
        print('OK DEAL')
    elif flag == 'BID':
        if MY_POSITION == 'A':
            if action == 'WHAT':
                if eval_hand_call(MY_HANDCARD) > BID_POOL[1] and eval_hand_call(MY_HANDCARD) > BID_POOL[2]:
                   print('BID A' + str(eval_hand_call(MY_HANDCARD)))
                else:
                   print('BID A0')
                BID_POOL[0] = eval_hand_call(MY_HANDCARD)
            elif action[0] == 'B':
                BID_POOL[1] = int(action[1])
                print('OK BID')
            elif action[0] == 'C':
                BID_POOL[2] = int(action[1])
                print('OK BID')
        elif MY_POSITION == 'B':
            if action[0] == 'A':
                BID_POOL[0] = int(action[1])
                print('OK BID')
            elif action == 'WHAT':
                if eval_hand_call(MY_HANDCARD) > BID_POOL[0] and eval_hand_call(MY_HANDCARD) > BID_POOL[2]:
                   print('BID B' + str(eval_hand_call(MY_HANDCARD)))
                else:
                   print('BID B0')
                BID_POOL[1] = eval_hand_call(MY_HANDCARD)
            elif action[0] == 'C':
                BID_POOL[2] = int(action[1])
                print('OK BID')
        elif MY_POSITION == 'C':
            if action[0] == 'A':
                BID_POOL[0] = int(action[1])
                print('OK BID')
            elif action[0] == 'B':
                BID_POOL[1] = int(action[1])
                print('OK BID')
            elif action == 'WHAT':
                if eval_hand_call(MY_HANDCARD) > BID_POOL[1] and eval_hand_call(MY_HANDCARD) > BID_POOL[0]:
                   print('BID C' + str(eval_hand_call(MY_HANDCARD)))  # 最后叫牌的策略
                else:
                   print('BID C0')
                BID_POOL[2] = eval_hand_call(MY_HANDCARD)

    elif flag == 'LEFTOVER':
        WHO_BOSS = action[0]
        action = action.split(',')
        a = list(action[0])
        a.remove(a[0])
        a = ''.join(a)
        action[0] = a
        if WHO_BOSS == 'A':
            PORT_BOSS_UP = 'C'
            PORT_BOSS_DOWN = 'B'
        elif WHO_BOSS == 'B':
            PORT_BOSS_UP = 'A'
            PORT_BOSS_DOWN = 'C'
        elif WHO_BOSS == 'C':
            PORT_BOSS_UP = 'B'
            PORT_BOSS_DOWN = 'A'
        three_boss_hand = ''
        for i in range(3):
            three_boss_hand += port_code_into_card1(int(action[i]))
        three_landlord_cards = three_boss_hand
        if WHO_BOSS == MY_POSITION:
            MY_HANDCARD[17] = int(action[0])
            MY_HANDCARD[18] = int(action[1])
            MY_HANDCARD[19] = int(action[2])
            temp1 = ''
            for i in range(17, 20):
                temp1 += port_code_into_card(MY_HANDCARD[i])
            three_landlord_cards = temp1
            player_position = '0'
            temp2 = ''
            for i in range(0, 20):
                temp2 += port_code_into_card(MY_HANDCARD[i])

            player_hand_cards = temp2
            list1 = []
            for i in range(0, 54):
                list1.append(i)
            #print(list1)
            for i in range(20):
                list1.remove(MY_HANDCARD[i])
            temp3 = ''
            for i in range(len(list1)):
                temp3 += port_code_into_card1(list1[i])
            other_hand_cards = temp3
        else:
            if WHO_BOSS == 'A' and MY_POSITION == 'B':
                player_position = '1'
            elif WHO_BOSS == 'A' and MY_POSITION == 'C':
                player_position = '2'
            elif WHO_BOSS == 'B' and MY_POSITION == 'C':
                player_position = '1'
            elif WHO_BOSS == 'B' and MY_POSITION == 'A':
                player_position = '2'
            elif WHO_BOSS == 'C' and MY_POSITION == 'A':
                player_position = '1'
            elif WHO_BOSS == 'C' and MY_POSITION == 'B':
                player_position = '2'
            temp2 = ''
            for i in range(0, 17):
                temp2 += port_code_into_card(MY_HANDCARD[i])
            player_hand_cards = temp2
            list1 = []
            for i in range(0, 54):
                list1.append(i)
            #print(list1)
            for i in range(17):
                list1.remove(MY_HANDCARD[i])
            temp3 = ''
            for i in range(len(list1)):
                temp3 += port_code_into_card1(list1[i])
            other_hand_cards = temp3
        THREE_BOSS_CARD[0] = int(action[0])
        THREE_BOSS_CARD[1] = int(action[1])
        THREE_BOSS_CARD[2] = int(action[2])
        print('OK LEFTOVER')
    elif flag == 'PLAY':
        if action == 'WHAT':
            card_play_action_seq_tmp = ''
            if len(card_play_action_seq) != 0:
                if card_play_action_seq[-1] == 'C':
                    card_play_action_seq_tmp = card_play_action_seq
                    card_play_action_seq_tmp = card_play_action_seq_tmp[0:-3:1]
            decision = AI_decision(bomb_num, card_play_action_seq_tmp, last_move_landlord, last_move_landlord_down,
                                   last_move_landlord_up,
                                   num_cards_left_landlord, num_cards_left_landlord_down,
                                   num_cards_left_landlord_up, played_cards_landlord,
                                   played_cards_landlord_down, played_cards_landlord_up, other_hand_cards,
                                   player_hand_cards, player_position, three_landlord_cards)
            if len(decision) == 0:
                print('PLAY ' + MY_POSITION + '-1')
            else:
                if len(decision) == 1:
                    out = 'PLAY ' + MY_POSITION + str(card_into_port_code(decision))
                else:
                    out = 'PLAY ' + MY_POSITION + str(card_into_port_code(decision[0]))
                    for i in range(1, len(decision)):
                        out += (',' + str(card_into_port_code(decision[i])))
                print(out)
                # 更新参数
                if len(decision) == 4:
                    if decision[0] == decision[1] and decision[1] == decision[2] and decision[2] == decision[3]:
                        bomb_num = str(int(bomb_num) + 1)
                elif len(decision) == 2:
                    if (decision[0] == 'X' and decision[1] == 'D') or (decision[0] == 'D' and decision[1] == 'X'):
                        bomb_num = str(int(bomb_num) + 1)
                card_play_action_seq += decision + '%2C'        #可能有问题
                if WHO_BOSS == MY_POSITION:
                    last_move_landlord = decision
                    PORT_NUM_BOSS_CARD = PORT_NUM_BOSS_CARD - len(decision)
                    num_cards_left_landlord = str(PORT_NUM_BOSS_CARD)
                    played_cards_landlord += decision
                elif MY_POSITION == PORT_BOSS_DOWN:
                    last_move_landlord_down = decision
                    PORT_BOSS_DOWN_CARD = PORT_BOSS_DOWN_CARD - len(decision)
                    num_cards_left_landlord_down = str(PORT_BOSS_DOWN_CARD)
                    played_cards_landlord_down += decision
                elif MY_POSITION == PORT_BOSS_UP:
                    last_move_landlord_up = decision
                    PORT_BOSS_UP_CARD = PORT_BOSS_UP_CARD - len(decision)
                    num_cards_left_landlord_up = str(PORT_BOSS_UP_CARD)
                    played_cards_landlord_up += decision
                p = list(player_hand_cards)
                for i in range(len(decision)):
                    for j in range(len(p)):
                        if decision[i] == p[j]:
                            p.remove(p[j])
                            break
                player_hand_cards = ''.join(p)
        elif action[0] == WHO_BOSS:
            if action[-2] == '-':
                card_play_action_seq += '%2C'
                last_move_landlord = ''
            else:
                action = action.split(',')
                a = list(action[0])
                a.remove(a[0])
                a = ''.join(a)
                action[0] = a
                ls = ''
                for i in range(len(action)):
                    ls += port_code_into_card1(int(action[i]))
                if len(ls) == 4:
                    if ls[0] == ls[1] and ls[1] == ls[2] and ls[2] == ls[3]:
                        bomb_num = str(int(bomb_num) + 1)
                elif len(ls) == 2:
                    if (ls[0] == 'X' and ls[1] == 'D') or (ls[0] == 'D' and ls[1] == 'X'):
                        bomb_num = str(int(bomb_num) + 1)
                card_play_action_seq += ls + '%2C'
                last_move_landlord = ls
                PORT_NUM_BOSS_CARD = PORT_NUM_BOSS_CARD - len(ls)
                num_cards_left_landlord = str(PORT_NUM_BOSS_CARD)
                played_cards_landlord += ls
                p = list(other_hand_cards)
                for i in range(len(ls)):
                    for j in range(len(p)):
                        if ls[i] == p[j]:
                            p.remove(p[j])
                            break
                other_hand_cards = ''.join(p)
            print('OK PLAY')
        elif action[0] == PORT_BOSS_UP:
            if action[-2] == '-':
                card_play_action_seq += '%2C'
                last_move_landlord_up = ''
            else:
                action = action.split(',')
                a = list(action[0])
                a.remove(a[0])
                a = ''.join(a)
                action[0] = a
                ls = ''
                for i in range(len(action)):
                    ls += port_code_into_card1(int(action[i]))
                if len(ls) == 4:
                    if ls[0] == ls[1] and ls[1] == ls[2] and ls[2] == ls[3]:
                        bomb_num = str(int(bomb_num) + 1)
                elif len(ls) == 2:
                    if (ls[0] == 'X' and ls[1] == 'D') or (ls[0] == 'D' and ls[1] == 'X'):
                        bomb_num = str(int(bomb_num) + 1)
                card_play_action_seq += ls + '%2C'
                last_move_landlord_up = ls
                PORT_BOSS_UP_CARD -= len(ls)
                num_cards_left_landlord_up = str(PORT_BOSS_UP_CARD)
                played_cards_landlord_up += ls
                p = list(other_hand_cards)
                for i in range(len(ls)):
                    for j in range(len(p)):
                        if ls[i] == p[j]:
                            p.remove(p[j])
                            break
                other_hand_cards = ''.join(p)
            print('OK PLAY')
        elif action[0] == PORT_BOSS_DOWN:
            if action[-2] == '-':
                card_play_action_seq += '%2C'
                last_move_landlord_down = ''
            else:
                action = action.split(',')
                a = list(action[0])
                a.remove(a[0])
                a = ''.join(a)
                action[0] = a
                ls = ''
                for i in range(len(action)):
                    ls += port_code_into_card1(int(action[i]))
                if len(ls) == 4:
                    if ls[0] == ls[1] and ls[1] == ls[2] and ls[2] == ls[3]:
                        bomb_num = str(int(bomb_num) + 1)
                elif len(ls) == 2:
                    if (ls[0] == 'X' and ls[1] == 'D') or (ls[0] == 'D' and ls[1] == 'X'):
                        bomb_num = str(int(bomb_num) + 1)
                card_play_action_seq += ls + '%2C'
                last_move_landlord_down = ls
                PORT_BOSS_DOWN_CARD -= len(ls)
                num_cards_left_landlord_down = str(PORT_BOSS_DOWN_CARD)
                played_cards_landlord_down += ls
                p = list(other_hand_cards)
                for i in range(len(ls)):
                    for j in range(len(p)):
                        if ls[i] == p[j]:
                            p.remove(p[j])
                            break
                other_hand_cards = ''.join(p)
            print('OK PLAY')
    elif flag == 'GAMEOVER':
        print('OK GAMEOVER')
        return True
    elif flag == 'ERROR':
        print('OK ERROR')



"""
CommandIndict = {"DOUDIZHUVER": 0,
                     "INFO": 1,
                     "DEAL": 2,
                     "BID": 3,
                     "LEFTOVER": 4,
                     "PLAY": 5,
                     "GAMEOVER": 6
                     }
    sCommandIn = input()
    return CommandIndict[sCommandIn.split(" ")[0]], sCommandIn.split(" ")
"""

"""
if __name__ == '__main__':
    while True:
        MYLOCATION = ""
        HIM = ""
        LOCATIONPOOL = {"A": 0, "B": 0, "C": 0}  # 叫分信息
        HISTORYCARD = {"A": [0] * 15, "B": [0] * 15, "C": [0] * 15}  # 历史出牌信息
        SENDINGCARD = []  # 当前底牌信息

        MYHAVECARD = [False] * 54  # 自己拥有的牌
        pks = [[0] * 15 for j in range(3)]
        while True:
            commandtulp = ALInput()
            if AIcal(commandtulp):
                break
"""
if __name__ == '__main__':
    while True:
        port_message = ''  # 平台发送的消息

        NAME = 'doudizhu'
        TURNID = 0  # 当前轮序号
        TURNCOUNT = 0  # 总轮数
        ROUNDID = 0  # 当前局序号
        ROUNDCOUNT = 0  # 每轮总局数
        UPCOUNT = 0  # 本轮可晋级到下一轮的选手数
        MAXSCORE = 0  # 封顶分数
        TIME = 0  # AI引擎应答时间限制，单位秒
        MY_POSITION = ''  # 我的位置
        MY_HANDCARD = [0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0]
        BID_POOL = [0, 0, 0]
        WHO_BOSS = ''
        THREE_BOSS_CARD = [0, 0, 0]
        PORT_BOSS_UP = ''
        PORT_BOSS_DOWN = ''
        PORT_NUM_BOSS_CARD = 20
        PORT_BOSS_DOWN_CARD = 17
        PORT_BOSS_UP_CARD = 17
        """
          红桃 方片 黑桃 梅花
        0  3
        1  4
        2  5
        3  6
        4  7
        5  8
        6  9
        7  T
        8  J
        9  Q
        10  K
        11  A
        12  2
        """
        all_poker = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]

        """
        AI可以发出的指令
        """
        ai_name = 'doudizhu'
        ai_bid = ''
        ai_play = ''
        ai_ok = ''
        ai_position = -1

        """
        AI决策参数
        """
        bomb_num = '0'
        card_play_action_seq = ''
        last_move_landlord = ''
        last_move_landlord_down = ''
        last_move_landlord_up = ''
        num_cards_left_landlord = '20'
        num_cards_left_landlord_down = '17'
        num_cards_left_landlord_up = '17'
        played_cards_landlord = ''
        played_cards_landlord_down = ''
        played_cards_landlord_up = ''
        other_hand_cards = ''
        player_hand_cards = ''
        player_position = ''
        three_landlord_cards = ''
        while True:
            flag, action = get_port_message()
            a = port_message_deal(flag, action)
            if a == True:
                break
            else:
                continue
