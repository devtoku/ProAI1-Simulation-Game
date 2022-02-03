from dataclasses import dataclass
from typing import ByteString
import numpy as np
import copy
import random

'''
CASTLE, SOLDIER, KNIGHT, ARCHERの順番。
WALL, GRASS, SAND, ROCKの順番。
'''

#初期変数郡
MAP_X = 15
MAP_Y = 15

PLAYER_1, PLAYER_2 = 1, 2

#地形情報
WALL, GRASS, SAND, ROCK = 0, 1, 2, 3
#コマ情報
CASTLE, SOLDIER, KNIGHT, ARCHER = 0, 1, 2, 3

#死亡判定
DEAD, ALIVE = 0, 1
#移動判定
NOT_MOVED, MOVED = 0, 1

#コマのID
P1_CASTLE_ID = 0
P1_KNIGHT_ID = 1
P1_SOLDIER1_ID = 2
P1_SOLDIER2_ID = 3
P1_SOLDIER3_ID = 4
P1_SOLDIER4_ID = 5
P1_ARCHER1_ID = 6
P1_ARCHER2_ID = 7
P2_CASTLE_ID = 8
P2_KNIGHT_ID = 9
P2_SOLDIER1_ID = 10
P2_SOLDIER2_ID = 11
P2_SOLDIER3_ID = 12
P2_SOLDIER4_ID = 13
P2_ARCHER1_ID = 14
P2_ARCHER2_ID = 15
ID_LIST = [P1_CASTLE_ID, P1_KNIGHT_ID,\
    P1_SOLDIER1_ID, P1_SOLDIER2_ID, P1_SOLDIER3_ID, P1_SOLDIER4_ID,\
        P1_ARCHER1_ID, P1_ARCHER2_ID,\
            P2_CASTLE_ID, P2_KNIGHT_ID,\
                P2_SOLDIER1_ID, P2_SOLDIER2_ID, P2_SOLDIER3_ID, P2_SOLDIER4_ID,\
                    P2_ARCHER1_ID, P2_ARCHER2_ID]

#コマのステータス
CASTLE_STATUS = {"HP": 150, "ATK": 90, "DEF": 30, "MOV": 1}
SOLDIER_STATUS = {"HP": 80, "ATK": 50, "DEF": 40, "MOV": 5}
KNIGHT_STATUS = {"HP": 100, "ATK": 65, "DEF": 50, "MOV": 8}
ARCHER_STATUS = {"HP": 50, "ATK": 40, "DEF": 35, "MOV": 5}

STATUS_DIR = {"C": CASTLE_STATUS, "S": SOLDIER_STATUS, "K": KNIGHT_STATUS, "A": ARCHER_STATUS,\
    "c": CASTLE_STATUS, "s": SOLDIER_STATUS, "k": KNIGHT_STATUS, "a": ARCHER_STATUS}

#コマ同士の相性(Compatibility)
piece_compatibility = [[0, 0, 0, -15], [0, 0, -25, 50], [0, 25, 0, -25], [15, -50, 25, 0]]

#地形による防御力バフ(%)
terrain_power = [100, 0, 5, 30]

#最大移動コスト
MAX_DISTANCE = 99

#AI同士の繰り返しの上限数
MAX_NUMBER_OF_MOVES = 100

#地形効果による移動コスト
move_cost = [[MAX_DISTANCE, MAX_DISTANCE, MAX_DISTANCE, MAX_DISTANCE],\
    [MAX_DISTANCE, 1, 3, 2], [MAX_DISTANCE, 1, 1, 1], [MAX_DISTANCE, 2, 4, 4]]

GAME_FINISHED = 0
GAME_NOT_FINISHED = 1
PLAYER1_WIN_LEFT, PLAYER2_WIN_LEFT = 2, 3
PLAYER1_WIN_CASTLE, PLAYER2_WIN_CASTLE = 4, 5

