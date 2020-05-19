import numpy as np

side_vertex_pixel_threshold = 0.9
trunc_threshold = 0.1
feature_layers_range = range(5, 1, -1)
pixel_size = 2 ** feature_layers_range[-1]
segment_region_threshold = 10
epsilon = 1e-4

def should_merge(region, i, j):
    neighbor = {(i, j - 1)}
    return not region.isdisjoint(neighbor)

    
def region_neighbor(region_set):
    region_pixels = np.array(list(region_set))
    j_min = np.amin(region_pixels, axis=0)[1] - 1
    j_max = np.amax(region_pixels, axis=0)[1] + 1
    i_m = np.amin(region_pixels, axis=0)[0] + 1
    region_pixels[:, 0] += 1
    neighbor = {(region_pixels[n, 0], region_pixels[n, 1]) for n in range(len(region_pixels))}
    neighbor.add((i_m, j_min))
    neighbor.add((i_m, j_max))
    return neighbor


def region_group(region_list):
    S = [i for i in range(len(region_list))]
    D = []
    while len(S) > 0:
        m = S.pop(0)
        if len(S) == 0:
            # S has only one element, put it to D
            D.append([m])
        else:
            D.append(rec_region_merge(region_list, m, S))
    return D


def rec_region_merge(region_list, m, S):
    rows = [m]
    tmp = []
    for n in S:
        if not region_neighbor(region_list[m]).isdisjoint(region_list[n]) or \
                not region_neighbor(region_list[n]).isdisjoint(region_list[m]):
            # 第m与n相交
            tmp.append(n)
    for d in tmp:
        S.remove(d)
    for e in tmp:
        rows.extend(rec_region_merge(region_list, e, S))
    return rows


