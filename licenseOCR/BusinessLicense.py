import re
from .utils import isPoiWithinPoly
class BusinessLicense:

    def __init__(self, result):
        self.result = result
        self.box_levels = self.sort_ypos(self.result)
        self.res = {}
        self.license_type()     # 执照类型
        self.license_copy()     # 副本
        self.business_id()      # 注册号/统一社会信用代码
        self.business_name()    # 企业名称
        self.business_type()    # 企业类型
        self.address()          # 企业地址
        self.operator()         # 法定代表人/经营者
        self.registered_capital()   # 注册资本
        self.register_date()    # 注册日期
        self.business_term()    # 营业期限
        self.scope()            # 经营范围
        self.present_date()     # 颁发日期
        self.fixup_missing()    # 查缺补漏

    def sort_ypos(self, result):

        # 对文本框按y值进行排序
        sorted_by_ypos = sorted(result, key=lambda item: item['box'][1])
        box_levels = {}
        key = 0
        cur_ypos = sorted_by_ypos[0]['box'][1]
        y_threshold = abs(sorted_by_ypos[0]['box'][3] - sorted_by_ypos[0]['box'][1]) / 2
        box_levels[key] = []
        for item in sorted_by_ypos:
            # 以不超过第一个文本框高度的1/2为准
            if abs(item['box'][1] - cur_ypos) > y_threshold:
                key += 1
                box_levels[key] = []
                y_threshold = abs(item['box'][3] - item['box'][1]) / 2
            box_levels[key].append(item)
            cur_ypos = item['box'][1]

        # 对每一个key的文本框按x进行排序
        for key in box_levels:
            box_levels[key] = sorted(box_levels[key], key=lambda item: item['box'][0])
            # 添加对前后紧邻的box是否有很大重叠的检查。
            # 为简单，可以仅判断四边形的重心是否在另一个四边形内。
            if len(box_levels[key]) > 0:
                remove_overlaps = []
                remove_overlaps.append(box_levels[key][0])
                ahead_box = box_levels[key][0]['box']
                fbox = [
                    [ahead_box[0], ahead_box[1]],
                    [ahead_box[2], ahead_box[3]],
                    [ahead_box[4], ahead_box[5]],
                    [ahead_box[6], ahead_box[7]]
                ]
                for item in box_levels[key]:
                    point = [sum(item['box'][0::2])/4, sum(item['box'][1::2])/4]
                    if not isPoiWithinPoly(point, fbox):
                        remove_overlaps.append(item)
                        ahead_box = item['box']
                        fbox = [
                            [ahead_box[0], ahead_box[1]],
                            [ahead_box[2], ahead_box[3]],
                            [ahead_box[4], ahead_box[5]],
                            [ahead_box[6], ahead_box[7]]
                        ]
                box_levels[key] = remove_overlaps
        return box_levels

    def license_type(self):
        self.res['执照名称'] = ''
        for key in self.box_levels:
            sln_items = []
            for item in self.box_levels[key]:
                xsearch = re.search("(执照$)", item['text'])
                if xsearch is not None:
                    self.res['执照名称'] = item['text']
                    sln_items.append(item)
                    break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def license_copy(self):
        self.res['正副本'] = ''
        for key in self.box_levels:
            sln_items = []
            for item in self.box_levels[key]:
                xsearch = re.search("([\(（]*副本[\)）]*)|(^副本$)", item['text'])
                if xsearch is not None:
                    self.res['正副本'] = xsearch.group(1)
                    sln_items.append(item)
                    break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def business_id(self):
        self.res['统一社会信用代码'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("(信用代码|注册号)", item['text'])
                if xsearch is not None:
                    code_search = re.search("(信用代码|注册号)[：\:\.]?([A-Za-z0-9]+)", item['text'])
                    if code_search is not None:
                        self.res['统一社会信用代码'] = code_search.group(2)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind+1]
                        code_search = re.search("^[：\:\.]?([A-Za-z0-9]+)", next_item['text'])
                        if code_search is not None:
                            self.res['统一社会信用代码'] = code_search.group(1)
                            sln_items.append(item)
                            sln_items.append(next_item)
                            break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def business_name(self):
        self.res['名称'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(企业|公司|字号)?(名称|称)", item['text'])
                if xsearch is not None:
                    name_search = re.search("^(企业|公司|字号)?(名称|称)(.+)", item['text'])
                    if name_search is not None:
                        self.res['名称'] = name_search.group(3)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        self.res['名称'] = next_item['text']
                        sln_items.append(item)
                        sln_items.append(next_item)
                        break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def business_type(self):
        self.res['类型'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(企业|公司|主体)?(类?型|性质|组成形式|经济性质)", item['text'])
                if xsearch is not None:
                    type_search = re.search("^(企业|公司|主体)?(类?型|性质|组成形式|经济性质)(.*[\u4E00-\u9FA5A-Za-z]+.*)", item['text'])
                    if type_search is not None:
                        self.res['类型'] = type_search.group(3)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        self.res['类型'] = next_item['text']
                        sln_items.append(item)
                        sln_items.append(next_item)
                        break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def address(self):
        self.res['住所'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(企业|公司)?(住?所|地址|营业场所|经营场所|场所)", item['text'])
                if xsearch is not None:
                    addr_search = re.search("^(企业|公司)?(住?所|地址|营业场所|场所)(.*[\u4E00-\u9FA5A-Za-z]+.*)", item['text'])
                    if addr_search is not None:
                        self.res['住所'] = addr_search.group(3)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        if re.search('[\u4E00-\u9FA5A-Za-z]', next_item['text']) is not None:
                            self.res['住所'] = next_item['text']
                            sln_items.append(item)
                            sln_items.append(next_item)
                            break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                # 考虑到部分地址过长分两行打印，这里再检查下一行的第一个元素。
                if key+1 in self.box_levels:
                    if len(self.box_levels[key+1]) != 0:
                        item = self.box_levels[key+1][0]
                        xsearch = re.search("(栋|楼|路|幢|室|街|广场|大厦|工业园|镇|村|乡|坝|塘|区|大桥)", item['text'])
                        if xsearch is not None:
                            self.res['住所'] += item['text']
                            self.box_levels[key+1].remove(item)
                return

    def operator(self):
        self.res['法定代表人'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(法定?代表人|法定?代表人姓名|负责人|经营者)", item['text'])
                if xsearch is not None:
                    name_search = re.search("^(法定?代表人|法定?代表人姓名|负责人|经营者)(.*[\u4E00-\u9FA5A-Za-z]+.*)", item['text'])
                    if name_search is not None:
                        name = re.sub('([\(（]*(负责人|姓名)[\)）]*)', '', name_search.group(2))
                        if len(name) > 1:
                            self.res['法定代表人'] = name
                            sln_items.append(item)
                            break
                    if ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        if re.search('[\u4E00-\u9FA5A-Za-z]', next_item['text']) is not None:
                            self.res['法定代表人'] += next_item['text']
                            sln_items.append(item)
                            sln_items.append(next_item)
                            break

            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def registered_capital(self):
        self.res['注册资本'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(注册资本|注册资金)", item['text'])
                if xsearch is not None:
                    money_search = re.search("^(注册资本|注册资金)"
                                             "(.*[一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬亿元圆]+.*)", item['text'])
                    if money_search is not None:
                        self.res['注册资本'] = money_search.group(2)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        if re.search('[一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬亿元圆]',
                                     next_item['text']) is not None:
                            self.res['注册资本'] = next_item['text']
                            sln_items.append(item)
                            sln_items.append(next_item)
                            break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def register_date(self):
        self.res['成立日期'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(成立|注册)([日目]期)", item['text'])
                if xsearch is not None:
                    date_search = re.search("^(成立|注册)([日目]期)(.*[年月日目]+.*)", item['text'])
                    if date_search is not None:
                        self.res['成立日期'] = date_search.group(3)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        if re.search('[年月日目]', next_item['text']) is not None:
                            self.res['成立日期'] = next_item['text']
                            sln_items.append(item)
                            sln_items.append(next_item)
                            break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def business_term(self):
        self.res['营业期限'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("^(营业期限|经营期限)", item['text'])
                if xsearch is not None:
                    date_search = re.search("^(营业期限|经营期限)(.*[年月日]+.*|.*长期.*)", item['text'])
                    if date_search is not None:
                        self.res['营业期限'] = date_search.group(2)
                        sln_items.append(item)
                        break
                    elif ind < len(self.box_levels[key]) - 1:
                        next_item = self.box_levels[key][ind + 1]
                        if re.search('([年月日]|长期)', next_item['text']) is not None:
                            self.res['营业期限'] = next_item['text']
                            sln_items.append(item)
                            sln_items.append(next_item)
                            break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def scope(self):
        self.res['经营范围'] = ''
        addString = []
        address_y = 0
        diff_y = 0
        for key in self.box_levels:
            sln_items = []
            returnflag = False
            for ind, item in enumerate(self.box_levels[key]):
                if address_y == 0:
                    xsearch = re.search("^(经营范|业务范)", item['text'])
                    if xsearch is not None:
                        addString.append(re.sub('^(经营范围及方式|经营范围|经营范|业务范围|业务范)', '', item['text']))
                        address_y = item['box'][1]
                        diff_y = item['box'][3] - item['box'][1]
                        sln_items.append(item)
                        if ind != len(self.box_levels[key]) - 1:
                            next_item = self.box_levels[key][ind+1]
                            if next_item['box'][0] - item['box'][6] < diff_y * 5:
                                addString.append(next_item['text'])
                                sln_items.append(next_item)
                        break
                elif ind == 0:
                    if item['box'][1] - address_y < 2 * diff_y and re.search('(提示|登记机关)', item['text']) is None:
                        addString.append(item['text'])
                        sln_items.append(item)
                        address_y = item['box'][1]
                        break
                    else:
                        returnflag = True
                        break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
            if returnflag:
                break
        self.res['经营范围'] = ''.join(addString)

    def present_date(self):
        self.res['颁发日期'] = ''
        for key in self.box_levels:
            sln_items = []
            for ind, item in enumerate(self.box_levels[key]):
                xsearch = re.search("([年月]+.*日$|^[12一二].*年.*月)", item['text'])
                if xsearch is not None:
                    date_search = re.search("(.*[年月]+.*日$|^[12一二].*年.*月.*)", item['text'])
                    if date_search is not None and len(item['text']) < 13:
                        self.res['颁发日期'] = item['text']
                        sln_items.append(item)
                        break
            if len(sln_items) != 0:
                for item in sln_items:
                    self.box_levels[key].remove(item)
                return

    def fixup_missing(self):
        if self.res['统一社会信用代码'] == '':
            for key in self.box_levels:
                sln_items = []
                for ind, item in enumerate(self.box_levels[key]):
                    xsearch = re.search("^[A-Za-z0-9]{10,}$", item['text'])
                    if xsearch is not None:
                        self.res['统一社会信用代码'] = item['text']
                        sln_items.append(item)
                        break
                if len(sln_items) != 0:
                    for item in sln_items:
                        self.box_levels[key].remove(item)
                    break
        if self.res['名称'] == '':
            for key in self.box_levels:
                sln_items = []
                for ind, item in enumerate(self.box_levels[key]):
                    xsearch = re.search("(公司|企业|机构)$", item['text'])
                    if xsearch is not None and item['text'] != '有限责任公司':
                        self.res['名称'] = item['text']
                        sln_items.append(item)
                        break
                if len(sln_items) != 0:
                    for item in sln_items:
                        self.box_levels[key].remove(item)
                    break
        if self.res['住所'] == '':
            for key in self.box_levels:
                sln_items = []
                for ind, item in enumerate(self.box_levels[key]):
                    xsearch = re.search("(栋|楼|路|幢|室|街|广场|大厦|工业园|镇|村|乡|坝|塘|区|大桥)", item['text'])
                    if xsearch is not None and len(item['text']) > 8:
                        self.res['住所'] = item['text']
                        sln_items.append(item)
                        break
                if len(sln_items) != 0:
                    for item in sln_items:
                        self.box_levels[key].remove(item)
                    break
        if self.res['类型'] == '':
            for key in self.box_levels:
                sln_items = []
                for ind, item in enumerate(self.box_levels[key]):
                    xsearch = re.search("^(有限责任公司|股份有限公司)", item['text'])
                    if xsearch is not None:
                        self.res['类型'] = item['text']
                        sln_items.append(item)
                        break
                if len(sln_items) != 0:
                    for item in sln_items:
                        self.box_levels[key].remove(item)
                    break