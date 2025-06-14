# AstrBot JavBus 搜索插件

一个基于JavBus API的AstrBot插件，提供影片、演员和磁力链接搜索功能。

## 功能

- 通过关键词搜索影片（番号）
- 搜索演员信息
- 获取影片磁力链接
- 支持合并转发消息

## 安装

1. 将插件文件夹放入AstrBot的`data/plugins`目录
2. 确保已安装Python依赖：
   ```
   pip install requests
   ```
3. 在AstrBot配置中添加JavBus API URL

## 配置

在`_conf_schema.json`中配置以下参数：

- `javbus_api_url`: JavBus API地址
- `forward_url`: QQ合并消息转发服务地址
- `javbus_image_proxy`: JavBus  图片代理地址

## 使用

### 命令格式

- 搜关键词[关键词] - 搜索影片
- 搜演员[演员名] - 搜索演员信息
- 搜磁力[番号] - 获取影片磁力链接

## 开发

```
@register("JavBus Serach", "cloudcranesss", "一个基于JavBus API的搜索服务", "v1.0.0", "https://github.com/cloudcranesss/astrbot_plugin_javbus_search")
```

## 许可证

MIT License