def nms(predict, activation_pixels, threshold=side_vertex_pixel_threshold):
    region_list = []
    for i, j in zip(activation_pixels[0], activation_pixels[1]):
        merge = False
        for k in range(len(region_list)):
            if should_merge(region_list[k], i, j):            
                region_list[k].add((i, j))
                merge = True
                
        if not merge:
            region_list.append({(i, j)})
    D = region_group(region_list)
    quad_list = np.zeros((len(D), 4, 2))
    score_list = np.zeros((len(D), 4))
    for group, g_th in zip(D, range(len(D))):
        total_score = np.zeros((4, 2))
        prev_p_v_0 = None
        prev_p_v_1 = None   
        yellow_list = []
        green_list = []
        # Firstly find the left-most yellow one and right-most green one
        for row in group:
            for ij in region_list[row]:
                score = predict[ij[0], ij[1], 1]
                if score >= threshold:
                    ith_score = predict[ij[0], ij[1], 2:3]
                    if not (trunc_threshold <= ith_score < 1 - trunc_threshold):
                        ith = int(np.around(ith_score))
                        px = (ij[1] + 0.5) * pixel_size
                        py = (ij[0] + 0.5) * pixel_size
                        if ith == 0:
                            if prev_p_v_0 == None:
                                prev_p_v_0 = [px, py]
                            else:
                                if prev_p_v_0[0] > px:
                                    prev_p_v_0[0] = px
                                    prev_p_v_0[1] = py
                        if ith == 1:
                            if prev_p_v_1 == None:
                                prev_p_v_1 = [px, py]
                            else:
                                if prev_p_v_1[0] < px:
                                    prev_p_v_1[0] = px
                                    prev_p_v_1[1] = py
        yellow_list.append(prev_p_v_0)
        green_list.append(prev_p_v_1)
        
        for row in group:
            for ij in region_list[row]:
                score = predict[ij[0], ij[1], 1]
                if score >= threshold:
                    ith_score = predict[ij[0], ij[1], 2:3]
                    if not (trunc_threshold <= ith_score < 1 - trunc_threshold):
                        ith = int(np.around(ith_score))
                        px = (ij[1] + 0.5) * pixel_size
                        py = (ij[0] + 0.5) * pixel_size
                        if ith == 0:
                            FLAG = True
                            for item in yellow_list:
                                if abs(item[0] - px) > 10:
                                    FLAG = FLAG & True
                                else:
                                    FLAG = FLAG & False
                            if FLAG == True:
                                yellow_list.append([px, py])
                                
                        if ith == 1:
                            FLAG = True
                            for item in green_list:
                                if abs(item[0] - px) > 10:
                                    FLAG = FLAG & True
                                else:
                                    FLAG = FLAG & False
                            if FLAG == True:
                                green_list.append([px, py])
        # We divided connected regions into more segments only when # of heads == # of tails 
        if len(green_list) != 1 and len(yellow_list)!= 1 and len(green_list) == len(yellow_list):
            green_list = sorted(green_list)
            yellow_list = sorted(yellow_list)
            for ls in range(len(green_list)):
                prev_p_v_0 = yellow_list[ls]
                prev_p_v_1 = green_list[ls]
                total_score = np.zeros((4, 2))
                tmp = np.zeros((1, 4, 2))
                for row in group:
                    for ij in region_list[row]:
                        score = predict[ij[0], ij[1], 1]
                        if score >= threshold:
                            ith_score = predict[ij[0], ij[1], 2:3]
                            if not (trunc_threshold <= ith_score < 1 - trunc_threshold):
                                ith = int(np.around(ith_score))
                                px = (ij[1] + 0.5) * pixel_size
                                py = (ij[0] + 0.5) * pixel_size
                                if ith == 0:
                                    if prev_p_v_0 == None:
                                        prev_p_v_0 = [px, py]
                                    else:
                                        if abs(prev_p_v_0[0] - px) > segment_region_threshold:
                                            continue
                                if ith == 1:
                                    if prev_p_v_1 == None:
                                        prev_p_v_1 = [px, py]
                                    else:
                                        if abs(prev_p_v_1[0] - px) > segment_region_threshold:
                                            continue
                                
                                total_score[ith * 2:(ith + 1) * 2] += score
                                p_v = [px, py] + np.reshape(predict[ij[0], ij[1], 3:7],
                                                      (2, 2)) # Expand
                                tmp[0, ith * 2:(ith + 1) * 2] += score * p_v
                                    
                
                if not quad_list[g_th].all():
                    score_list[g_th] = total_score[:, 0]
                    quad_list[g_th] = tmp[0]
                    quad_list[g_th] /= (total_score + epsilon)
                else:
                    tmp[0] /= (total_score + epsilon)
                    quad_list = np.concatenate((quad_list, tmp))
                    score_list = np.concatenate((score_list,np.resize(total_score[:,0], (1,4))))
            
        else: # We don't have multiple green/yellow boxes in a merged regions
            for row in group:
                for ij in region_list[row]:
                    score = predict[ij[0], ij[1], 1]
                    if score >= threshold:
                        ith_score = predict[ij[0], ij[1], 2:3]
                        if not (trunc_threshold <= ith_score < 1 - trunc_threshold):
                            ith = int(np.around(ith_score))
                            px = (ij[1] + 0.5) * pixel_size
                            py = (ij[0] + 0.5) * pixel_size
                            if ith == 0:
                                if prev_p_v_0 == None:
                                    prev_p_v_0 = [px, py]
                                else:
                                    if abs(prev_p_v_0[0] - px) > segment_region_threshold:
                                        continue
                            if ith == 1:
                                if prev_p_v_1 == None:
                                    prev_p_v_1 = [px, py]
                                else:
                                    if abs(prev_p_v_1[0] - px) > segment_region_threshold:
                                        continue
                            
                            total_score[ith * 2:(ith + 1) * 2] += score
                            p_v = [px, py] + np.reshape(predict[ij[0], ij[1], 3:7],
                                                  (2, 2)) # Expand
                            quad_list[g_th, ith * 2:(ith + 1) * 2] += score * p_v
                                
            score_list[g_th] = total_score[:, 0]
            quad_list[g_th] /= (total_score + epsilon)
    return score_list, quad_list
