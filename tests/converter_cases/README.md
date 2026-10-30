# 原转换器golden

每个子目录保留原版探针的 `input.pddl`，接受且有输出的样本另有 `output.pl`。157项结果的接受/拒绝、stdout、stderr和哈希统一保存在 `../../evidence/converter_oracle.json`，不再重复附每例JSON。

运行根目录下的 `python tests/verify_converter.py` 或转换器单元测试进行比较。不需要原转换器二进制；不会重新生成原版golden。

语法接受或输出字节一致不代表标准PDDL语义正确。扩大探针已发现尚未修复的输出差异，见 `../../docs/status.md`。
