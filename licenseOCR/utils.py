def isRayIntersectsSegment(poi, s_poi, e_poi):
    # 输入：判断点，边起点，边终点，都是[lng,lat]格式数组
    if s_poi[1] == e_poi[1]:   # 排除与射线平行、重合，线段首尾端点重合的情况
        return False
    if s_poi[1] > poi[1] and e_poi[1] > poi[1]:  # 线段在射线上边
        return False
    if s_poi[1] < poi[1] and e_poi[1] < poi[1]:  # 线段在射线下边
        return False
    if s_poi[1] == poi[1] and e_poi[1] > poi[1]:  # 交点为下端点，对应spoint
        return False
    if e_poi[1] == poi[1] and s_poi[1] > poi[1]:  # 交点为下端点，对应epoint
        return False
    if s_poi[0] < poi[0] and e_poi[1] < poi[1]:  # 线段在射线左边
        return False

    xseg = e_poi[0] - (e_poi[0] - s_poi[0]) * (e_poi[1] - poi[1]) / (e_poi[1] - s_poi[1])  # 求交
    if xseg < poi[0]:  # 交点在射线起点的左侧
        return False
    return True  # 排除上述情况之后

def isPoiWithinPoly(poi, poly):
    # 输入：点 poi = [x,y]，多边形 poly = [[x1,y1],[x2,y2],……,[xn,yn]]
    sinsc = 0  # 交点个数
    plen = len(poly)
    for i in range(plen):  # 循环检查每条边
        s_poi = poly[i]
        if i != plen - 1:
            e_poi = poly[i+1]
        else:
            e_poi = poly[0]
        if isRayIntersectsSegment(poi, s_poi, e_poi):
            sinsc += 1  # 有交点就加1
    return True if sinsc % 2 == 1 else False