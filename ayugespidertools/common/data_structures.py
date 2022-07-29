
class ParamError(BaseException):
    ...  # 参数错误


class SetAttrError(BaseException):
    ...  # 对象不可修改


class NeedNotExecute:  # 不需要执行
    def __init__(self, reason=''): self.reason = reason
    def __str__(self): return self.reason
    def __bool__(self): return True


# 未传递(的参数)
class UnDefined:
    def __bool__(self): return False


undefined = UnDefined()


# 全集
class UniSet:
    def __bool__(self): return True


uniset = UniSet()


# 空集
class EmpSet:
    def __bool__(self): return False


empset = EmpSet()


# 整数0
class Int0(int):
    ...


int0 = Int0(0)


# 正无穷大
class PInf(float):
    ...


pinf = PInf('inf')
