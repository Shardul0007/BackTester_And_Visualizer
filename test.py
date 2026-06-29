from datetime import date

from models.enums import *
from models.instrument import Instrument

instrument = Instrument(
    underlying=Underlying.NIFTY,
    instrument_type=InstrumentType.OPTION,
    expiry=date(2022, 11, 3),
    strike=24500,
    option_type=OptionType.CALL,
    symbol="NIFTY22110324500CE",
)

print(instrument)
print(instrument.is_option)
print(instrument.display_name)