TOTAL_GAMES_TO_PLAY = 100
ARMY_DESTROYER_AI = 1
CASTLE_DESTROYER_AI = 2

@dataclass
class Piece:
    ID: int = None #コマのID
    Player: int = None #プレイヤー
    Name :str = None #コマの名前
    piece_type: int = None #コマの種類
    piece_type_str: str = None
    startX: int = None #マップ上のコマの初期位置
    startY: int = None
    nowX: int = None #マップ上のコマの現在位置
    nowY: int = None
    dead_or_alive: int = ALIVE #コマの生死判定
    move_finished: int = NOT_MOVED #コマが移動済みか判定
    hit_point: int = None #コマの体力, 攻撃力, 防御力, 移動力
    attack: int = None
    defense: int = None
    mov_pow: int = None
    destinations = None #コマの移動可能な場所

def readFile(file): #ファイルを読み込むための関数
    obj = None

    with open(file, "r", encoding="utf-8") as f:
        obj = f.read().split("#")

        obj_map = obj[0].replace("\n", "").replace(" ", "")
        obj_piece = obj[1]
    
    return obj_map, obj_piece

def read_map(map_obj, sizeX, sizeY): #マップを読み込むための関数
    mapFile = map_obj
    mapSize = [sizeX, sizeY]
    mapList = []

    for s in mapFile:
        if s == "W": mapList.append(WALL)
        if s == "G": mapList.append(GRASS)
        if s == "S": mapList.append(SAND)
        if s == "R": mapList.append(ROCK)

    mapForm = np.array(mapList).reshape(mapSize)
    mapList = mapForm.tolist()

    return mapList

def make_piece(piece_obj):
    pieceList =piece_obj.split("\n")
    pieceList.pop(0) #先頭に謎の空要素があるので削除
    pinfoList = []
    pieceIDCount = 0
    pieceNameCount = {"C": 1, "K": 1, "S": 1, "A": 1,\
        "c": 1, "k": 1, "s": 1, "a": 1}

    for p in pieceList:
        thisType, thisY, thisX = p.split(" ")
        thisX, thisY = int(thisX), int(thisY)
        thisStatus = STATUS_DIR[thisType]
        thisNameOfType = ""
        thisNumverOfType = None

        #txt内のコマリストから、それぞれCKSAのどれなのかを判定して一時的に記憶
        if thisType == "C" or thisType == "c":
            thisNameOfType = "Castle"
            thisNumverOfType = CASTLE
        elif thisType == "K" or thisType == "k":
            thisNameOfType = "Knight"
            thisNumverOfType = KNIGHT
        elif thisType == "S" or thisType == "s":
            thisNameOfType = "Soldier"
            thisNumverOfType = SOLDIER
        elif thisType == "A" or thisType == "a":
            thisNameOfType = "Archer"
            thisNumverOfType = ARCHER

        thisPiece = Piece(Name = thisNameOfType+str(pieceNameCount[thisType]), piece_type=thisNumverOfType,\
            piece_type_str = thisType, startX=thisX, startY=thisY, nowX=thisX, nowY=thisY,\
                hit_point=thisStatus["HP"], attack=thisStatus["ATK"],\
                    defense=thisStatus["DEF"], mov_pow=thisStatus["MOV"])
        
        if thisType in ["C", "K", "S", "A"]:
            thisPiece.Player = 1
        else: thisPiece.Player = 2

        thisPiece.ID = ID_LIST[pieceIDCount]
        pinfoList.append(thisPiece)

        for type in pieceNameCount.keys():
            if type == thisType:
                pieceNameCount[type] += 1
        pieceIDCount += 1

    return pinfoList

def outputMap(thismap): #ゲーム盤のリストをきれいに表示する関数
    mapStrForm = []

    for i in thismap:
        tmpList = []
        for j in i:
            tmpList.append(str(j))
        mapStrForm.append(tmpList)
    mapFormResult = [ "   ".join(i) for i in mapStrForm]

    for i in mapFormResult:
        moji = i
        print("{:>15s}".format(moji))

