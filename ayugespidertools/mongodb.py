'''
MongoDB ORM
基于 pymongo 开发
'''

from math import ceil, floor
from collections import deque
from copy import deepcopy
from decimal import Decimal
# from ._toolkit.data_structures import NeedNotExecute, SetAttrError, ParamError
# from ._toolkit.data_structures import undefined, int0, pinf, uniset, empset

from common.DataStructures import NeedNotExecute, SetAttrError, ParamError
from common.DataStructures import undefined, int0, pinf, uniset, empset


class ColumnsError(BaseException):
    ...


class SliceError(BaseException):
    ...


class _Factory:
    """ 不可变类型, 创建后不允许修改. """

    def __init__(self, where=uniset):
        if where is not empset:
            where = where or uniset
        object.__setattr__(self, 'where', where)

    def __setattr__(self, key, value):
        raise SetAttrError('_Factory是不可变对象')

    def __bool__(self):
        return True  # 下面有一个 where or _Factory(uniset)

    def __deepcopy(self, obj):
        if obj in (uniset, empset):
            return obj
        return deepcopy(obj)

    def __and__(self, obj):  # 交集
        a = self.__deepcopy(self.where)
        b = self.__deepcopy(obj.where)
        if a is uniset: return _Factory(b)
        if b is uniset: return _Factory(a)
        if a and b:  # a和b有可能是empset
            if set(a) & set(b):
                return _Factory({'$and': [a, b]})
            return _Factory({**a, **b})
        return _Factory(empset)

    def __or__(self, obj):  # 并集
        a = self.__deepcopy(self.where)
        b = self.__deepcopy(obj.where)
        if a is empset: return _Factory(b)
        if b is empset: return _Factory(a)
        if a is uniset or b is uniset:
            return _Factory(uniset)
        return _Factory({'$or': [a, b]})

    def __sub__(self, obj):
        return self & (~ obj)  # 差集

    def __invert__(self):  # 补集
        w = self.where
        if w is uniset: return _Factory(empset)
        if w is empset: return _Factory(uniset)
        return _Factory({'$nor': [w]})

    def where_sql(self):
        where = self.__deepcopy(self.where)
        if where is uniset: return {}
        if where is empset: return {'$and': [{'a': 1}, {'a': 2}]}
        print("sssss", where)
        return where


class _list_base():
    def __init__(self, *lis, **dic):
        self.lis = lis
        self.dic = dic


class contain_all(_list_base): ...


class contain_any(_list_base): ...


class contain_zero(_list_base): ...


class isin(_list_base): ...


class notin(_list_base): ...


class mo:  # 表示: mongodb_oper
    # 所有操作都允许脱离mo独立调用
    def re(s, i=False):
        if i:
            return {'$regex': s, '$options': 'i'}
        return {'$regex': s}

    contain_all = contain_all
    contain_any = contain_any
    contain_zero = contain_zero
    isin = isin
    notin = notin


class _Filter():

    def __init__(self, field):
        print("init:", field)
        object.__setattr__(self, 'field', field)

    def __setattr__(self, key, value):
        raise SetAttrError('_Filter是不可变对象')

    def __getattr__(self, name):
        print("getttt:", name)
        return _Filter(f"{self.field}.{name}")

    def __lt__(self, obj):
        return _Factory({self.field: {'$lt': obj}})  # <

    def __le__(self, obj):
        return _Factory({self.field: {'$lte': obj}})  # <=

    def __gt__(self, obj):
        print("gtttt")
        return _Factory({self.field: {'$gt': obj}})  # >

    def __ge__(self, obj):
        print("geeee", self.field, obj)
        return _Factory({self.field: {'$gte': obj}})  # >=

    def __ne__(self, obj):
        return _Factory({self.field: {'$ne': obj}})  # !=

    def __eq__(self, obj):
        typ = type(obj)
        if typ is contain_all:
            lis = obj.lis
            if len(lis) == 1: return _Factory({self.field: {'$elemMatch': {'$eq': lis[0]}}})
            if len(lis) > 1: return _Factory({'$and': [{self.field: {'$elemMatch': {'$eq': x}}} for x in set(lis)]})
            return _Factory(uniset)

        elif typ is contain_any:
            lis = obj.lis
            if len(lis) == 1: return _Factory({self.field: {'$elemMatch': {'$eq': lis[0]}}})
            if len(lis) > 1: return _Factory({'$or': [{self.field: {'$elemMatch': {'$eq': x}}} for x in set(lis)]})
            return _Factory(empset)

        elif typ is contain_zero:
            lis = obj.lis
            if lis: return _Factory({'$nor': [{self.field: {'$elemMatch': {'$eq': x}}} for x in set(lis)]})
            return _Factory(uniset)

        elif typ is isin:
            lis = obj.lis
            if not lis: return _Factory(empset)
            if len(lis) == 1: return _Factory({self.field: lis[0]})
            return _Factory({self.field: {'$in': lis}})

        elif typ is notin:
            lis = obj.lis
            if not lis: return _Factory(uniset)
            if len(lis) == 1: return _Factory({self.field: {'$ne': lis[0]}})
            return _Factory({self.field: {'$nin': lis}})

        return _Factory({self.field: obj})


