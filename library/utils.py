# Upwind derivative scheme
def derivative(A) :
    dA = []
    for i in range(1:len(A)) :
        dA.append(A[i]-A[-1])
    return dA