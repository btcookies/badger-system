from helpers.multicall import functions, Call, func, as_wei
from helpers.sett.resolvers.StrategyCoreResolver import StrategyCoreResolver
from brownie import *

def confirm_harvest_badger_lp(before, after):
    """
    Harvest Should;
    - Increase the balanceOf() underlying asset in the Strategy
    - Reduce the amount of idle BADGER to zero
    - Increase the ppfs on sett
    """

    assert after.strategy.balanceOf >= before.strategy.balanceOf
    if before.sett.pricePerFullShare:
        assert after.sett.pricePerFullShare > before.sett.pricePerFullShare


class StrategyBadgerLpMetaFarmResolver(StrategyCoreResolver):
    def add_balances_snap(self, calls, entities):
        super().add_balances_snap(calls, entities)
        strategy = self.manager.strategy
        
        badger = interface.IERC20(strategy.badger())

        calls = self.add_entity_balances_for_tokens(calls, "badger", badger, entities)
        return calls
        
    def add_strategy_snap(self, calls, entities=None):
        strategy = self.manager.strategy
        staking_rewards_address = strategy.geyser()

        super().add_strategy_snap(calls)
        calls.append(
            Call(
                staking_rewards_address,
                [func.erc20.balanceOf, strategy.address],
                [["stakingRewards.staked", as_wei]],
            )
        )
        calls.append(
            Call(
                staking_rewards_address,
                [func.rewardPool.earned, strategy.address],
                [["stakingRewards.earned", as_wei]],
            )
        )

        return calls

    def confirm_harvest(self, before, after, tx):
        super().confirm_harvest(before, after, tx)
        # Strategy want should increase
        before_balance = before.get("strategy.balanceOf")
        assert after.get("strategy.balanceOf") >= before_balance if before_balance else 0

        # PPFS should not decrease
        assert after.get("sett.pricePerFullShare") >= before.get("sett.pricePerFullShare")

    def get_strategy_destinations(self):
        strategy = self.manager.strategy
        return {"stakingRewards": strategy.geyser()}
