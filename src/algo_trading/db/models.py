# File: src/algo_trading/db/models.py
"""
SQLModel models translated from your previous SQLAlchemy models.
Keep these models in sync with Alembic migrations when you move to production.
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import PrimaryKeyConstraint, Integer, String


# --- users & accounts (starter) ---
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    last_name: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    email: Optional[str] = Field(default=None, sa_column=Column(String, unique=True, index=True))
    password_hash: Optional[str] = None
    dhan_client_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- instruments / master lists ---
class AllInstrumentsList(SQLModel, table=True):
    __tablename__ = "all_instruments_list"
    id: Optional[int] = Field(default=None, primary_key=True)
    sem_exm_exch_id: Optional[str] = Field(default=None)
    sem_segment: Optional[str] = Field(default=None)
    sem_smst_security_id: Optional[str] = Field(default=None)
    sem_instrument_name: Optional[str] = Field(default=None)
    sem_expiry_code: Optional[str] = Field(default=None)
    sem_trading_symbol: Optional[str] = Field(default=None)
    sem_lot_units: Optional[str] = Field(default=None)
    sem_custom_symbol: Optional[str] = Field(default=None)
    sem_expiry_date: Optional[str] = Field(default=None)
    sem_strike_price: Optional[str] = Field(default=None)
    sem_option_type: Optional[str] = Field(default=None)
    sem_tick_size: Optional[str] = Field(default=None)
    sem_expiry_flag: Optional[str] = Field(default=None)
    sem_exch_instrument_type: Optional[str] = Field(default=None)
    sem_series: Optional[str] = Field(default=None)
    sm_symbol_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InstrumentMaster(SQLModel, table=True):
    __tablename__ = "instrument_master"

    # composite PK: security_id + exchange_segment
    security_id: int = Field(sa_column=Column("security_id", Integer, primary_key=True))
    exchange_segment: str = Field(sa_column=Column("exchange_segment", String(length=64), primary_key=True))

    trading_symbol: Optional[str] = Field(default=None)
    exchange: Optional[str] = Field(default=None)
    segment: Optional[str] = Field(default=None)
    instrument: Optional[str] = Field(default=None)

    underlying: Optional[str] = Field(default=None)
    expiry_code: Optional[int] = Field(default=None)
    expiry_flag: Optional[str] = Field(default=None)
    expiry_date: Optional[date] = Field(default=None)
    option_type: Optional[str] = Field(default=None)
    strike_price: Optional[float] = Field(default=None)
    lot_size: Optional[int] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (PrimaryKeyConstraint("security_id", "exchange_segment"),)


# --- trade plan / user-saved opportunities ---
class TradePlan(SQLModel, table=True):
    __tablename__ = "trade_plan"

    trade_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, nullable=True, index=True)  # multi-user mapping
    trading_symbol: str
    exchange: str = Field(default="NSE")
    instrument: str

    time_frame: str  # Daily, Hourly, 15 Min
    trade_direction: str  # e.g., Bullish, Bearish
    trade_type: str  # Swing, Momentum, Neutral
    trade_setup: str  # Breakout, double bottom, etc.

    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None

    signal: Optional[str] = None
    probability: Optional[str] = None
    score: Optional[float] = None

    execution_strategy: Optional[str] = None
    execution_flag: str = Field(default="Disabled")  # Disabled, Enabled, Traded, Exited
    status: Optional[str] = None  # Pending / Executed / Exited

    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# --- live trades (open positions) ---
class LiveTrade(SQLModel, table=True):
    __tablename__ = "live_trades"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, nullable=True, index=True)
    trade_id: Optional[int] = Field(default=None)  # group id for multi-leg strategies

    trading_symbol: str
    exchange: str = Field(default="NSE")
    instrument: str

    ltp: Optional[float] = None
    transaction_type: Optional[str] = None  # BUY / SELL

    entry_order_id: Optional[str] = None
    entry_price: Optional[float] = None
    entry_quantity: Optional[int] = None
    entry_date: Optional[datetime] = None
    entry_time: Optional[str] = None

    exit_order_id: Optional[str] = None
    exit_price: Optional[float] = None
    exit_quantity: Optional[int] = None
    exit_date: Optional[datetime] = None
    exit_time: Optional[str] = None

    status: str = Field(default="Traded")
    remark: Optional[str] = None


# --- trade log summary & detail ---
class TradeLog(SQLModel, table=True):
    __tablename__ = "trade_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, nullable=True, index=True)
    trade_id: Optional[str] = Field(default=None)
    trading_symbol: Optional[str] = Field(default=None)
    exchange: str = Field(default="NSE")
    instrument: Optional[str] = Field(default=None)

    trade_direction: Optional[str] = Field(default=None)
    trade_type: Optional[str] = Field(default=None)
    trade_setup: Optional[str] = Field(default=None)
    probability: Optional[str] = Field(default=None)
    execution_strategy: Optional[str] = Field(default=None)

    entry_date: Optional[datetime] = None
    entry_time: Optional[str] = None
    exit_date: Optional[datetime] = None
    exit_time: Optional[str] = None

    pnl: Optional[float] = None
    roi: Optional[str] = None
    risk_reward: Optional[str] = None
    holding_period: Optional[str] = None

    remark: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TradeLogDetail(SQLModel, table=True):
    __tablename__ = "trade_log_detail"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, nullable=True, index=True)
    trade_id: Optional[str] = Field(default=None)
    trading_symbol: Optional[str] = Field(default=None)
    exchange: str = Field(default="NSE")
    instrument: Optional[str] = Field(default=None)

    entry_order_id: Optional[str] = None
    entry_price: Optional[float] = None
    entry_quantity: Optional[int] = None

    exit_order_id: Optional[str] = None
    exit_price: Optional[float] = None
    exit_quantity: Optional[int] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- history, ledger, indicators ---
class TradeHistory(SQLModel, table=True):
    __tablename__ = "trade_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, nullable=True, index=True)
    order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None
    exchange_trade_id: Optional[str] = None
    transaction_type: Optional[str] = None
    exchange_segment: Optional[str] = None
    product_type: Optional[str] = None
    order_type: Optional[str] = None

    trading_symbol: Optional[str] = None
    custom_symbol: Optional[str] = None
    security_id: Optional[str] = None
    traded_quantity: Optional[int] = None
    traded_price: Optional[float] = None
    isin: Optional[str] = None
    instrument: Optional[str] = None

    sebi_tax: Optional[float] = None
    stt: Optional[float] = None
    brokerage_charges: Optional[float] = None
    service_tax: Optional[float] = None
    exchange_transaction_charges: Optional[float] = None
    stamp_duty: Optional[float] = None

    exchange_time: Optional[datetime] = None
    drv_expiry_date: Optional[str] = None
    drv_option_type: Optional[str] = None
    drv_strike_price: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class LedgerReport(SQLModel, table=True):
    __tablename__ = "ledger_report"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, nullable=True, index=True)
    narration: Optional[str] = None
    voucher_date: Optional[datetime] = None
    exchange: Optional[str] = None
    voucher_desc: Optional[str] = None
    voucher_number: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    running_balance: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class IndicatorData(SQLModel, table=True):
    __tablename__ = "indicator_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    trading_symbol: Optional[str] = None
    security_id: Optional[str] = None
    exchange_segment: Optional[str] = None
    timeframe: Optional[str] = None
    datetime: Optional[datetime] = None

    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    vwap: Optional[float] = None
    volume_sma_10: Optional[float] = None

    ha_open: Optional[float] = None
    ha_high: Optional[float] = None
    ha_low: Optional[float] = None
    ha_close: Optional[float] = None

    # EMA
    ema_5: Optional[float] = None
    ema_13: Optional[float] = None
    ema_26: Optional[float] = None
    ema_50: Optional[float] = None
    ema_100: Optional[float] = None
    ema_200: Optional[float] = None

    # RSI, MACD
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None

    # Stochastic
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None

    # Bollinger Bands
    bollinger_upper_2: Optional[float] = None
    bollinger_middle_2: Optional[float] = None
    bollinger_lower_2: Optional[float] = None
    bollinger_upper_3: Optional[float] = None
    bollinger_middle_3: Optional[float] = None
    bollinger_lower_3: Optional[float] = None

    # DMI
    plus_di_14: Optional[float] = None
    minus_di_14: Optional[float] = None
    adx_14: Optional[float] = None

    # Volatility
    atr_14: Optional[float] = None
    historic_volatility: Optional[float] = None

    # Supertrend
    supertrend: Optional[str] = None  # Stored as 'True' or 'False' string
