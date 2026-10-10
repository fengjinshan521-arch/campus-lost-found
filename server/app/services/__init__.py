"""业务逻辑层（Service）：按模块拆分，由蓝图调用。

约定：Service 只依赖 Repository / Model，不直接读取 request，便于单测直接调用。
本文件保持轻量导入，避免与 Model 层循环依赖。
"""
