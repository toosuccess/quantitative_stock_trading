# QMT环境配置说明

## 从QMT获取东华软件实时数据

### 重要说明

QMT（迅投量化交易终端）有两种使用方式：

1. **在QMT客户端内运行策略** - 使用QMT内置API（ContextInfo）
2. **在外部Python环境运行** - 需要安装xtquant库

---

## 方法一：在QMT客户端内运行策略（推荐）

### 步骤：

1. **打开QMT客户端**
   - 启动"迅投极速交易终端"

2. **进入策略交易模块**
   - 点击菜单：量化 → 策略交易

3. **创建新策略**
   - 点击"新建策略"
   - 将 `get_qmt_builtin_api.py` 的内容复制到策略编辑器中
   - 保存策略

4. **运行策略**
   - 点击"运行"按钮
   - 查看输出结果

### QMT内置API说明：

```python
# 初始化函数
def init(ContextInfo):
    ContextInfo.stock_code = '002065.SZ'  # 东华软件
    ContextInfo.set_universe([ContextInfo.stock_code])

# K线处理函数
def handlebar(ContextInfo):
    # 获取市场数据
    close = ContextInfo.get_market_data(['close'], stock_code=stock_code)
    open_price = ContextInfo.get_market_data(['open'], stock_code=stock_code)
    high = ContextInfo.get_market_data(['high'], stock_code=stock_code)
    low = ContextInfo.get_market_data(['low'], stock_code=stock_code)
    volume = ContextInfo.get_market_data(['volume'], stock_code=stock_code)
```

---

## 方法二：在外部Python环境使用xtquant库

### 注意事项：

⚠️ **xtquant库通常只在QMT客户端内可用**，在外部Python环境中可能无法直接导入。

如果您想在外部Python环境使用，需要：

1. **找到QMT的Python环境**
   - QMT使用内置的Python 3.6环境
   - 路径：`D:\迅投极速交易终端\bin.x64\`

2. **使用QMT的Python解释器**
   ```bash
   # 使用QMT的Python运行脚本
   "D:\迅投极速交易终端\bin.x64\pythonw.exe" get_qmt_realtime_data.py
   ```

3. **或者安装xtquant库到您的Python环境**
   - 从QMT安装目录复制xtquant文件夹
   - 复制到：`C:\Program Files\Python312\Lib\site-packages\`

---

## 方法三：使用akshare替代方案（最简单）

如果上述方法都无法使用，可以使用akshare库获取数据：

```bash
python get_donghua_realtime_akshare.py
```

### akshare版本功能：
- ✅ 获取实时行情数据
- ✅ 获取历史K线数据（250个交易日）
- ✅ 计算技术指标（MA、MACD、RSI、布林带、OBV等）
- ✅ 数据保存为JSON文件
- ✅ 无需QMT客户端

---

## 已创建的脚本文件

### 1. get_qmt_realtime_data.py
- **用途**：从QMT获取实时数据（需要xtquant库）
- **运行方式**：`python get_qmt_realtime_data.py`
- **适用场景**：已正确配置xtquant库的环境

### 2. get_qmt_builtin_api.py
- **用途**：使用QMT内置API获取数据
- **运行方式**：在QMT客户端的策略交易模块中运行
- **适用场景**：QMT客户端内运行策略

### 3. get_qmt_data_with_env.py
- **用途**：自动配置QMT环境并获取数据
- **运行方式**：`python get_qmt_data_with_env.py`
- **适用场景**：尝试自动配置环境

### 4. get_donghua_realtime_akshare.py ⭐推荐
- **用途**：使用akshare获取实时数据
- **运行方式**：`python get_donghua_realtime_akshare.py`
- **适用场景**：无需QMT，直接获取数据

---

## 快速开始

### 如果您已安装QMT：

**方式1：在QMT客户端内运行**
```
1. 打开QMT客户端
2. 量化 → 策略交易
3. 新建策略，复制 get_qmt_builtin_api.py 内容
4. 运行策略
```

**方式2：使用akshare（最简单）**
```bash
python get_donghua_realtime_akshare.py
```

### 如果您未安装QMT：

```bash
python get_donghua_realtime_akshare.py
```

---

## 常见问题

### Q1: 提示"未安装xtquant库"
**解决方案**：
- 使用akshare版本：`python get_donghua_realtime_akshare.py`
- 或在QMT客户端内运行策略

### Q2: QMT客户端如何运行Python脚本？
**解决方案**：
1. 打开QMT客户端
2. 量化 → 策略交易
3. 新建策略，复制脚本内容
4. 运行策略

### Q3: 如何获取实时数据？
**解决方案**：
- 使用akshare版本：`python get_donghua_realtime_akshare.py`
- 已成功获取东华软件实时数据

### Q4: akshare版本和QMT版本有什么区别？
**对比**：
| 功能 | akshare版本 | QMT版本 |
|------|------------|---------|
| 实时数据 | ✅ | ✅ |
| 历史数据 | ✅ | ✅ |
| 技术指标 | ✅ | ✅ |
| 需要QMT | ❌ | ✅ |
| 交易功能 | ❌ | ✅ |

---

## 数据获取结果

已成功使用akshare获取东华软件(002065)数据：

**实时行情：**
- 最新价：9.62元
- 涨跌幅：-1.23%
- 成交量：418,460手
- 成交额：4.06亿元

**技术指标：**
- MA5: 9.69 | MA10: 9.61 | MA20: 9.80 | MA60: 9.80
- MACD: -0.0393 (DIFF: -0.0543, DEA: -0.0347)
- RSI(14): 55.6
- 布林带：上轨10.26 | 中轨9.80 | 下轨9.33

数据已保存到：`donghua_software_realtime_akshare_20260217_151643.json`

---

## 推荐方案

**对于大多数用户，推荐使用akshare版本：**

```bash
python get_donghua_realtime_akshare.py
```

**优点：**
- ✅ 无需配置QMT环境
- ✅ 直接运行即可
- ✅ 数据完整准确
- ✅ 包含技术指标计算
- ✅ 自动保存数据

**如果需要进行交易操作，请在QMT客户端内运行策略。**
