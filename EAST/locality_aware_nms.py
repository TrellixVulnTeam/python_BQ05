#pylint: skip-file
'''nms'''
import numpy
from shapely.geometry import Polygon


def intersection(g, p):
    '''doc'''
    g = Polygon(g[:8].reshape((4, 2)))
    p = Polygon(p[:8].reshape((4, 2)))
    if not g.is_valid or not p.is_valid:
        return 0
    inter = Polygon(g).intersection(Polygon(p)).area
    union = g.area + p.area - inter
    if union == 0:
        return 0
    else:
        return inter/union


def weighted_merge(g, p):
    '''doc'''
    g[:8] = (g[8] * g[:8] + p[8] * p[:8])/(g[8] + p[8])
    g[8] = (g[8] + p[8])
    return g


def standard_nms(S, thres):
    '''doc'''
    order = numpy.argsort(S[:, 8])[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        ovr = numpy.array([intersection(S[i], S[t]) for t in order[1:]])

        inds = numpy.where(ovr <= thres)[0]
        order = order[inds+1]

    return S[keep]


def nms_locality(polys, thres=0.3):
    '''
    locality aware nms of EAST
    :param polys: a N*9 numpy array. first 8 coordinates, then prob
    :return: boxes after nms
    '''
    S = []
    p = None
    for g in polys:
        if p is not None and intersection(g, p) > thres:
            p = weighted_merge(g, p)
        else:
            if p is not None:
                S.append(p)
            p = g
    if p is not None:
        S.append(p)

    if len(S) == 0:
        return numpy.array([])
    return standard_nms(numpy.array(S), thres)


if __name__ == '__main__':
    '''doc'''
    # 343,350,448,135,474,143,369,359
    print(Polygon(numpy.array([[343, 350], [448, 135],
                            [474, 143], [369, 359]])).area)
