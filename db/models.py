from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.init_db import Base


# ----------------------------
# Instruments
# ----------------------------
class AllInstrumentsList(Base):
    __tablename__ = "all_instruments_list"

    id = Column(Integer, primary_key=True, index=True)
    sem_exm_exch_id = Column(String)               # e.g., BSE, NSE, MCX
    sem_segment = Column(String)                   # Segment code (e.g., C)
    sem_smst_security_id = Column(String)          # Unique security ID
    sem_instrument_name = Column(String)           # e.g., FUTSTK, OPTIDX, EQUITY
    sem_expiry_code = Column(String)
    sem_trading_symbol = Column(String)
    sem_lot_units = Column(String)
    sem_custom_symbol = Column(String)
    sem_expiry_date = Column(String)               # Stored as string
    sem_strike_price = Column(String)
    sem_option_type = Column(String)               # CE / PE / XX / NULL
    sem_tick_size = Column(String)
    sem_expiry_flag = Column(String)               # M / W / D
    sem_exch_instrument_type = Column(String)
    sem_series = Column(String)
    sm_symbol_name = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


class InstrumentMaster(Base):
    __tablename__ = "instrument_master"

    security_id = Column(Integer, nullable=False)
    exchange_segment = Column(String, nullable=False)  # <- Required in PK

    trading_symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    segment = Column(String, nullable=False)
    instrument = Column(String, nullable=False)

    underlying = Column(String)
    expiry_code = Column(Integer)
    expiry_flag = Column(String)
    expiry_date = Column(Date)
    option_type = Column(String)
    strike_price = Column(Float)
    lot_size = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint('security_id', 'exchange_segment'),
    )


# ----------------------------
# Trading Plans & Live Trades
# ----------------------------
class TradePlan(Base):
    __tablename__ = "trade_plan"

    trade_id = Column(Integer, primary_key=True, index=True)
    trading_symbol = Column(String, nullable=False)
    exchange = Column(String, default="NSE")
    instrument = Column(String, nullable=False)

    time_frame = Column(String, nullable=False)  # Daily, Hourly, 15 Min
    trade_direction = Column(String, nullable=False)  # e.g., Bullish, Mild Bullish, Bearish, Mild Bearish, Sideways
    trade_type = Column(String, nullable=False)       # e.g., Swing, Momentum, Neutral
    trade_setup = Column(String, nullable=False)      # e.g. Breakout, double bottom, inverted head and shoulder

    entry_price = Column(Float)
    stop_loss = Column(Float)
    target_price = Column(Float)

    signal = Column(String)  # BUY / SELL / None
    probability = Column(String)       # High, Medium, Low
    score = Column(Float)    # Computed score from setup logic

    execution_strategy = Column(String)     # Option Strategy

    execution_flag = Column(String, default="Disabled")  # Enable, Traded, Exited, Disabled
    status = Column(String)  # Pending / Executed / Exited

    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LiveTrade(Base):
    __tablename__ = "live_trades"

    id = Column(Integer, primary_key=True, index=True)  # Restored for unique record identification
    trade_id = Column(Integer, nullable=False)           # Group identifier for multi-leg strategies

    trading_symbol = Column(String, nullable=False)
    exchange = Column(String, default="NSE")
    instrument = Column(String, nullable=False)

    ltp = Column(Float)
    transaction_type = Column(String)  # BUY / SELL

    entry_order_id = Column(String)
    entry_price = Column(Float)
    entry_quantity = Column(Integer)
    entry_date = Column(DateTime, default=datetime.utcnow)
    entry_time = Column(String)

    exit_order_id = Column(String, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_quantity = Column(Integer, nullable=True)
    exit_date = Column(DateTime, nullable=True)
    exit_time = Column(String, nullable=True)

    status = Column(String, default="Traded")
    remark = Column(String)


# ----------------------------
# Trade Logs
# ----------------------------
class TradeLog(Base):
    __tablename__ = "trade_log"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String, nullable=False)
    trading_symbol = Column(String, nullable=False)
    exchange = Column(String, default="NSE")
    instrument = Column(String, nullable=False)

    trade_direction = Column(String, nullable=False)
    trade_type = Column(String, nullable=False)
    trade_setup = Column(String, nullable=False)
    probability = Column(String, nullable=False)
    execution_strategy = Column(String, nullable=False)

    entry_date = Column(DateTime)
    entry_time = Column(String)
    exit_date = Column(DateTime)
    exit_time = Column(String)

    pnl = Column(Float)
    roi = Column(String)
    risk_reward = Column(String)
    holding_period = Column(String)

    remark = Column(String)
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