def mapToList(thismap):
    mapStrForm = []

    for i in thismap:
        tmpList = []
        for j in i:
            tmpList.append(str(j))
        mapStrForm.append(tmpList)
    mapFormResult = [ "  ".join(i) for i in mapStrForm]

    for i in range(len(mapFormResult)):
        mapFormResult[i] = mapFormResult[i] + "\n"

    return mapFormResult


def outputPInfo(pinfo): #pinfoリストの情報を列挙するための関数
    for piece in pinfo:
        print("Player{} {}(ID: {}) info: y= {} x= {} HP= {} ATK= {} DEF= {} MOV= {}"\
            .format(piece.Player, piece.Name,piece.ID, piece.nowY, piece.nowX,\
                    piece.hit_point, piece.attack, piece.defense, piece.mov_pow))

def setPieceToMap(mapform, piece_obj): #マップにコマを配置する関数
    thisMap = copy.deepcopy(mapform) #deepcopyを用いることで元のリストの要素を変更しないで済む。

    pieceList = piece_obj.split("\n")
    pieceList.pop(0) #先頭に謎の空要素があるので削除

    for p in pieceList:
        thisType, thisY, thisX = p.split(" ")
        thisX, thisY = int(thisX), int(thisY)

        thisMap[thisY][thisX] = thisType

    return thisMap

def searchEnemyPosition(pinfo, player): #プレイヤー毎のコマの位置をリストにして返す関数
    enemyPositionList = []
    enemy = None
    if player == PLAYER_1:
        enemy = PLAYER_2
    elif player == PLAYER_2:
        enemy = PLAYER_1
    for piece in pinfo:
        if piece.Player == enemy and piece.nowX <= MAP_X:
            enemyPositionList.append([piece.nowX, piece.nowY])
    return enemyPositionList

def searchPiecePosition(pinfo, piece_type): #城の位置を返す
    PositionList = []

    for piece in pinfo:
        if piece.piece_type == piece_type:
            PositionList.append([piece.nowX, piece.nowY])
    
    return PositionList

def searchPositionToMove(piece, EnemyPositionList): #移動可能な場所を探索する関数
    piece.destinations = [[0 for _ in range(MAP_X)] for _ in range(MAP_Y)]

    if piece.dead_or_alive == ALIVE and piece.move_finished == NOT_MOVED and piece.piece_type != CASTLE:
        for position in EnemyPositionList:
            enemyX, enemyY = position[0], position[1]
            if enemyX < MAP_X and enemyY < MAP_Y:
                piece.destinations[enemyY][enemyX] = MAX_DISTANCE
        
        get_destinations_for_piece(piece.nowY, piece.nowX,\
            piece.mov_pow, piece.piece_type, piece.destinations)

        for position in EnemyPositionList:
            enemyX, enemyY = position[0], position[1]
            if enemyX < MAP_X and enemyY < MAP_Y:
                piece.destinations[enemyY][enemyX] = WALL
        
def get_destinations_for_piece(starty, startx, cur_pow, piece_type, destinations):
    destinations[starty][startx] = cur_pow
    for i in [[startx, starty-1], [startx, starty+1], [startx+1, starty], [startx-1, starty]]:
        next_x, next_y = i[0], i[1]
        if MAP_X > next_x >= 0 and MAP_Y > next_y >= 0: #ゲーム盤（リスト）の範囲外にいかないように指定。
            next_position_type = strategy_map[next_y][next_x]
            next_position_mov = destinations[next_y][next_x]
            if next_position_type != WALL: #壁でないことを確認している。
                mov_left = cur_pow - move_cost[next_position_type][piece_type]
                if mov_left > next_position_mov:
                    get_destinations_for_piece(next_y, next_x, mov_left, piece_type, destinations)
                else:
                    continue

