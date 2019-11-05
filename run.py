import argparse
import glob
import os
import random

import sc2
from sc2 import Difficulty, Race
from sc2.paths import Paths
from sc2.player import Bot, Computer

from __init__ import run_ladder_game
# Load bot
from example_bot import ExampleBot
bot = Bot(Race.Random, ExampleBot())


def get_random_map_name() -> str:
    """Returns a random map name from SC2 Maps folder."""
    map_file_paths = glob.glob(f"{Paths.MAPS}/**/*.SC2Map")

    def get_file_name(path) -> str:
        filename_w_ext = os.path.basename(path)
        filename, file_ext = os.path.splitext(filename_w_ext)
        return filename

    # Use a set to remove duplicate names (same map in multiple folders)
    map_file_names = set(map(get_file_name, map_file_paths))

    if not any(map_file_names):
        raise Exception(f"no maps found from {Paths.MAPS}")

    return random.choice(list(map_file_names))


# Start game
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run a Starcraft 2 bot game."
    )
    parser.add_argument("--LadderServer", help="Run a game with SC2 Ladder Manager. Otherwise a local game game will "
                                               "be run.", action="store_true")
    parser.add_argument("-rt", "--real-time", help="Use real-time mode. Otherwise games will be run as fast as "
                                                   "possible.", action="store_true")
    parser.add_argument('--ComputerRace', type=str, nargs="?", help='Computer race', default='Random')
    parser.add_argument('--ComputerDifficulty', type=str, nargs="?", help='Computer difficulty',
                        default='VeryHard')

    args = parser.parse_args()

    if args.LadderServer:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        result, opponent_id = run_ladder_game(bot)
        print(result, " against opponent ", opponent_id)
    else:
        difficulty = Difficulty[args.ComputerDifficulty]
        race = Race[args.ComputerRace]

        # Local game
        print(f"Starting a local game against {args.ComputerDifficulty} {args.ComputerRace}...")

        map_name = get_random_map_name()
        print(f"Using map {map_name}")

        sc2.run_game(sc2.maps.get(map_name), [
            bot,
            Computer(race, difficulty)
        ], realtime=args.real_time)