class TradeLogDetail(Base):
    __tablename__ = "trade_log_detail"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String, nullable=False)
    trading_symbol = Column(String, nullable=False)
    exchange = Column(String, default="NSE")
    instrument = Column(String, nullable=False)

    entry_order_id = Column(String)
    entry_price = Column(Float)
    entry_quantity = Column(Integer)

    exit_order_id = Column(String, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_quantity = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ----------------------------
# Ledger & History
# ----------------------------
class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, index=True)
    dhan_client_id = Column(String, nullable=False)
    order_id = Column(String)
    exchange_order_id = Column(String)
    exchange_trade_id = Column(String)
    transaction_type = Column(String)
    exchange_segment = Column(String)
    product_type = Column(String)
    order_type = Column(String)

    trading_symbol = Column(String)
    custom_symbol = Column(String)
    security_id = Column(String)
    traded_quantity = Column(Integer)
    traded_price = Column(Float)
    isin = Column(String)
    instrument = Column(String)

    sebi_tax = Column(Float)
    stt = Column(Float)
    brokerage_charges = Column(Float)
    service_tax = Column(Float)
    exchange_transaction_charges = Column(Float)
    stamp_duty = Column(Float)

    exchange_time = Column(DateTime)  # Convert from "2022-12-30 10:00:46"
    drv_expiry_date = Column(String)  # Still storing as string (optional)
    drv_option_type = Column(String)
    drv_strike_price = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)


class LedgerReport(Base):
    __tablename__ = "ledger_report"

    id = Column(Integer, primary_key=True, index=True)
    dhan_client_id = Column(String, nullable=False)
    narration = Column(String)
    voucher_date = Column(DateTime)  # Should be parsed from "Jun 22, 2022"
    exchange = Column(String)
    voucher_desc = Column(String)
    voucher_number = Column(String)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    running_balance = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)


# ----------------------------
# Indicator Data Storage
# ----------------------------
class IndicatorData(Base):
    __tablename__ = 'indicator_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trading_symbol = Column(String)
    security_id = Column(String)
    exchange_segment = Column(String)
    timeframe = Column(String)
    datetime = Column(DateTime)

    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    vwap = Column(Float)
    volume_sma_10 = Column(Float)

    ha_open = Column(Float)
    ha_high = Column(Float)
    ha_low = Column(Float)
    ha_close = Column(Float)

    # EMA
    ema_5 = Column(Float)
    ema_13 = Column(Float)
    ema_25 = Column(Float)
    ema_50 = Column(Float)
    ema_100 = Column(Float)
    ema_200 = Column(Float)

    # RSI, MACD
    rsi_14 = Column(Float)
    macd_line = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)

    # Stochastic
    stochastic_k = Column(Float)
    stochastic_d = Column(Float)

    # Bollinger Bands
    bollinger_upper_2 = Column(Float)
    bollinger_middle_2 = Column(Float)
    bollinger_lower_2 = Column(Float)
    bollinger_upper_3 = Column(Float)
    bollinger_middle_3 = Column(Float)
    bollinger_lower_3 = Column(Float)

    # DMI
    plus_di_14 = Column(Float)
    minus_di_14 = Column(Float)
    adx_14 = Column(Float)

    # Volatility
    atr_14 = Column(Float)
    historic_volatility = Column(Float)

    # Supertrend
    supertrend = Column(String)  # Stored as 'True' or 'False' string