def move_pieces_army_destroyer(pinfo, turn):
    aspiration_map = create_aspiration_map_army_destroyer(pinfo, turn)
    #outputMap(aspiration_map)
    nowinfo = None
    if turn == PLAYER_1: nowinfo = pinfo[:8]
    elif turn == PLAYER_2: nowinfo = pinfo[8:]
    for piece in nowinfo:
        if piece.dead_or_alive == ALIVE and piece.piece_type != CASTLE and\
            piece.move_finished == NOT_MOVED:
            find_piece_destination(piece, aspiration_map)
            resolve_battle(piece)

#有利度マップの作成
def create_aspiration_map_army_destroyer(pinfo, turn):
    player = None
    best_dest_info = [[MAX_DISTANCE for _ in range(MAP_X)] for _ in range(MAP_Y)]

    if turn == PLAYER_1:
        player = PLAYER_2
    elif turn == PLAYER_2:
        player = PLAYER_1
    
    for piece in pinfo:
        if piece.Player == player and piece.piece_type != CASTLE and piece.dead_or_alive == ALIVE:
            #print("###############################")
            for y in range(MAP_Y):
                for x in range(MAP_X):
                    manhattan = abs(x - piece.nowX) + abs(y - piece.nowY)
                    if manhattan < best_dest_info[y][x]:
                        best_dest_info[y][x] = manhattan
                        #print(outputMap(best_dest_info))
    #outputMap(best_dest_info)
    return best_dest_info


#コマの移動の順番をランダムで決定
def move_pieces_castle_destroyer(pinfo, turn):
    nowinfo = None
    if turn == PLAYER_1: nowinfo = pinfo[:8]
    elif turn == PLAYER_2: nowinfo = pinfo[8:]
    for piece in nowinfo:
        if piece.dead_or_alive == ALIVE and piece.piece_type != CASTLE and\
            piece.move_finished == NOT_MOVED:
            aspiration_map = create_aspiration_map_castle_destroyer(piece, turn)
            find_piece_destination(piece, aspiration_map)
            resolve_battle(piece)

#有利度マップの作成
def create_aspiration_map_castle_destroyer(piece, turn):
    best_dest_info = [[MAX_DISTANCE for _ in range(MAP_X)] for _ in range(MAP_Y)]
    target = None

    if turn == PLAYER_1:
        target = P2_CASTLE_ID
    elif turn == PLAYER_2:
        target = P1_CASTLE_ID

    if piece.dead_or_alive == ALIVE:
        check_distance(pinfo[target].nowY, pinfo[target].nowX, 0, piece.piece_type, best_dest_info, target)
        #outputMap(best_dest_info)
    return best_dest_info

def check_distance(starty, startx, distance, piece_type, aspmap, target):
    #print(startx, starty, pinfo[8].hit_point, pinfo[8].dead_or_alive)
    if 0 <= startx < MAP_X and 0 <= starty < MAP_Y:
        aspmap[starty][startx] = distance
        #castle = pinfo[target]
        for i in [[startx, starty-1], [startx, starty+1], [startx+1, starty], [startx-1, starty]]:
            next_x, next_y = i[0], i[1]
            if MAP_X > next_x >= 0 and MAP_Y > next_y >= 0: #ゲーム盤（リスト）の範囲外にいかないように指定。
                next_position_type = strategy_map[next_y][next_x]
                next_position_mov = aspmap[next_y][next_x]
                if next_position_type != WALL: #壁でないことを確認している。
                    mov_left = distance + move_cost[piece_type][next_position_type]
                    if mov_left < next_position_mov:
                        #outputMap(aspmap)
                        check_distance(next_y, next_x, mov_left, piece_type, aspmap, target)
                    else:
                        continue
    else: pass

