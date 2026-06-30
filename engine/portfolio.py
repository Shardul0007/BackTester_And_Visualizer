"""
Portfolio component to track positions, trades, and PnL.
"""

from __future__ import annotations

from typing import Dict, List

from models.enums import OrderAction, PositionStatus, Underlying, OptionType
from models.instrument import Instrument
from models.market_snapshot import MarketSnapshot
from models.order import Order
from models.portfolio_view import PortfolioView
from models.position import Position
from models.trade import Trade


class Portfolio:
    """
    Maintains active positions, closed trades, and computes PnL.
    """

    def __init__(self, initial_cash: float = 0.0):
        self.cash: float = initial_cash
        self.positions: Dict[Instrument, Position] = {}
        self.trades: List[Trade] = []
        
        # PnL metrics
        self.realized_pnl: float = 0.0
        self.unrealized_pnl: float = 0.0
        self.mark_to_market_pnl: float = 0.0

    @property
    def portfolio_value(self) -> float:
        """Total value of portfolio (cash + unrealized PnL)."""
        return self.cash + self.unrealized_pnl

    def get_view(self, underlying: Underlying) -> PortfolioView:
        """
        Creates a read-only PortfolioView for the given underlying.
        Returns the strike currently held, if any.
        """
        held_strike = None
        for instrument, position in self.positions.items():
            if instrument.underlying == underlying and position.status == PositionStatus.OPEN:
                held_strike = instrument.strike
                break
                
        return PortfolioView(held_strike=held_strike)

    def apply_orders(self, orders: List[Order]) -> None:
        """
        Executes a list of orders, updating positions and cash.
        """
        for order in orders:
            self._apply_order(order)

    def _apply_order(self, order: Order) -> None:
        """
        Applies a single order to the portfolio.
        """
        if order.action == OrderAction.BUY:
            if order.instrument in self.positions:
                pos = self.positions[order.instrument]
                total_cost = (pos.quantity * pos.entry_price) + (order.quantity * order.price)
                pos.quantity += order.quantity
                pos.entry_price = total_cost / pos.quantity
            else:
                self.positions[order.instrument] = Position(
                    instrument=order.instrument,
                    quantity=order.quantity,
                    entry_time=order.timestamp,
                    entry_price=order.price,
                    status=PositionStatus.OPEN
                )
            self.cash -= order.quantity * order.price
            
        elif order.action == OrderAction.SELL:
            if order.instrument not in self.positions:
                raise ValueError(f"Cannot sell {order.instrument}: no open position.")
            
            pos = self.positions[order.instrument]
            if order.quantity > pos.quantity:
                raise ValueError(f"Cannot sell {order.quantity} of {order.instrument}: only {pos.quantity} held.")
            
            trade = Trade(
                instrument=order.instrument,
                quantity=order.quantity,
                entry_time=pos.entry_time,
                entry_price=pos.entry_price,
                exit_time=order.timestamp,
                exit_price=order.price
            )
            self.trades.append(trade)
            self.realized_pnl += trade.realized_pnl
            
            self.cash += order.quantity * order.price
            
            pos.quantity -= order.quantity
            if pos.quantity == 0:
                pos.status = PositionStatus.CLOSED
                del self.positions[order.instrument]

    def mark_to_market(self, snapshot: MarketSnapshot) -> None:
        """
        Updates unrealized PnL using the current market snapshot.
        """
        self.unrealized_pnl = 0.0
        
        for instrument, position in self.positions.items():
            if instrument.underlying == snapshot.future.instrument.underlying:
                strike = instrument.strike
                if strike in snapshot.option_chain:
                    pair = snapshot.option_chain[strike]
                    if instrument.option_type == OptionType.CALL:
                        current_price = pair.call.price
                    else:
                        current_price = pair.put.price
                    
                    self.unrealized_pnl += (current_price - position.entry_price) * position.quantity
                    
        self.mark_to_market_pnl = self.realized_pnl + self.unrealized_pnl
