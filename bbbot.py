from enum import Enum

import sc2
from sc2.constants import UnitTypeId as Id
from sc2.units import Units

MINERAL_WORKERS_PER_BASE = 16

SUPPLY_MAX = 200
SUPPLY_PER_NEXUS = 11
SUPPLY_PER_PYLON = 8


class Strategy(Enum):
    FIGHTING = 1
    ATTACK = 2
    IDLE = 3


class BBBot(sc2.BotAI):
    def __init__(self):
        super().__init__()
        self.natural = None

    async def on_step(self, iteration):
        if iteration == 0:
            await self.setup()
            print("Game started")

        await self.macro()
        await self.war()

    def on_end(self, result):
        print("OnGameEnd() was called.")

    async def macro(self):
        await self.distribute_workers()
        await self.build_all()
        self.train_all()

    # Setup

    async def setup(self):
        self.natural = await self.get_next_expansion()
        print("Natural at {location}.".format(location=self.natural))

    # War

    async def war(self):
        strategy = self.main_strategy()
        if strategy == Strategy.FIGHTING:
            self.find_fight()
        if strategy == Strategy.ATTACK:
            self.attack()
        if strategy == Strategy.IDLE:
            self.to_natural()

    def main_strategy(self) -> Strategy:
        if len(self.all_targets()) > 0:
            return Strategy.FIGHTING
        if self.supply_army >= 20:
            return Strategy.ATTACK

        return Strategy.IDLE

    def all_targets(self):
        possible = self.enemy_units if self.enemy_units.amount > 0 else self.enemy_structures

        return possible.filter(lambda target: target.can_be_attacked)

    def all_attackers(self) -> Units:
        return self.units(Id.ZEALOT)

    def find_fight(self):
        for attacker in self.all_attackers():
            target = self.search_location(attacker)
            self.do(attacker.attack(target))

    def attack(self):
        for attacker in self.all_attackers():
            target = self.find_target(attacker)
            self.do(attacker.attack(target))

    def to_natural(self):
        for attacker in self.all_attackers():
            target = self.natural
            self.do(attacker.move(target))

    def find_target(self, unit):
        targets = self.all_targets()
        if targets:
            target = targets.closest_to(unit)
            if target:
                return target

        return self.search_location(unit)

    def search_location(self, unit):
        return self.enemy_start_locations[0]

    # Build

    async def build_all(self):
        await self.build_supply()
        await self.build_gateways()
        if self.should_expand():
            await self.expand_now()

    async def build_supply(self):
        if self.should_build_supply() and self.can_afford(Id.PYLON):
            nexus = self.townhalls.ready.random
            await self.build(Id.PYLON, near=nexus)

    def should_build_supply(self) -> bool:
        return self.supply_cap + self.supply_pending() < self.supply_need_expected()

    def should_expand(self) -> bool:
        return self.supply_workers > self.need_workers() - (2 * self.townhalls.amount)

    def need_workers(self) -> int:
        return min(self.townhalls.amount * MINERAL_WORKERS_PER_BASE, 80)

    def supply_pending(self) -> int:
        return self.already_pending(Id.PYLON) * SUPPLY_PER_PYLON + self.already_pending(Id.NEXUS) * SUPPLY_PER_NEXUS

    def supply_need_expected(self) -> int:
        return min(round((self.supply_used + 2) * 1.2), SUPPLY_MAX)

    async def build_gateways(self):
        if self.should_build_gateway():
            pylon = self.structures(Id.PYLON).ready.random
            await self.build(Id.GATEWAY, near=pylon)

    def should_build_gateway(self):
        return (
            self.structures(Id.PYLON).ready
            and self.already_pending(Id.GATEWAY) == 0
            and (
                not self.structures(Id.GATEWAY).ready
                or self.minerals > 250
            )
        )

    # Train

    def train_all(self):
        self.train_workers()
        self.train_zealots()

    def train_workers(self):
        for nexus in self.townhalls.ready.idle:
            if self.should_train_worker(nexus):
                self.train_in(nexus, Id.PROBE)

    def should_train_worker(self, nexus) -> bool:
        return self.supply_workers < self.need_workers()

    def train_zealots(self):
        for gateway in self.structures(Id.GATEWAY).ready.idle:
            self.train_in(gateway, Id.ZEALOT)

    def train_in(self, building, unit_id):
        self.do(building.train(unit_id), subtract_cost=True, subtract_supply=True, can_afford_check=True)