#各コマの移動先を決定
def find_piece_destination(piece, aspiration_map):
    if piece.dead_or_alive == ALIVE and piece.move_finished == NOT_MOVED and piece.piece_type != CASTLE:
        piece_position_list = [[p.nowX, p.nowY] for p in pinfo]
        for pos in piece_position_list:
            #print([pos[1], pos[0]])
            if pos[1] < MAP_Y and pos[0] < MAP_X:
                piece.destinations[pos[1]][pos[0]] = 0
        
        next_position_candidates = []
        for y in range(MAP_Y):
            for x in range(MAP_X):
                if piece.destinations[y][x] != 0:
                    next_position_candidates.append([y, x])
                else:
                    continue

        next_aspiration = MAX_DISTANCE
        next_position = [piece.nowY, piece.nowX]
        for pos in next_position_candidates:
            if aspiration_map[pos[0]][pos[1]] < next_aspiration:
                next_aspiration = aspiration_map[pos[0]][pos[1]]
                next_position = pos
                #print(next_aspiration)
            elif aspiration_map[pos[0]][pos[1]] == next_aspiration:
                if random.randint(0, 1) == 1:
                    next_aspiration = aspiration_map[pos[0]][pos[1]]
                    next_position = pos
        piece.nowX, piece.nowY = next_position[1], next_position[0]
        piece.move_finished = MOVED

#戦闘を実施
#戦う相手の決定
def resolve_battle(piece):
    #print("BATTLE!!!!!!")
    enemy_player = None
    if piece.Player == PLAYER_1:
        enemy_player = PLAYER_2
    elif piece.Player == PLAYER_2:
        enemy_player = PLAYER_1
    
    battle_candidates = []
    for enemy in pinfo:
        if enemy.Player == enemy_player and enemy.dead_or_alive == ALIVE:
            if enemy.nowX in [piece.nowX - 1, piece.nowX + 1] and enemy.nowY in [piece.nowY - 1, piece.nowY + 1]:
                battle_candidates.append(enemy)
    for i in range(len(battle_candidates)):#バブルソート
            for j in range(len(battle_candidates)-1, i, -1):
                if battle_candidates[j].hit_point < battle_candidates[j-1].hit_point:
                    battle_candidates[j], battle_candidates[j-1] = battle_candidates[j-1], battle_candidates[j]
    
    if len(battle_candidates) > 0:
        enemy_to_fight = battle_candidates.pop(0)
        if enemy_to_fight.nowX < MAP_X and enemy_to_fight.nowY < MAP_Y:
            fight_battle(piece, enemy_to_fight)

#実際に戦う
def fight_battle(friend, enemy):
    friendNowPosType = strategy_map[friend.nowY][friend.nowX]
    enemyNowPosType = strategy_map[enemy.nowY][enemy.nowX]

    friendToEnemy_hp = update_battle_hp(friend.attack, enemy.defense, piece_compatibility[friend.piece_type][enemy.piece_type], terrain_power[enemyNowPosType])
    enemy.hit_point -= friendToEnemy_hp
    with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
        f.write(f"【############戦闘###########】\n Player{friend.Player} {friend.Name} --Attack-> Player{enemy.Player} {enemy.Name} HP: {enemy.hit_point}\n")
    if enemy.hit_point <= 0:
        enemy.dead_or_alive = DEAD
        enemy.nowX, enemy.nowY = MAP_X + MAX_DISTANCE, MAP_Y + MAX_DISTANCE
    else:
        if enemy.dead_or_alive == ALIVE:
            enemyToFriend_hp = update_battle_hp(enemy.attack, friend.defense, piece_compatibility[enemy.piece_type][friend.piece_type], terrain_power[friendNowPosType])
            friend.hit_point -= enemyToFriend_hp
            with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
                f.write(f"【############反撃###########】\n Player{enemy.Player} {enemy.Name} --Counter-> Player{friend.Player} {friend.Name} HP: {friend.hit_point}\n")
            if friend.hit_point <= 0:
                friend.dead_or_alive = DEAD
                friend.nowX, friend.nowY = MAP_X + MAX_DISTANCE, MAP_Y + MAX_DISTANCE
    
    #print(f"BATTLE Player{friend.Player} {friend.Name} --Attack-> Player{enemy.Player} {enemy.Name} HP: {enemy.hit_point}")

