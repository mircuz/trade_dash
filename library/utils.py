# Derivative scheme
def derivative(A, schema='upwind', order='first') :
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





def computeMinMax(arr,length=200) :
        """
        Compute local Maximum and Minimum in the last length days

        Returns
        -------
        list 
            List of the local Maximum of the stock
        list
            List of the local minimum of the stock 
        """
        maxima = [];    minima = []
        # Compute for the last n values
        length = len(arr) - length
        for i in range(length,len(arr)-1) : 
            if arr[i-1] < arr[i] > arr[i+1] :
                maxima.append(arr.index[i]) 
            if arr[i-1] > arr[i] < arr[i+1] :
                minima.append(arr.index[i]) 
        return maxima, minima