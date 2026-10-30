# 前处理器

`original/mult5zsic.pl` 是原分发源码，`original/pddl2pl.pl` 是参考实例。来源和哈希见根目录的 [第三方说明](../THIRD_PARTY_NOTICES.md)。

```text
python preprocessor/run_preprocessor.py preprocessor/original/pddl2pl.pl -o runs/pre-01
python preprocessor/run_preprocessor.py preprocessor/original/pddl2pl.pl -o runs/pre-repaired-01 --mode repaired
```

默认faithful保留原算法和缺陷；repaired显式应用16个补丁标签，每次记录于 `run.json`。实际运行是SWI兼容执行，不是原SICStus等价证明。运行器需要新的空输出目录，并为每次执行使用独立进程。

首次运行自动解压配套离线包。选项、已知错误、完整管线与独立AL输出说明见 [运行指南](../docs/usage.md) 和 [恢复状态](../docs/status.md)。
