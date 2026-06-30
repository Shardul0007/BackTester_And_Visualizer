"""
Execution Engine for converting TradingSignals to Orders.
"""


from models.enums import OrderAction, OptionType
from models.market_snapshot import MarketSnapshot
from models.order import Order
from models.trading_signal import TradingSignal, SignalType
from engine.portfolio import Portfolio
from models.instrument import Instrument


class ExecutionEngine:
    """
    Translates Strategy signals into concrete Orders, respecting
    current market prices and execution rules.
    """

    def process(
        self,
        signals: list[TradingSignal],
        snapshot: MarketSnapshot,
        portfolio: Portfolio
    ) -> list[Order]:
        """
        Convert signals into orders.
        """
        orders: list[Order] = []
        pending_instruments = set()
        
        for signal in signals:
            new_orders = self._process_signal(signal, snapshot, portfolio, pending_instruments)
            for order in new_orders:
                pending_instruments.add(order.instrument)
            orders.extend(new_orders)
            
        return orders

    def _process_signal(
        self, 
        signal: TradingSignal, 
        snapshot: MarketSnapshot, 
        portfolio: Portfolio,
        pending_instruments: set
    ) -> list[Order]:
        
        orders: list[Order] = []
        
        if signal.signal_type == SignalType.BUY_PAIR:
            if signal.strike not in snapshot.option_chain:
                return []
                
            pair = snapshot.option_chain[signal.strike]
            
            ce_held = (pair.call.instrument in portfolio.positions) or (pair.call.instrument in pending_instruments)
            pe_held = (pair.put.instrument in portfolio.positions) or (pair.put.instrument in pending_instruments)
            
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
                # EXIT_PAIR requires a live price from the current snapshot.
                # If the strike has dropped out of the chain there is no price
                # available for a normal mid-day roll, so skip this signal.
                # The end-of-day EXIT_ALL path handles missing strikes via the
                # portfolio.last_prices fallback in _resolve_exit_price().
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
                    price = self._resolve_exit_price(
                        instrument, snapshot, portfolio
                    )
                    if price is None:
                        continue
                    orders.append(
                        Order(
                            timestamp=snapshot.timestamp,
                            action=OrderAction.SELL,
                            instrument=instrument,
                            quantity=pos.quantity,
                            price=price,
                        )
                    )

        return orders

    def _resolve_exit_price(
        self,
        instrument: Instrument,
        snapshot: MarketSnapshot,
        portfolio: Portfolio,
    ) -> float | None:
        """
        Determine the exit price for an instrument.

        Preference order:
        1. Current snapshot option chain (most accurate).
        2. Last known price recorded in the portfolio (fallback for strikes
           that have dropped out of the chain on the final snapshot).

        Returns ``None`` only when no price is available at all, which
        indicates a data gap that cannot be recovered from.
        """
        strike = instrument.strike
        if strike in snapshot.option_chain:
            pair = snapshot.option_chain[strike]
            if instrument.option_type == OptionType.CALL:
                return pair.call.price
            return pair.put.price

        # Fallback: use the last price seen during mark-to-market updates.
        return portfolio.last_prices.get(instrument)
