import random
import json
import psycopg2
from db import store_spin_db

# CONFIG
TOTAL_BET = 20.0
PAYLINES_COUNT = 20
BET_PER_LINE = TOTAL_BET / PAYLINES_COUNT

ROWS = 3
COLS = 5

WILD = "Wild"
SCATTER = "Scatter"


# REELS (List)

REEL_1 = ["Wild"]*2 + ["Gun"]*2 + ["Hat"]*2 + ["Gold"]*2 + ["A"]*3 + ["K"]*3 + ["Q"]*4 + ["J"]*4 + ["10"]*4 + ["9"]*2 + ["Scatter"]*2 + ["Boot"]*2 + ["Barrel"]*2
REEL_2 = ["Wild"]*2 + ["Gun"]*1 + ["Hat"]*1 + ["Gold"]*2 + ["A"]*3 + ["K"]*4 + ["Q"]*3 + ["J"]*3 + ["10"]*4 + ["9"]*3 + ["Boot"]*3 + ["Barrel"]*3
REEL_3 = ["Wild"]*2 + ["Gun"]*1 + ["Hat"]*1 + ["Gold"]*2 + ["A"]*3 + ["K"]*3 + ["Q"]*4 + ["J"]*4 + ["10"]*4 + ["9"]*4 + ["Scatter"]*2 + ["Boot"]*3 + ["Barrel"]*3
REEL_4 = ["Wild"]*1 + ["Gun"]*1 + ["Hat"]*1 + ["Gold"]*2 + ["A"]*3 + ["K"]*3 + ["Q"]*4 + ["J"]*3 + ["10"]*4 + ["9"]*3 + ["Boot"]*2 + ["Barrel"]*3
REEL_5 = ["Wild"]*1 + ["Gun"]*2 + ["Hat"]*2 + ["Gold"]*5 + ["A"]*2 + ["K"]*3 + ["Q"]*4 + ["J"]*4 + ["10"]*4 + ["9"]*3 + ["Scatter"]*2 + ["Boot"]*2 + ["Barrel"]*3

REELS = [REEL_1, REEL_2, REEL_3, REEL_4, REEL_5]


# PAYTABLE (Data dictionary)
PAYTABLE = {
    "A": {3:10, 4:50, 5:125},
    "K": {3:10, 4:50, 5:100},
    "Q": {3:5, 4:25, 5:100},
    "J": {3:5, 4:25, 5:100},
    "10":{3:5, 4:25, 5:100},
    "9": {2:2, 3:5, 4:25, 5:100},
    "Wild": {2:10, 3:200, 4:2000, 5:10000},
    "Gold": {2:2, 3:25, 4:100, 5:750},
    "Gun": {2:2, 3:25, 4:100, 5:750},
    "Hat": {3:15, 4:100, 5:400},
    "Boot":{3:10, 4:75, 5:250},
    "Barrel":{3:10, 4:50, 5:250}
}
SCATTER_PAY = {2:2, 3:5, 4:20, 5:100}


# PAYLINES (top = 0 , middle = 1,bottom = 2)
PAYLINES = [
    [1,1,1,1,1],[0,0,0,0,0],[2,2,2,2,2],
    [0,1,2,1,0],[2,1,0,1,2],[0,0,1,2,2],
    [2,2,1,0,0],[1,0,1,2,0],[1,2,1,0,1],
    [0,1,1,1,2],[2,1,1,1,0],[1,0,0,1,2],
    [1,2,2,1,0],[1,1,0,1,2],[1,1,2,1,0],
    [0,0,1,2,1],[2,2,1,0,1],[1,0,1,2,2],
    [1,2,1,0,0],[0,0,0,1,2]
]




# RESHUFFLE REELS 
def reshuffle_reels():
    for reel in REELS:
        random.shuffle(reel)


# GRID GENERATION
def generate_base_game_grid():
    grid = []

    # STEP 1: Create empty 3x5 grid
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            row.append("")
        grid.append(row)

    # STEP 2: Fill grid using reels
    for c in range(COLS):
        reel = REELS[c]
        stop = random.randrange(len(reel))
        for r in range(ROWS):
            grid[r][c] = reel[(stop + r) % len(reel)]

    return grid



# COUNTING SCATTERS
def count_scatters(grid):
    return sum(1 for row in grid for s in row if s == SCATTER)


# EVALUATING PAYLINE 
def evaluate_line(symbols):
    best_win = 0

    # Step 1: base symbols collect karo (Wild + normal symbols, Scatter ignore)
    bases = set()

    for s in symbols:
        if s != WILD and s != SCATTER:
            bases.add(s)

    # Wild ko ek baar add karo
    bases.add(WILD)

    # Step 2: har base symbol ke liye win calculate karo
    for base in bases:
        count = 0

        for s in symbols:
            if s == SCATTER:
                break

            if s == base or (s == WILD and base != SCATTER):
                count += 1
            else:
                break

        if base in PAYTABLE and count in PAYTABLE[base]:
            win = PAYTABLE[base][count] * BET_PER_LINE
            best_win = max(best_win, win)

    return best_win



def evaluate_grid(grid):
    total = 0

    for line in PAYLINES:
        symbols = []

        for c in range(COLS):
            row = line[c]
            symbol = grid[row][c]
            symbols.append(symbol)

        total += evaluate_line(symbols)

    scatters = count_scatters(grid)
    if scatters<3 and scatters in SCATTER_PAY:
        total += SCATTER_PAY[scatters] * TOTAL_BET

    return total



# RTP SIMULATION
def simulate_rtp(total_spins):
    total_bet = 0
    total_win = 0

    for spin_id in range(1,total_spins+1):
        total_bet += TOTAL_BET

        # Reshuffle reels every spin
        reshuffle_reels()
        # Generate grid
        grid = generate_base_game_grid()
        # Evaluate Payline 
        win = evaluate_grid(grid)
        total_win += win

        store_spin_db(
            spin_id=spin_id,
            grid=grid,
            total_bet=TOTAL_BET,
            total_win=win
        )

        scatters = count_scatters(grid)
        if scatters >= 3:  # 3,4,5 scatters trigger free spins
            free_spins = 3  # always 3 free spins

            for fs_index in range(free_spins):
                reshuffle_reels()
                free_grid = generate_base_game_grid()
                free_win = evaluate_grid(free_grid)
                total_win += free_win  # add free spin win
                
                store_spin_db(
                    spin_id=f"{spin_id}_FS{fs_index}",  
                    grid=free_grid,                      
                     total_bet=0.0,                
                    total_win=free_win,
                    is_free_spin=True
                )

    rtp = (total_win / total_bet) * 100
    print(f"Total Spins : {total_spins}")
    print(f"Total Bet   : {total_bet}")
    print(f"Total Win   : {total_win}")
    print(f"RTP (%)     : {rtp:.2f}")

# RUN
simulate_rtp(10)
