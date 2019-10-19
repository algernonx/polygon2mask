import numpy as np
from collections import defaultdict


def polygon2mask(image_size, polygon, exist_mask=None):
    # image_size: [H, W].
    # polygon: the coordinate of polygon, format such as [x1,y1,x2,y2,...,xn,yn].
    # return: mask numpy of image_size, 1 means points in polygon.
    # attention: border points on mask are all 1.

    # --------------------------------------------------------------------------
    # -------------------------internal functions-------------------------------
    # --------------------------------------------------------------------------
    def double_int_judge(a_tuple):
        if (a_tuple[0] == int(a_tuple[0])) and (a_tuple[1] == int(a_tuple[1])):
            if int(a_tuple[1]) < image_size[0] and int(a_tuple[0]) < image_size[1]:
                mask[int(a_tuple[1]), int(a_tuple[0])] = 1

    def cal_slope(p1, p2, return_d=True, return_k=True):
        # pi is a tuple:(xi, yi)
        # d > 0 : p1->p2 towards down
        if return_k:
            if p1[0] == p2[0]:
                k = None
            else:
                k = (p2[1] - p1[1]) * 1.0 / (p2[0] - p1[0])
        else:
            k = None
        if return_d:
            if p2[1] != p1[1]:
                d = (p2[1] - p1[1]) / abs(p2[1] - p1[1])
            else:
                d = 0
        else:
            d = None
        return k, d

    def find_border_points(last_p, current_p):
        double_int_judge(last_p)
        double_int_judge(current_p)

        x1, y1 = last_p
        x2, y2 = current_p

        k, d = cal_slope(last_p, current_p)

        if k == 0:
            if int(y1) == y1:
                x_start = min(x1, x2)
                x_end = max(x1, x2)
                if int(y1) < image_size[0]:
                    mask[int(y1), int(x_start):int(x_end) + 1] = 1
            else:
                return
        else:
            if d > 0:
                x_start, y_start = x1, y1
                x_end, y_end = x2, y2
            else:
                x_start, y_start = x2, y2
                x_end, y_end = x1, y1
            y_index_start = int(y_start) + 1
            y_index_end = int(np.ceil(y_end))

            if k is None:
                for y_index in range(y_index_start, y_index_end):
                    scan_border_dict[y_index].append(x_start)
                    scan_border_dict[y_index].sort()
            else:
                k_trans = 1.0 / k
                for y_index in range(y_index_start, y_index_end):
                    x = k_trans * (y_index - y_start) + x_start
                    scan_border_dict[y_index].append(x)
                    scan_border_dict[y_index].sort()

    # --------------------------------------------------------------------------
    # ------------------------------init variable-------------------------------
    # --------------------------------------------------------------------------
    co_num = len(polygon)
    assert co_num % 2 == 0
    points_num = int(len(polygon) / 2)

    # output mask
    if exist_mask is None:
        mask = np.zeros(image_size, dtype=np.float32)
    else:
        mask = exist_mask

    # scan_border: y->border_points
    scan_border_dict = defaultdict(list)

    # --------------------------------------------------------------------------
    # --------------first step: remove vertice on the same line-----------------
    # --------------------------------------------------------------------------
    points_after_filter = []
    for i in range(points_num):
        current_point = polygon[2 * i], polygon[2 * i + 1]
        last_point = polygon[2 * i - 2], polygon[2 * i - 1]
        next_point = polygon[(2 * i + 2) % co_num], polygon[(2 * i + 3) % co_num]
        k1, _ = cal_slope(last_point, current_point, return_d=False)
        k2, _ = cal_slope(current_point, next_point, return_d=False)
        if k1 != k2 and current_point != last_point:
            points_after_filter.append(current_point)
    points_num = len(points_after_filter)

    # --------------------------------------------------------------------------
    # ---------------------second step: generate border points------------------
    # --------------------------------------------------------------------------
    for i in range(points_num):
        last_point = points_after_filter[i - 1]
        current_point = points_after_filter[i]
        find_border_points(last_point, current_point)

    # --------------------------------------------------------------------------
    # ---third step: add good points to border_points(good points:d1*d2 >= 0)---
    # --------------------------------------------------------------------------
    for i in range(points_num):
        current_point = points_after_filter[i]
        y = int(current_point[1])
        if y != current_point[1]:
            continue
        last_point = points_after_filter[i - 1]
        next_point = points_after_filter[(i + 1) % points_num]
        _, d1 = cal_slope(last_point, current_point, return_k=False)
        if d1 == 0:
            continue
        else:
            _, d2 = cal_slope(current_point, next_point, return_k=False)
            if d2 == 0:
                next_point = points_after_filter[(i + 2) % points_num]
                _, d2 = cal_slope(current_point, next_point, return_k=False)

            if d1 * d2 > 0:
                scan_border_dict[y].append(current_point[0])
                scan_border_dict[y].sort()

    # --------------------------------------------------------------------------
    # ---------------------forth step: scan points in polygon-------------------
    # --------------------------------------------------------------------------
    for r in scan_border_dict.keys():
        c_list = scan_border_dict[r]
        assert len(c_list) % 2 == 0

        nps = int(len(c_list) / 2)
        for i in range(nps):
            c_start = c_list[2 * i]
            c_end = c_list[2 * i + 1]
            if r < image_size[0]:
                mask[r, int(np.ceil(c_start)):int(c_end) + 1] = 1

    return mask