class _MakeSlice():
    def __init__(self, func, **param):
        self.func = func
        self.param = param

    def __getitem__(self, key): return self.func(key, **self.param)


class _msheet():

    def __init__(self, mkconn, connpool, sheet, where=None, columns='*', _sort=None):
        if not columns: ParamError('columns 不能为空')
        setv = object.__setattr__
        setv(self, 'mkconn', mkconn)  # lambda : pymysql.connect(**address)
        setv(self, 'connpool', connpool)
        setv(self, 'sheet', sheet)
        setv(self, 'where', where or _Factory(uniset))
        setv(self, 'columns', columns)  # str型 或 tuple型
        setv(self, '_sort', deepcopy(_sort or {}))  # {A:True, B:False, ...}

    def __setattr__(self, key, value):
        raise SetAttrError('_msheet是不可变对象')

    def _deepcopy(self):
        ...

    def _copy(self, where=undefined, columns=undefined, _sort=undefined):
        return _msheet(
            mkconn=self.mkconn,
            connpool=self.connpool,  # 避免每个过滤器都与MySQL建立新的连接, 造成性能浪费
            sheet=self.sheet,
            where=self.where if where is undefined else where,
            columns=self.columns if columns is undefined else columns,
            _sort=self._sort if _sort is undefined else _sort
        )

    def get_conn(self):
        try:
            conn = self.connpool.popleft()  # 右进左出
        except:
            conn = self.mkconn()
        db, sheet = self.sheet
        return conn, conn[db][sheet]

    def _columns_sql(self):
        columns = self.columns
        if type(columns) is tuple:
            columns = dict.fromkeys(columns, 1)
            columns.setdefault('_id', 0)
        elif columns == '*':
            columns = None
        elif columns == '_id':
            columns = {columns: 1}
        else:
            columns = {columns: 1, '_id': 0}
        return columns

    def order(self, **rule):
        return self._copy(_sort={**self._sort, **rule})  # 必须self._sort在前

    def reset_order(self, **rule):
        return self._copy(_sort=rule)

    def _order_sql(self):
        if self._sort:
            return [(k, 1 if v else -1) for k, v in self._sort.items()]
        return []

    def __add__(self, data):
        conn, sheet = self.get_conn()
        if type(data) is dict:
            r = sheet.insert(data)  # 分配到的 _id 为 str(r)
        else:
            r = sheet.insert_many(data)  # r.acknowledged, r.inserted_ids
        self.connpool.append(conn)
        return r

    def delete(self, **param):
        return _MakeSlice(self._ExeDelete, **param)

    def _ExeDelete(self, key, **param):
        if key == 1:
            conn, sheet = self.get_conn()
            r = sheet.delete_one(self.where.where_sql())
            self.connpool.append(conn)
            return r  # r.acknowledged, r.deleted_count
        elif type(key) is slice and not key.start and not key.stop:
            conn, sheet = self.get_conn()
            r = sheet.delete_many(self.where.where_sql())
            self.connpool.append(conn)
            return r  # r.acknowledged, r.deleted_count
        else:
            raise SliceError('delete 方法暂时只支持 [1] 和 [:] 两种切片')

    def update(self, data, **param):
        return _MakeSlice(self._ExeUpdate, data=data, **param)

    def _ExeUpdate(self, key, data, add_null=False, force_data=False, **param):
        columns = self.columns
        typec = type(columns)
        if columns == '*':
            pass
        elif typec is tuple:
            data = {k: v for k, v in data.items() if k in columns}
        elif columns in data:
            data = {columns: data[columns]}
        else:
            data = {}
        if add_null:
            if columns == '*':
                raise ColumnsError('add_null=True 时必须指定字段')
            elif typec is tuple:
                data = {k: data.get(k) for k in columns}
            else:
                data = {columns: data.get(columns)}
        if data or force_data:
            if key == 1:
                conn, sheet = self.get_conn()
                r = sheet.update_one(self.where.where_sql(), {'$set': data})
                self.connpool.append(conn)
                return r  # r.acknowledged, r.matched_count
            elif type(key) is slice and not key.start and not key.stop:
                conn, sheet = self.get_conn()
                r = sheet.update_many(self.where.where_sql(), {'$set': data})
                self.connpool.append(conn)
                return r  # r.acknowledged, r.matched_count
                # matched_count 与 modified_count 的区别:
                # matched_count 表示匹配到的数目, 如果是update_one, 则 matched_count in [0, 1]
                # modified_count 表示数据有变化的数目
                # 如果一条数据修改前和修改后一致(例如:把3修改成3), 则不会统计到modified_count中
            else:
                raise SliceError('update 方法暂时只支持 [1] 和 [:] 两种切片')
        else:
            return NeedNotExecute('没有需要更新的字段')

    def _RStyleSlice(self, key):
        '''
        采用R语言的切片风格:
            索引从1开始, 1表示第1个元素, -1表示倒数第1个元素
            切片为双闭区间.
        在此ORM中:
            索引应该 >=1 或 <=-1
            若索引==0则视为1的左边1位
        '''
        total = None
        if type(key) is slice:
            type_data = list
            A = key.start or 1
            if A < 0:
                if total is None: total = self.len()
                A = total + A + 1
            A = ceil(max(1, A))
            B = key.stop
            if B is None or B == -1:
                size = pinf
            elif B == 0:
                size = int0
            else:
                if B < 0:
                    if total is None: total = self.len()
                    B = total + B + 1
                size = max(0, floor(B) - A + 1) or int0
            A -= 1  # 传递给数据库
        else:
            type_data = dict
            size = 1  # 取值的size是1, 勿改成0
            A = int(key)
            if A < 0:
                if total is None: total = self.len()
                A = total + A + 1
            A -= 1  # 传递给数据库
            if A < 0: A = pinf
        return A, size, type_data

    def len(self):
        conn, sheet = self.get_conn()
        tatal = sheet.count(self.where.where_sql())
        self.connpool.append(conn)
        return tatal

    __len__ = len

    def __getitem__(self, key):
        type_ = type(key)
        # 查询
        if type_ in (slice, int, float, Decimal):
            A, size, type_data = self._RStyleSlice(key)
            if A is pinf: return [][0]
            if not size: return []
            conn, sheet = self.get_conn()
            sh = sheet.find(self.where.where_sql(), self._columns_sql())
            sort = self._order_sql()
            if sort: sh = sh.sort(sort)
            if A: sh = sh.skip(A)
            if size is not pinf: sh = sh.limit(size)
            lines = list(sh)
            self.connpool.append(conn)
            if type_data is list:
                return lines
            return lines[0]
        # 限定columns
        elif type_ in (str, tuple):  # 输入多个字符串, 用逗号隔开, Python会自动打包成tuple
            return self._copy(columns=key)
        # _Factory
        elif type_ is _Factory:
            return self._copy(where=self.where & key)

    # 对某一个 array column添加元素
    # 当某条数据的该column已存在相同元素时, 该column不再添加(若要添加, 可尝试用$push替换$addToSet).
    # def add_for_array(self, column, o):
    #     where = deepcopy(self.where)
    #     r = self.sheet.update_many(where, {'$addToSet': {column: o}})
    #     return r.acknowledged, r.matched_count


