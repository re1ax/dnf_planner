# DNF Planner

DNF conformant planner 的可运行功能重建，提供 C++17 规划器、PDDL→Prolog 转换器，以及原 Prolog 前处理源码的 SWI 兼容执行层。

```text
PDDL → Python转换器 → Prolog前处理 → AL理论 → C++规划器 → 计划/无计划/达到限制
```

这是从逆向工作工程中整理出的源码发布目录。运行时不依赖作者原二进制或原逆向工作目录。**当前实现尚未与作者版本完全等价，也不是完整标准 PDDL 编译器。** 已知差异见 [恢复状态](docs/status.md)，组件来源见 [来源与第三方说明](THIRD_PARTY_NOTICES.md)。

## 环境

| 内容 | 要求 |
|---|---|
| 规划器编译 | 支持 C++17 的编译器；可选 Make / CMake 3.12+ |
| PDDL转换器 | Python 3.10+，仅使用标准库，无需 `pip install` |
| Linux完整管线 | x86-64 Ubuntu兼容环境、Python 3.10+、`dpkg-deb` |
| Windows完整管线 | Python 3.10+、本地C++17编译器，以及已初始化的默认WSL Ubuntu x86-64发行版 |

离线 SWI-Prolog 包随仓库保留，首次使用自动校验并解包到 `runtime/linux-x64/root/`，不需要网络、sudo或全局安装Prolog。仍需满足包的系统库依赖，见 [运行时元数据](runtime/linux-x64/package.json)。

本源码发布版不包含预编译的 `dnf` / `dnf.exe`，请先完成下面的编译步骤。

## 快速开始

在仓库根目录执行。Windows默认WSL发行版必须可运行 `dpkg-deb`；可用 `wsl --list --verbose` 查看带星号的默认项。

### Windows PowerShell

需要本机已有 `g++`（例如现有的MinGW-w64工具链）：

```powershell
g++ -O2 -std=c++17 src/main.cpp src/reader.cpp src/state.cpp src/planner.cpp -o dnf.exe
python run_pipeline.py original_support/dp.pddl -o runs/blocks-faithful
```

### Linux / WSL

```bash
make
python3 run_pipeline.py original_support/dp.pddl -o runs/blocks-faithful
```

自带Blocks输入同时包含domain和problem。该样例应找到7步计划，输出包含 `Found a plan` 和 `Length: 7`。

**输出目录必须不存在或为空。** 再次运行请换目录，例如 `runs/blocks-faithful-02`。

### 使用自己的输入

```text
python run_pipeline.py domain.pddl problem.pddl -o runs/my-problem --mode repaired --timeout 120
```

若domain和problem在同一文件，只传一个输入。文件使用UTF-8无BOM、LF换行。Linux可将命令中的 `python` 换成 `python3`。

| 模式 | 含义 |
|---|---|
| `faithful`（默认） | 原前处理算法加SWI兼容层，保留原缺陷；不代表原SICStus运行已验证等价 |
| `repaired` | 应用16个有记录的前处理补丁标签；不保证修复全部转换器或优化问题 |

更多参数、分阶段运行、计划验证和故障排查见 [运行指南](docs/usage.md)。

## 编译选项

也可使用CMake：

```text
cmake -S . -B build
cmake --build build --config Release
```

CMake产物不一定在仓库根目录。运行管线时通过 `--planner` 指定实际产物，例如Windows多配置构建：

```powershell
python run_pipeline.py original_support/dp.pddl -o runs/cmake-demo --planner build/Release/dnf.exe
```

Linux通常为 `--planner build/dnf`；Windows单配置生成器通常为 `build/dnf.exe`，以实际产物为准。

## 查看结果

- `theory_0.plan.txt`：规划器完整输出，含动作、长度和统计；不是可直接输入 `--plan` 的动作文件。
- `pipeline.json`：模式、前处理日志、规划器返回码和输出。
- `preprocessed/`：Prolog组合源、原始AL、去注释后的AL及前处理日志。
- `standalone/`：真正交给规划器的独立AL理论。

`Found a plan` 表示找到计划；`No plan was found.` 表示当前搜索耗尽；`Search limit reached` 表示达到限制，存在性未知。**退出码0或 `status: completed` 均不能单独证明有解。**

## 测试

完整前处理测试需要上文的Linux/WSL运行环境；转换器测试本身不需要WSL：

```text
python -m unittest discover -s tests -p "test_*.py" -v
python tests/verify_converter.py
```

保留157项原版转换器golden，以及前处理微例。测试只约束覆盖内行为，不能作为全部输入等价证明。测试临时结果在忽略目录生成。

本次源码发布整理的实测结果见 [发布验证](docs/validation.md)。

## 目录

```text
src/                    C++17规划器
converter/              Python转换器、必需的原词法/语法表
preprocessor/           兼容层、运行器、原Prolog源码和参考实例
runtime/linux-x64/      离线SWI包、元数据、第三方版权
original_support/       Blocks PDDL样例
examples/               目标拆分演示输入
tests/                  测试代码、golden及前处理fixtures
evidence/               测试必需的原转换器golden索引
docs/                   运行方法与恢复状态
run_pipeline.py         完整管线入口
```

运行产物、解压后的运行时、编译产物和逆向临时工作区不进入源码发布包。原源码与第三方组件的身份、哈希和许可边界见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
