def exp_movingAvg(array, win):
    SMA = float(sum(array[:win]))/win
    Multiplier = (2 / float(win + 1))
    EMA_array = [SMA] 
    i = 0 
    for item in array[win:]:
        s = (float(item)-EMA_array[i])*Multiplier + EMA_array[i] 
        EMA_array.append(s)
        i+=1
    #j=0
    #while j < (len(array)-len(EMA_array)):
    #    EMA_array.insert(0,None)
    #    j+=1
    return EMA_array

#from pylab import plot,show
from numpy import arange,array,ones,linalg
from signl.utils import * 
def li(reach):
    xi = arange(0,len(reach))
    xi = rescale(xi)
    A = array([ xi, ones(len(reach))])
    # linearly generated sequence
    #y = [19, 20, 20.5, 21.5, 22, 23, 23, 25.5, 24]
    w = linalg.lstsq(A.T,reach)[0] # obtaining the parameters
    return round(w[0],5)
    # plotting the line
    #line = w[0]*xi+w[1] # regression line
    #plot(xi,line,'r-',xi,reach,'o')
    #show()

from numpy import polyfit, polyder, linspace
def li2(reach):
    y = array(reach)
    x = linspace(1,len(y),len(y))
    [a,b] = polyfit(x,y,1)
    if a > 0:
        if max(y)-y[-1] < max(y)*.25:
            return a
        if max(y)-y[-1] <= max(y)*.25 and max(y)-y[-1] > max(y)*.5:
            return 0.5*a
        if max(y)-y[-1] <= max(y)*.5 and max(y)-y[-1] > max(y)*0.75:
            return 0.25*a
        else:
            return 0.1*a
    else:
        return a

def dayiter(start, end):
    one = dt.timedelta(days=1)
    day = start
    while day <= end:
        yield day
        day += one


def moving_average(mapping, window, dft=0):
    n = float(window)
    t1, t2 = tee(dayiter(min(mapping), max(mapping)))
    s = sum(mapping.get(day, dft) for day in islice(t2, window))
    yield s / n
    for olddate, newdate in izip(t1, t2):
        oldvalue = mapping.get(olddate, dft)
        newvalue = mapping.get(newdate, dft)
        s += newvalue - oldvalue
        yield s / n


def movingAverage(dataArray):
    inputArray = {}
    for item in dataArray:
        inputArray[item.date] = item.reach
    result =  moving_average(inputArray, window=4)
    response = []
    for item in result:
        response.append(item)
    return response
