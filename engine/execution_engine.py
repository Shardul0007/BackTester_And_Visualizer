"""
Execution Engine for converting TradingSignals to Orders.
"""

from typing import List

from models.enums import OrderAction, OptionType
from models.market_snapshot import MarketSnapshot
from models.order import Order
from models.trading_signal import TradingSignal, SignalType
from engine.portfolio import Portfolio


class ExecutionEngine:
    """
    Translates Strategy signals into concrete Orders, respecting
    current market prices and execution rules.
    """

    def process(
        self, 
        signals: List[TradingSignal], 
        snapshot: MarketSnapshot, 
        portfolio: Portfolio
    ) -> List[Order]:
        """
        Convert signals into orders.
        """
        orders: List[Order] = []
        
        for signal in signals:
            orders.extend(self._process_signal(signal, snapshot, portfolio))
            
        return orders

    def _process_signal(
        self, 
        signal: TradingSignal, 
        snapshot: MarketSnapshot, 
        portfolio: Portfolio
    ) -> List[Order]:
        
        orders: List[Order] = []
        
        if signal.signal_type == SignalType.BUY_PAIR:
            if signal.strike not in snapshot.option_chain:
                return []
                
            pair = snapshot.option_chain[signal.strike]
            
            ce_held = pair.call.instrument in portfolio.positions
            pe_held = pair.put.instrument in portfolio.positions
            
            quantity = 1 
            
            if not ce_held:
                orders.append(
                    Order(
                        timestamp=snapshot.timestamp,
                        action=OrderAction.BUY,
                        instrument=pair.call.instrument,
                        quantity=quantity,
                        price=pair.call.price
                    )
                )
            if not pe_held:
                orders.append(
                    Order(
                        timestamp=snapshot.timestamp,
                        action=OrderAction.BUY,
                        instrument=pair.put.instrument,
                        quantity=quantity,
                        price=pair.put.price
                    )
                )
                
        elif signal.signal_type == SignalType.EXIT_PAIR:
            if signal.strike not in snapshot.option_chain:
                # Still try to exit if not in chain? We need a price to exit.
                # Since we don't have a price in the current snapshot, skip for now.
                return []
                
            pair = snapshot.option_chain[signal.strike]
            
            if pair.call.instrument in portfolio.positions:
                pos = portfolio.positions[pair.call.instrument]
                orders.append(
                    Order(
                        timestamp=snapshot.timestamp,
                        action=OrderAction.SELL,
                        instrument=pos.instrument,
                        quantity=pos.quantity,
                        price=pair.call.price
                    )
                )
                
            if pair.put.instrument in portfolio.positions:
                pos = portfolio.positions[pair.put.instrument]
                orders.append(
                    Order(
                        timestamp=snapshot.timestamp,
                        action=OrderAction.SELL,
                        instrument=pos.instrument,
                        quantity=pos.quantity,
                        price=pair.put.price
                    )
                )
                
        elif signal.signal_type == SignalType.EXIT_ALL:
            for instrument, pos in portfolio.positions.items():
                if instrument.underlying == signal.underlying:
                    strike = instrument.strike
                    if strike in snapshot.option_chain:
                        pair = snapshot.option_chain[strike]
                        if instrument.option_type == OptionType.CALL:
                            price = pair.call.price
                        else:
                            price = pair.put.price
                            
                        orders.append(
                            Order(
                                timestamp=snapshot.timestamp,
                                action=OrderAction.SELL,
                                instrument=instrument,
                                quantity=pos.quantity,
                                price=price
                            )
                        )
                    
        return orders
