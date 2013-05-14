from collections import namedtuple
from operator    import itemgetter

def smooth(iq_data, alpha=1, today=None):
    """Perform exponential smoothing with factor `alpha`.

    Time period is a day.
    Each time period the value of `iq` drops `alpha` times.
    The most recent data is the most valuable one.
    """
    assert 0 < alpha <= 1

    if alpha == 1: # no smoothing
        return sum(map(itemgetter(1), iq_data))

    if today is None:
        today = max(map(itemgetter(0), iq_data))
    print today
    return sum(alpha**((today - date).days) * iq for date, iq in iq_data)

IQData = namedtuple("IQData", "date iq")

if __name__ == "__main__":
    from datetime import date

    days = [date(2008,1,1), date(2008,1,2), date(2008,1,7)]
    IQ = [110, 105, 90]
    iqdata = list(map(IQData, days, IQ))
    print("\n".join(map(str, iqdata)))
    today=date(2008, 1, 8)
    print(smooth(iqdata, alpha=0.5,today=today))