#戦闘結果の反映
def update_battle_hp(atk, defe, piece_com, ter_power):
    attack = atk + (atk * piece_com) / 100
    defense = defe + (defe * ter_power) / 100
    hp = attack - defense
    if hp < 0:
        hp = 0
    #print(hp)
    return int(hp)

def check_game_finished():
    p1_castle = ALIVE
    p2_castle = ALIVE
    p1_left = DEAD
    p2_left = DEAD
    win_situation = GAME_NOT_FINISHED

    if pinfo[P1_CASTLE_ID].dead_or_alive == DEAD:
        p1_castle = DEAD
    if pinfo[P2_CASTLE_ID].dead_or_alive == DEAD:
        p2_castle = DEAD
    
    for piece in pinfo:
        if piece.Player == PLAYER_1 and piece.piece_type != CASTLE:
            if piece.dead_or_alive == ALIVE:
                p1_left = ALIVE
        if piece.Player == PLAYER_2 and piece.piece_type != CASTLE:
            if piece.dead_or_alive == ALIVE:
                p2_left = ALIVE
    
    if p1_castle == ALIVE and p1_left == ALIVE and p2_left == DEAD:
        win_situation = PLAYER1_WIN_LEFT
    elif p2_castle == ALIVE and p2_left == ALIVE and p1_left == DEAD:
        win_situation = PLAYER2_WIN_LEFT
    elif p2_castle == DEAD:
        win_situation = PLAYER1_WIN_CASTLE
    elif p1_castle == DEAD:
        win_situation = PLAYER2_WIN_CASTLE
    
    return win_situation

def map_reload(strategy_map, pinfo):
    now_map = copy.deepcopy(strategy_map)

    for piece in pinfo:
        thisX, thisY = piece.nowX, piece.nowY
        if thisX < MAP_X and thisY < MAP_Y:
            now_map[thisY][thisX] = piece.piece_type_str
    
    return now_map

