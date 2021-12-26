# Derivative scheme
def derivative(A, schema='upwind', order='first') :
    """
    Compute the derivative of the array A

    Parameters
    ----------
    A : array
        f(x)
    schema : str, optional, [upwind/centered]
        Define the differentiation schema, by default 'upwind'
    order : str, optional, [first/second/third]
        Define the order of the derivative schema, by default 'first'

    Returns
    -------
    array
        Derivative of the array A
    """    
    dA = []
    if schema == 'upwind' :
        if order == 'first' : 
            for i in range(1,len(A)) :
                dA.append(A[i]-A[i-1])
        if order == 'second' :
            for i in range(2,len(A)) : 
                dA.append((3*A[i] - 4*A[i-1] + A[i-2])*0.5)
        if order == 'third' :
            for i in range(3,len(A)) :
                dA.append((11*A[i] - 18*A[i-1] + 9*A[i-2] - 2*A[i-3])/6)
                
    if schema == 'centered' :
        if order == 'second' :
            for i in range(1,len(A)-1) :
                dA.append((A[i+1] - A[i-1])*0.5)
    return dA


def nearest(items, pivot):
    """
    Calculate the closest item to the pivot value

    Parameters
    ----------
    items : array
        Array which contains the list of dates to lookup in
    pivot : type(array[0])
        Reference value

    Returns
    -------
    type(array[0])
        Item in items array which is the closest to the pivot ones
    """    
    return min(items, key=lambda x: abs(x - pivot))


def nearest_yesterday(items, pivot):
    """
    Calculate the closest passed item to the pivot value 

    Parameters
    ----------
    items : array
        Array which contains the list of dates to lookup in
    pivot : type(array[0])
        Reference value

    Returns
    -------
    type(array[0])
        Item in items array which is the closest to the pivot ones
    """ 
    i = 0
    while items[i] < pivot :
        i += 1
        if i == len(items) : break
    return items[i-1]


def computeMinMax(arr,length=200, tollerance=1.5) :
    """
    Compute mins and maxs of the array

    Parameters
    ----------
    arr : list
        f(x)
    length : int, optional
        Window length of computation, by default 200
    tollerance : float, optional
        Percentual tollerance which determines if values are 
        too close to each other to be declared extremant points, by default 1.5

    Returns
    -------
    list
        List of maxima
    list
        List of minima
    """        
    maxima = [];    minima = []
    # Compute for the last n values
    length = len(arr) - length
    for i in range(length,len(arr)-1) : 
        if arr[i-1] < arr[i] > arr[i+1] :
            if maxima == [] : maxima.append(arr.index[i]) 
            if minima != [] :
                if (((arr[maxima[-1]]+arr[maxima[-1]]*0.01*tollerance) >= arr[i]) \
                    and (((arr[maxima[-1]]-arr[maxima[-1]]*0.01*tollerance) <= arr[i]))
                    or
                    ((arr[minima[-1]]+arr[minima[-1]]*0.01*tollerance) >= arr[i] ) \
                    and ((arr[minima[-1]]-arr[minima[-1]]*0.01*tollerance <= arr[i]))): continue
                maxima.append(arr.index[i]) 
        if arr[i-1] > arr[i] < arr[i+1] :
            if minima == [] : minima.append(arr.index[i]) 
            if maxima != [] :
                if (((arr[minima[-1]]+arr[minima[-1]]*0.01*tollerance) >= arr[i] ) \
                    and ((arr[minima[-1]]-arr[minima[-1]]*0.01*tollerance <= arr[i]))
                    or
                    ((arr[maxima[-1]]+arr[maxima[-1]]*0.01*tollerance) >= arr[i]) \
                    and (((arr[maxima[-1]]-arr[maxima[-1]]*0.01*tollerance) <= arr[i]))): continue
            minima.append(arr.index[i]) 

    i = len(arr)-1
    if arr[-2] < arr[-1] : maxima.append(arr.index[-1]) 
    if arr[-2] > arr[-1] : minima.append(arr.index[-1])
    return maxima[1:], minima[1:]


def ColNum2ColName(n):
   convertString = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
   base = 26
   i = n - 1

   if i < base:
      return convertString[i]
   else:
      return ColNum2ColName(i//base) + convertString[i%base]