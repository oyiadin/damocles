1. **部署架构**

CoolQ Air，配合 [HTTP API](https://github.com/richardchien/coolq-http-api) 插件，将所需操作折射成对相应 HTTP 地址的请求、回复。本仓库代码为机器人主要逻辑，借由 [cqhttp 库](https://github.com/richardchien/python-cqhttp)间接与 CoolQ Air 进行通讯。

由于插件的设计，CoolQ Air 端与本仓库代码需要各自监听独立的端口并提供 HTTP 服务，注意设置好安全组策略，别将端口暴露给外网，同时设置好 `access_token` 跟 `secret`。

另外，由于我所使用的服务器环境为 Ubuntu，CoolQ Air 端运行在 Docker 中的 Wine 里边，镜像为[插件所提供](https://cqhttp.cc/docs/4.3/#/Docker)。平时借助 noVNC 操作 CoolQ Air。

2. **开发指南**

首先，提交 PR 请尽量遵循 PEP 8。

各文件作用：

* base.py: 对 cqhttp 框架的直接操作，封装好对消息的操作
* config.py: 配置账号相关信息
* fmtstr: printf 命令的 ELF 文件
* fmtstr.c: fmtstr 文件的源代码
* gal.py: gal 命令的主要逻辑
* globals.py: 各种全局常量（主要为各种提示消息）
* keywords.py: 关键词相关，数据+逻辑
* main.py: 各个子模块的逻辑就在这里
* sqli.py: bonus 命令的主要逻辑

3. **文档 _(不存在的)_**

就对 main.py 里需要怎么写简单说一下，这个文件里可以安排的事情：

1. 对所有群聊/私聊信息进行处理
2. 绑定特定命令

具体做法就是，定义一个你自己的函数，函数名随意，然后在上边加上一行修饰器。注意，函数**必须**包含一个位置参数：

```python
@bot.register(...参数...)
def your_func_name(cxt):
    pass
```

如果要对私聊信息/命令进行处理，请传递 `private=True`，群聊同理：`public=True`。可同时设置，但是至少需要一个（默认都是 False）。

如果要处理所有消息，直接传 `private` 和 `public` 就行；如果要处理特定命令，将命令名作为第一个参数传入。注意，在当前的代码逻辑下，前者优先于命令执行。

`register` 过的函数，在遇到符合的场景（如：私聊+命令）时，会依照其注册顺序执行。一旦有某个函数返回了非假的值，接下去的函数将不会被执行。同时，这个返回值会作为[`事件上报`](https://cqhttp.cc/docs/4.3/#/Post)的值回传给 HTTP API（因此，要求返回一个字典或者 None/False）。

如果想与 HTTP API 进行联络且不中断对该消息的进一步处理，请使用 `bot.send` 或 `bot.xxx`，其中，xxx 直接对应着[这里](https://cqhttp.cc/docs/4.3/#/API)的 API 路径名。
