import sc2

from sc2.constants import UnitTypeId as Id

MINERAL_WORKERS_PER_BASE = 16


class BBBot(sc2.BotAI):
    async def on_step(self, iteration):
        if iteration == 0:
            print("Game started")

        await self.macro()
        await self.war()

    def on_end(self, result):
        print("OnGameEnd() was called.")

    async def macro(self):
        await self.distribute_workers()
        await self.train_workers()
        await self.build_supply()
        await self.build_gateways()
        await self.train_zealots()

    async def war(self):
        if self.should_attack():
            self.attack()

    # Attack

    def attack(self):
        for zealot in self.units(Id.ZEALOT):
            target = self.find_target(zealot)
            self.do(zealot.attack(target))

    def should_attack(self):
        return self.supply_army >= 20

    def find_target(self, unit):
        targets = (self.enemy_units | self.enemy_structures).filter(lambda target: target.can_be_attacked)
        if targets:
            return targets.closest_to(unit)
        else:
            return self.enemy_start_locations[0]

    # Build

    async def build_supply(self):
        if self.should_build_supply() and self.can_afford(Id.PYLON):
            nexus = self.townhalls.ready.random
            await self.build(Id.PYLON, near=nexus)

    def should_build_supply(self):
        return (self.supply_left < 2 and self.already_pending(Id.PYLON) == 0) or (
                self.supply_used > 15 and self.supply_left < 6 and self.already_pending(Id.PYLON) < 2)

    async def build_gateways(self):
        if self.should_build_gateway() and self.can_afford(Id.GATEWAY):
            pylon = self.structures(Id.PYLON).ready.random
            await self.build(Id.GATEWAY, near=pylon)

    def should_build_gateway(self):
        return (
            self.structures(Id.PYLON).ready
            and self.already_pending(Id.GATEWAY) == 0
            and (
                not self.structures(Id.GATEWAY).ready
                or self.minerals > 300
            )
        )

    # Train

    async def train_workers(self):
        for nexus in self.townhalls.ready:
            if self.should_train_worker(nexus) and self.can_afford(Id.PROBE):
                self.do(nexus.train(Id.PROBE), subtract_cost=True, subtract_supply=True)

    def should_train_worker(self, nexus):
        return self.supply_workers < MINERAL_WORKERS_PER_BASE and nexus.is_idle

    async def train_zealots(self):
        for gateway in self.structures(Id.GATEWAY).ready.idle:
            if self.can_afford(Id.ZEALOT):
                self.do(gateway.train(Id.ZEALOT), subtract_cost=True, subtract_supply=True)