'''
メインループを別で作成して、ゲームループはその中で回せばよいのでは。
'''
def game_loop(player1, player2):
    Turn = player1
    counter = 2
    game_finished = GAME_NOT_FINISHED
    max_loop = 100
    loop_now = 0
    win = None

    while game_finished == GAME_NOT_FINISHED and loop_now < max_loop:
        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.write("【{}回目のループです。Player{}の手番です。】\n".format(int(counter/2), loop_now % 2 + 1))

        enemyPositionList = searchEnemyPosition(pinfo, Turn)
        for piece in pinfo:
            searchPositionToMove(piece, enemyPositionList)

        for piece in pinfo:
            if Turn == PLAYER_1:
                move_pieces_army_destroyer(pinfo, PLAYER_1)
            elif Turn == PLAYER_2:
                move_pieces_castle_destroyer(pinfo, PLAYER_2)
        game_finished = check_game_finished()
        if loop_now % 2 == 0 or loop_now == 0:
            Turn = player2
            for piece in pinfo:
                piece.move_finished = NOT_MOVED
                #if piece.Player == PLAYER_2:
                #    piece.move_finished = NOT_MOVED
        elif loop_now % 2 == 1:
            Turn = player1
            for piece in pinfo:
                piece.move_finished = NOT_MOVED
                #if piece.Player == PLAYER_1:
                #    piece.move_finieshed = NOT_MOVED
        
        #print("【{}回目のループです。Player{}の手番です。】".format(int(counter/2), loop_now  % 2 + 1))
        now_map = map_reload(strategy_map, pinfo)
        #outputMap(now_map)
        #outputPInfo(pinfo)
        #print(game_finished)

        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.writelines(mapToList(now_map))
            for piece in pinfo:
                if piece.dead_or_alive == ALIVE:
                    f.write("Player{} {}(ID: {}) info: y= {} x= {} HP= {} ATK= {} DEF= {} MOV= {}\n"\
                        .format(piece.Player, piece.Name,piece.ID, piece.nowY, piece.nowX,\
                            piece.hit_point, piece.attack, piece.defense, piece.mov_pow))

        counter += 1
        loop_now += 1
        #outputMap(pinfo[11].destinations)
    
    if game_finished == PLAYER1_WIN_LEFT:
        #print("Player1 Wins")
        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.write("Player2のコマが全滅した！Player1の勝ちでーす。")
    elif game_finished == PLAYER2_WIN_LEFT:
        #print("Player2 Wins")
        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.write("Player1のコマが全滅した！Player2の勝ちでーす。")
    elif game_finished == PLAYER1_WIN_CASTLE:
        #print("Player1 Wins")
        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.write("Player2の城が落ちた！Player1の勝ちでーす。")
    elif game_finished == PLAYER2_WIN_CASTLE:
        #print("Player2 Wins")
        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.write("Player1の城が落ちた！Player2の勝ちでーす。")
    elif game_finished == GAME_NOT_FINISHED and loop_now + 1 > max_loop:
        #print("Draw. Get ready to the next fight.")
        with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
            f.write("引き分けでーす。")
    
    if game_finished == PLAYER1_WIN_LEFT or game_finished == PLAYER1_WIN_CASTLE:
        win = PLAYER_1
    elif game_finished == PLAYER2_WIN_LEFT or game_finished == PLAYER2_WIN_CASTLE:
        win = PLAYER_2
    else:
        win = GAME_NOT_FINISHED
    return win


player1, player2 = None, None
which_win = None
army_ai_count, castle_ai_count = 0, 0
draw = 0
for loop in range(1, TOTAL_GAMES_TO_PLAY + 1):
    obj = readFile("./StrategyGameMap.txt")
    strategy_map = read_map(obj[0], MAP_X, MAP_Y)
    pinfo = make_piece(obj[1])
    piece_in_map = setPieceToMap(strategy_map, obj[1])
    print(f"{loop}回目のループです")
    if loop % 2 == 1:
        player1, player2 = ARMY_DESTROYER_AI, CASTLE_DESTROYER_AI
    elif loop % 2 == 0:
        player1, player2 = CASTLE_DESTROYER_AI, ARMY_DESTROYER_AI

    with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
        f.write(f"\n{loop}回目の対戦です。\n")
    
    which_win = game_loop(player1, player2)
    winner, loser = None, None
    if loop % 2 == 1:
        if which_win == PLAYER_1:
            winner = "ARMY_DESTROYER"
            #loser = "CASTLE_DESTROYER"
            army_ai_count += 1
        elif which_win == PLAYER_2:
            #loser = "ARMY_DESTROYER"
            winner = "CASTLE_DESTROYER"
            castle_ai_count += 1
        else: draw += 1

    elif loop % 2 == 0:
        if which_win == PLAYER_1:
            #loser = "ARMY_DESTROYER"
            winner = "CASTLE_DESTROYER"
            castle_ai_count += 1
        elif which_win == PLAYER_2:
            winner = "ARMY_DESTROYER"
            #loser = "CASTLE_DESTROYER"
            army_ai_count += 1
    pinfo = None
    piece_in_map = None
    print(f"winner: {which_win}")
    print(f"ARMY>>{army_ai_count}, CASTLE>>{castle_ai_count}")

    with open("./sim_game.txt", mode="a", encoding="utf-8") as f:
        f.write(f"\n{loop}回目の対戦が終了しました。\n勝者: {winner}\n現在のスコア: ARMY_DESTROYER>> {army_ai_count} - {castle_ai_count} <<CASTLE_DESTROYER")