class mongo():

    def __init__(self, mkconn, maxsize=None):
        self.maxsize = maxsize
        self.mkconn = mkconn
        self.connpool = deque([mkconn()], maxlen=maxsize)

    def __getitem__(self, sheet):
        return _msheet(
            mkconn=self.mkconn,
            connpool=self.connpool,
            sheet=sheet
        )

    def mksheet(self, db, sheet):
        return _msheet(
            mkconn=self.mkconn,
            connpool=deque([self.mkconn()], maxlen=self.maxsize),
            sheet=(db, sheet)
        )


class _MongoDBColumn():
    def __getattr__(self, field): return _Filter(field=field)


mc = _MongoDBColumn()

re = mo.re
# mo的所有操作都允许脱离mo独立调用
# 为防止"re操作"被"第三方库re"覆盖, 故本行代码放到最后


if __name__ == '__main__':
    from pymongo import MongoClient


    def mkconn():
        # return MongoClient("mongodb://localhost:27017/")
        return MongoClient("mongodb://admin:nimda@175.178.210.193:27017")


    conn = mongo(mkconn=mkconn)  # 创建mongo连接
    sheet = conn['test', 'test_sheet']  # 创建表对象

    line1 = {'姓名': '小一', '年龄': 11, '幸运数字': [1, 2, 3, 4], '成绩': {'语文': 81, '数学': 82, '英语': 83}}
    line2 = {'姓名': '小二', '年龄': 12, '幸运数字': [2, 3, 4, 5], '成绩': {'语文': 82, '数学': 83, '英语': 84}}
    line3 = {'姓名': '小三', '年龄': 13, '幸运数字': [3, 4, 5, 6], '成绩': {'语文': 83, '数学': 84, '英语': 85}}
    line4 = {'姓名': '小四', '年龄': 14, '幸运数字': [4, 5, 6, 7], '成绩': {'语文': 84, '数学': 85, '英语': 86}}
    line5 = {'姓名': '小五', '年龄': 15, '幸运数字': [5, 6, 7, 8], '成绩': {'语文': 85, '数学': 86, '英语': 87}}
    line6 = {'姓名': '小六', '年龄': 16, '幸运数字': [6, 7, 8, 9], '成绩': {'语文': 86, '数学': 87, '英语': 88}}

    # res = sheet + line1  # 单条添加
    # print(res, type(res))

    # res = sheet + [line2, line3, line4, line5, line6]  # 批量添加
    # print(res, type(res), res.inserted_ids)

    print(sheet[:])

    # res = sheet[mc.年龄 >= 16][mc.成绩.语文 >= 86][:]
    res = sheet[mc.年龄 >= 16][mc.成绩.语文 >= 86][mc.幸运数字 == [6, 7, 8, 9]][:]
    print("11", res)
