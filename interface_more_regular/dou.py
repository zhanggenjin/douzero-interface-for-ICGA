import os
import sys
import time
import re

from douzero.env.game import GameEnv
from douzero.evaluation.deep_agent import DeepAgent

EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                    8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}

# EnvCard2IndexList = {
#     3: [0, 1, 2, 3],
#     4: [4,5,6,7],
#     5:[8,9,10,11],
#     6:[12,13,14,15],
#     7:[16,17,18,19],
#
#
# }

RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                    '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
                    'K': 13, 'A': 14, '2': 17, 'X': 20, 'D': 30}

AllEnvCard = [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7,
              8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11, 12,
              12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 17, 17, 17, 17, 20, 30]

AllCards = ['rD', 'bX', 'b2', 'r2', 'bA', 'rA', 'bK', 'rK', 'bQ', 'rQ', 'bJ', 'rJ', 'bT', 'rT',
            'b9', 'r9', 'b8', 'r8', 'b7', 'r7', 'b6', 'r6', 'b5', 'r5', 'b4', 'r4', 'b3', 'r3']


class Ddz:
    def __init__(self):
        self.iStatus = 0  # 引擎状态-1错误,0结束,1开始
        self.sCommandIn = ""  # "['' for c in range(80)]  # 通信输入内容
        self.sCommandOut = ""  # "['' for c in range(80)]  # 通信输出内容
        self.iOnHand = [-1 for i in range(21)]  # 手中牌（所有值初始化为-1）
        # self.iOnTable[162][21]	# 以出牌数组（所有值初始化为-2）每行是一手牌，以-1结尾，Pass记为-1
        self.iToTable = []  # 要出的牌
        self.sVer = ""  # 协议版本号
        self.sName = "SMART Dou"  # 参赛选手称呼
        self.cDir = '-'  # 玩家方位编号
        self.cLandlord = '-'  # 地主玩家方位编号
        self.cWinner = '-'  # 胜利者方位编号
        self.iBid = [-1 for i in range(3)]  # 叫牌过程
        self.iBidMax = -1  # 当前最大叫牌数，值域{-1,0,1,2,3}
        # self.iOTmax				# 当前出牌手数
        self.iRoundNow = -1  # 当前局次
        self.iRoundTotal = -1  # 和总局数
        self.iTurnNow = -1  # 当前轮次
        self.iTurnTotal = 0  # 总轮数
        self.iLevelUp = -1  # 晋级选手数
        self.iScoreMax = -1  # 转换得分界限
        # self.iVoid				# 闲暇并行计算参数
        self.iLef = [-1 for _ in range(3)]  # 本局底牌
        # self.iLastPassCount		# 当前桌面连续PASS数（值域[0,2],初值2，正常出牌取0，一家PASS取1，两家PASS取2）
        # self.iLastTypeCount		# 当前桌面牌型张数（值域[0,1108],初值0，iLastPassCount=0时更新值，=1时保留原值，=2时值为0）
        # self.iLastMainPoint		# 当前桌面主牌点数（值域[0,15],初值-1，iLastPassCount=0时更新值，，=1时保留原值，=2时值为-1）
        # self.iPlaArr		# 己方多种出牌可行解集（各出牌解由牌编号升序组成-1间隔,-2收尾）
        # self.iPlaCount			# 己方多种出牌可行解数量（值域[0，kPlaMax-1]）
        # self.iPlaOnHand[21]		# 己方模拟出牌后手牌编码
        self.iTime = 0  # 玩家出牌限时

        # super(self).__init__()
        # 模型路径
        self.card_play_model_path_dict = {
            'landlord': "baselines/douzero_WP/landlord.ckpt",
            'landlord_up': "baselines/douzero_WP/landlord_up.ckpt",
            'landlord_down': "baselines/douzero_WP/landlord_down.ckpt"
        }

    def init_cards(self):
        # 玩家手牌
        # self.user_hand_cards_real = ""
        self.user_hand_cards_env = []
        # 其他玩家出牌
        self.other_played_cards_real = ""
        self.other_played_cards_env = []
        # 其他玩家手牌（整副牌减去玩家手牌，后续再减掉历史出牌）
        self.other_hand_cards = []
        # 三张底牌
        self.three_landlord_cards_real = ""
        self.three_landlord_cards_env = []
        # 玩家角色代码：0-地主上家, 1-地主, 2-地主下家
        self.user_position_code = None
        self.user_position = ""
        # 开局时三个玩家的手牌
        self.card_play_data_list = {}
        # 出牌顺序：0-玩家出牌, 1-玩家下家出牌, 2-玩家上家出牌
        self.play_order = 0
        self.env_to_all_card = {}
        self.env = None

    def get_cards(self):
        # 整副牌减去玩家手上的牌，就是其他人的手牌,再分配给另外两个角色（如何分配对AI判断没有影响）
        for i in set(AllEnvCard):
            self.other_hand_cards.extend([i] * (AllEnvCard.count(i) - self.user_hand_cards_env.count(i)))
        self.card_play_data_list.update({
            'three_landlord_cards': self.three_landlord_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 0) % 3]:
                self.user_hand_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 1) % 3]:
                self.other_hand_cards[0:17] if (self.user_position_code + 1) % 3 != 1 else self.other_hand_cards[17:],
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 2) % 3]:
                self.other_hand_cards[0:17] if (self.user_position_code + 1) % 3 == 1 else self.other_hand_cards[17:]
        })
        # print(self.card_play_data_list)
        # 得到出牌顺序
        self.play_order = 0 if self.user_position == "landlord" else 1 if self.user_position == "landlord_up" else 2

        # 创建一个代表玩家的AI
        ai_players = [0, 0]
        ai_players[0] = self.user_position
        ai_players[1] = DeepAgent(self.user_position, self.card_play_model_path_dict[self.user_position])

        self.env = GameEnv(ai_players)

        self.env.card_play_init(self.card_play_data_list)

    def my_turn(self):
        # print(self.user_position)
        # print(self.env.card_play_action_seq)
        # player_hand_cards = [self.env_to_all_card[c] for c in self.env.info_sets[self.user_position].player_hand_cards]
        # print(player_hand_cards)
        action_message = self.env.my_step(self.user_position)
        # print(action_message)
        #             # 更新界面

        # self.PredictedCard.setText(action_message["action"] if action_message["action"] else "不出")
        # self.WinRate.setText("胜率：" + action_message["win_rate"])
        # print("\n手牌：", str(''.join(
        #         [EnvCard2RealCard[c] for c in self.env.info_sets[self.user_position].player_hand_cards])))
        # print("出牌：", action_message["action"] if action_message["action"] else "不出", "， 胜率：",
        #         action_message["win_rate"])
        if action_message["action"] and len(action_message["action"]) > 0:

            for c in action_message["action"] if action_message["action"] else []:
                # print(c,type(c))
                i = self.env_to_all_card[c][0]
                self.iToTable.append(i)
                self.env_to_all_card[c].remove(i)
            # print([EnvCard2RealCard[c] for c in [AllEnvCard[c] for c in self.iToTable]])
            # self.play_order = 1
            return str(','.join(str(c) for c in self.iToTable))
            # print(self.env_to_all_card)
        else:
            return '-1'

    def others_turn(self):
        cards = []
        # pass_flag = False
        others_play_cards = self.sCommandIn
        reg = re.match(r"PLAY (?P<dir>[ABC])", others_play_cards).groupdict()
        if reg is None:
            self.sCommandOut = "PLAY WRONG"
            return
        # dir = reg["dir"]
        others_play_cards = re.sub(r"PLAY [ABC]", "", others_play_cards)
        # print(others_play_cards)
        while others_play_cards != "":
            num_str = re.match(r"(?P<number>[+-]?\d+)", others_play_cards).groupdict()["number"]
            # print(num_str)
            if num_str is None:
                break
            num = int(num_str)
            if num == -1:
                # pass_flag = True
                break
                # print(num)
            cards.append(AllEnvCard[num])
            str_temp = re.sub(num_str + ',', "", others_play_cards, count=1)
            if str_temp == others_play_cards:
                break
            others_play_cards = str_temp
            # print(others_play_cards)
        self.env.step(self.user_position, cards)

    # print('out')

    #
    # def stop(self):
    #     try:
    #         self.env.game_over = True
    #     except AttributeError as e:
    #         pass

    def init_turn(self):
        self.init_round()
        self.init_cards()

    # 重置本局初始数据
    def init_round(self):
        # self.iStatus = 1
        # self.sCommandIn = ""
        # self.sCommandOut = ""
        # self.sVer = ""
        # self.sName = "SMART Dou"
        self.cDir = '-'
        self.cLandlord = '-'
        # self.cWinner = '-'
        for i in range(3):
            self.iBid[i] = -1
        self.iBidMax = -1

    def analyze_msg(self):
        re_dou = "DOU"
        flag_dou = re.match(re_dou, self.sCommandIn)
        if flag_dou is not None:
            self.get_dou()
            return
        re_inf = "INF"
        flag_inf = re.match(re_inf, self.sCommandIn)
        if flag_inf is not None:
            self.get_inf()
            return
        re_dea = "DEA"
        flag_dea = re.match(re_dea, self.sCommandIn)
        if flag_dea is not None:
            self.get_dea()
            return
        re_bid = "BID"
        flag_bid = re.match(re_bid, self.sCommandIn)
        if flag_bid is not None:
            self.get_bid()
            return
        re_lef = "LEF"
        flag_lef = re.match(re_lef, self.sCommandIn)
        if flag_lef is not None:
            self.get_lef()
            return
        re_pla = "PLA"
        flag_pla = re.match(re_pla, self.sCommandIn)
        if flag_pla is not None:
            self.get_pla()
            return
        # print(self.sCommandIn)
        re_gam = "GAM"
        flag_gam = re.match(re_gam, self.sCommandIn)
        if flag_gam is not None:
            self.get_gam()
            return
        re_exi = "EXI"
        flag_exi = re.match(re_exi, self.sCommandIn)
        if flag_exi is not None:
            self.env = None
            exit(0)
        self.sCommandOut = "Error in AnalyzeMsg, input: " + self.sCommandIn
        return

    def get_dou(self):
        self.sVer = self.sCommandIn
        self.sCommandOut = "NAME " + self.sName
        return

    def get_inf(self):
        self.init_turn()
        match = re.match(r"INFO\s+(?P<turnid>\d+)," \
                         "(?P<turncount>\d+)," \
                         "(?P<roundid>\d+)," \
                         "(?P<roundcount>\d+)," \
                         "(?P<upcount>\d+)," \
                         "(?P<maxscore>\d+)," \
                         "(?P<time>\d+)", self.sCommandIn)
        if match is None:
            self.sCommandOut = "INFO WRONG"
            return
        reg_group_dict = match.groupdict()
        # print(reg_group_dict)
        self.iTurnNow = int(reg_group_dict["turnid"])
        self.iTurnTotal = int(reg_group_dict["turncount"])
        self.iRoundNow = int(reg_group_dict["roundid"])
        self.iRoundTotal = int(reg_group_dict["roundcount"])
        self.iLevelUp = int(reg_group_dict["upcount"])
        self.iScoreMax = int(reg_group_dict["maxscore"])
        self.iTime = int(reg_group_dict["time"])
        # print(self.iTurnNow, self.iTurnTotal, self.iRoundNow,
        # self.iRoundTotal, self.iLevelUp, self.iScoreMax, self.iTime)
        self.sCommandOut = "OK INFO"

    def get_dea(self):
        self.init_cards()
        self.env_to_all_card = {
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
            8: [],
            9: [],
            10: [],
            11: [],
            12: [],
            13: [],
            14: [],
            17: [],
            20: [],
            30: [],
        }
        for i in range(3):
            self.iBid[i] = -1
        self.iBidMax = -1

        deal = self.sCommandIn
        cnt = 0
        reg = re.match(r"DEAL (?P<dir>[ABC])", deal).groupdict()
        if reg is None:
            self.sCommandOut = "DEAL WRONG"
            return
        self.cDir = reg["dir"]
        # print(self.cDir)
        deal = re.sub(r"DEAL [ABC]", "", deal)
        # print(deal)
        while deal != "":
            num_str = re.match(r"(?P<number>\d+)", deal).groupdict()["number"]
            num = int(num_str)
            # print(num)
            self.iOnHand[cnt] = num
            cnt += 1
            if cnt == 17:
                break
            deal = re.sub(num_str + ',', "", deal, count=1)
            # print(deal)
        # print(self.iOnHand)

        # 识别玩家手牌
        # self.user_hand_cards_real = self.get_my_cards()
        # print(self.iOnHand)
        self.user_hand_cards_env = [AllEnvCard[c] for c in list(self.iOnHand[0:17])]
        # print(self.user_hand_cards_env)
        for c in list(self.iOnHand[0:17]):
            self.env_to_all_card[AllEnvCard[c]].append(c)
        # print(self.env_to_all_card)
        self.sCommandOut = "OK DEAL"

    def cal_bid(self):
        if self.iBidMax == 3:
            return 0
        return 3

    def get_bid(self):
        if re.match(r"BID WHAT", self.sCommandIn):
            bid = self.cal_bid()
            self.iBid[ord(self.cDir) - ord('A')] = bid
            if bid > self.iBidMax:
                self.iBidMax = bid
            self.sCommandOut = "BID " + self.cDir + str(bid)
            # print(self.iBid)
            return
        match = re.match(r"BID (?P<dir>[ABC])(?P<bid>\d)", self.sCommandIn)
        if match is None:
            self.sCommandOut = "BID WRONG"
            return
        dict = match.groupdict()
        bid = int(dict["bid"])
        self.iBid[ord(dict["dir"]) - ord('A')] = bid
        if bid > self.iBidMax:
            self.iBidMax = bid
        # print(self.iBid)
        self.sCommandOut = "OK BID"
        return

    def get_lef(self):
        match = re.match(r"LEFTOVER\s*(?P<landlord>[ABC])(?P<card0>\d+),(?P<card1>\d+),(?P<card2>\d+)", self.sCommandIn)
        if match is None:
            self.sCommandOut = "LEF WRONG"
            return
        dict = match.groupdict()
        self.cLandlord = dict["landlord"]
        # print(self.cLandlord)
        self.iLef[0] = int(dict["card0"])
        self.iLef[1] = int(dict["card1"])
        self.iLef[2] = int(dict["card2"])
        # print(self.iLef)
        # 识别三张底牌
        # self.three_landlord_cards_real = self.get_three_landlord_cards(self.ThreeLandlordCardsPos)
        self.three_landlord_cards_env = [AllEnvCard[c] for c in list(self.iLef)]
        # print(self.three_landlord_cards_env)

        self.user_position_code = self.get_position_code(self.cDir)
        self.user_position = ['landlord_up', 'landlord', 'landlord_down'][self.user_position_code]
        # print(self.user_position)
        if self.user_position_code == 1:
            self.user_hand_cards_env.extend(self.three_landlord_cards_env)
            for c in list(self.iLef):
                self.env_to_all_card[AllEnvCard[c]].append(c)
        # print(self.env_to_all_card)
        self.get_cards()
        self.sCommandOut = "OK LEFTOVER"
        return

    def get_position_code(self, dir):
        code = 0
        if dir == 'A':
            if self.cLandlord == 'A':
                code = 1
            elif self.cLandlord == 'B':
                code = 0
            else:
                code = 2
        elif dir == 'B':
            if self.cLandlord == 'B':
                code = 1
            elif self.cLandlord == 'C':
                code = 0
            else:
                code = 2
        elif dir == 'C':
            if self.cLandlord == 'C':
                code = 1
            elif self.cLandlord == 'A':
                code = 0
            else:
                code = 2
        return code

    def get_pla(self):
        my_turn_reg = r"PLAY WHAT"
        match = re.match(my_turn_reg, self.sCommandIn)
        if match is not None:
            self.sCommandOut = "PLAY " + self.cDir + self.my_turn()
            self.iToTable = []
            pass
        else:
            self.others_turn()
            self.sCommandOut = "OK PLAY"
        return

    def get_gam(self):
        # print(self.iRoundNow)
        # print(self.iRoundTotal)
        # if self.iRoundNow == self.iRoundTotal:
        #     self.iStatus = 0
        # else:
        #     self.iRoundNow += 1
        self.sCommandOut = "OK GAMEOVER"
        # self.env.reset()
        self.env = None
        return

    def output_msg(self):
        print(self.sCommandOut)
        self.sCommandOut = ""
        return


if __name__ == '__main__':
    pDdz = Ddz()
    # smart_dou = SMARTDou(pDdz)
    # # print('hi')
    # smart_dou.init_cards()
    while True:
        pDdz.sCommandIn = input()
        # print(pDdz.sCommandIn)
        pDdz.analyze_msg()
        pDdz.output_msg()
    # InitTurn(pDdz)
