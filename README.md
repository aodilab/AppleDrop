# AppleDrop ｜ Windows 局域网无损直传 iPhone 相册工具

<p align="left">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-34c759.svg" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-007aff.svg" alt="Python"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20%E2%86%92%20iPhone-1d1d1f.svg" alt="Platform">
</p>

将 Windows 电脑上的视频、照片通过同一 Wi-Fi 局域网直接传进 iPhone 系统相册，不经过外网、不压缩画质、不在电脑硬盘复制临时文件。

---

## 一、 解决什么问题？

Windows 电脑传视频和照片到 iPhone 常见的三种方式各有局限：

| 传统方式 | 存在问题 | AppleDrop 处理方式 |
| :--- | :--- | :--- |
| **微信文件传输助手** | 视频被二次压缩、大体积文件受限，手机端需逐个点开手动保存 | **100% 原始文件直传**，支持 4K/60fps `.mp4` / `.mov` 大视频 |
| **网盘 / iCloud** | 需先上传云端服务器再从手机下载，耗时取决于外网宽带上传速度 | **纯局域网内网直连**，不走外网流量，直接跑满本地路由器 Wi-Fi 速度 |
| **数据线 / 第三方助手** | 需插拔线材或在电脑、手机两端安装常驻后台驱动插件 | **电脑单脚本即开即用 + 手机原生快捷指令/Safari**，手机端无需安装第三方 App |

### 底层传输机制（零拷贝）
把文件拖入 AppleDrop 窗口时，程序**不会**在电脑内存中缓存或复制临时文件，仅记录文件的磁盘绝对路径。当 iPhone 发起请求时，服务端直接从原磁盘路径按 `512 KB` 分块流式读取（支持 `HTTP 206 Partial Content` 断点与分片流），占用内存极低，几十 GB 的原片也能秒级响应。

---

## 二、 界面预览

| 空状态（拖入或选择文件） | 待发送队列（实时进度与状态） | 手机连接弹窗（扫码与接口地址） |
| :---: | :---: | :---: |
| <img src="assets/preview_empty.png" width="260" alt="空状态"> | <img src="assets/preview_queue.png" width="260" alt="传输队列"> | <img src="assets/preview_modal.png" width="260" alt="手机连接"> |

---

## 三、 电脑端安装与启动

### 1. 环境准备
- 系统：Windows 10 / 11
- 环境：Python 3.10 及以上
- 网络：电脑与 iPhone 连接在**同一个 Wi-Fi 局域网**下（电脑插网线、手机连同一台路由器的 Wi-Fi 亦可）。

### 2. 安装依赖并创建桌面图标
```powershell
# 1. 克隆仓库
git clone https://github.com/aodilab/AppleDrop.git
cd AppleDrop

# 2. 安装依赖
pip install -r requirements.txt

# 3. 在 Windows 桌面自动生成 AppleDrop 快捷方式图标
python build.py --shortcut

# 4. 启动程序
python build.py
```

生成桌面快捷方式后，日常使用有两种投递方式：
1. **窗口内投递**：双击桌面 `AppleDrop` 图标打开窗口，将视频或照片拖入窗口。
2. **桌面图标直接投递**：直接把电脑上的视频或照片**拖拽到桌面的 `AppleDrop` 快捷方式图标上**，程序会自动启动（或唤醒已有窗口）并将文件加入待发送队列。

---

## 四、 iPhone 端接收方法（两种方式任选）

### 方式一：iOS「快捷指令」一键直存系统相册（推荐，配置一次长期使用）

利用 iOS 系统自带的「快捷指令（Shortcuts）」，只需配置 2 个动作，后续在手机桌面点一下图标即可把电脑队列中的视频/照片直接存入系统相册：

1. 点击电脑端窗口右上角 **「手机连接」**，点击 **「复制网址」** 获取本机接口地址（形如 `http://192.168.1.2:8899/api/latest`）。
2. 打开 iPhone 自带的 **「快捷指令」** App，点击右上角 **`+`** 新建指令：
   - **第 1 步**：搜索并添加动作 **「获取 URL 的内容」**（Get Contents of URL），将地址替换为刚才复制的 `http://<你的电脑局域网IP>:8899/api/latest`。
   - **第 2 步**：搜索并添加动作 **「存储到相簿」**（Save to Photo Album），保持默认参数「将 `URL 的内容` 存储到 `最近项目`」。
3. 点击顶部指令名称可重命名（如「收电脑原片」），点击下方分享按钮选择 **「添加到主屏幕」**。

> **日常使用流程**：电脑上把视频拖进 AppleDrop $\rightarrow$ 手机桌面点一下该快捷指令图标 $\rightarrow$ 视频直接无损存入 iPhone 相册。  
> *(注：首次运行快捷指令时，iOS 顶部会弹出「允许连接局域网设备」和「允许访问照片」权限提示，点击「始终允许」即可。)*

---

### 方式二：iPhone 相机扫码网页端下载（免配置）

如果不配置快捷指令，也可以直接通过手机浏览器下载：
1. 点击电脑端右上角 **「手机连接」** 打开二维码弹窗；
2. 打开 iPhone 原生相机对准二维码扫描，点击顶部黄条在 **Safari** 中打开；
3. 网页会列出当前电脑端所有待发送文件：
   - 单个文件：点击右侧 **「原画保存 ›」**；
   - 多个文件：点击底部 **「打包下载全部」**。

---

## 五、 目录结构与命令说明

```text
├── build.py                   # 统一启动与构建入口
├── requirements.txt           # Python 依赖声明 (Pillow / qrcode / tkinterdnd2 / pywin32)
├── config/
│   └── settings.py            # 端口、窗口尺寸、分块大小与色彩配置
├── src/
│   ├── core/
│   │   ├── queue_manager.py   # 线程安全零拷贝文件队列与单实例 IPC 唤醒
│   │   └── http_server.py     # 多线程 HTTP Range 206 流服务与 /api/latest 接口
│   └── ui/
│       ├── components.py      # 2x 超采样抗锯齿绘图原语与矢量图标
│       ├── renderer.py        # 主视图与毛玻璃连接弹窗渲染器
│       └── desktop_app.py     # TkinterDnD 窗口控制与主线程状态轮询
├── templates/
│   └── mobile_portal.html     # iPhone Safari 移动端接收页模板
├── scripts/
│   ├── icon_builder.py        # 图标生成与 Windows 桌面快捷方式构建
│   └── visual_audit.py        # 三态界面快照生成与代码行数校验
└── assets/                    # 应用图标与界面预览图
```

| 命令 | 作用 |
| :--- | :--- |
| `python build.py` | 启动 AppleDrop 桌面端窗口 |
| `python build.py <文件路径...>` | 启动或唤醒现有窗口，并将指定文件加入发送队列 |
| `python build.py --shortcut` | 在 Windows 桌面创建 `AppleDrop.lnk` 快捷方式 |
| `python build.py --icon` | 重新生成 `assets/` 下的多分辨率图标 |
| `python build.py --audit` | 生成三态界面快照并校验工程模块代码行数 |
| `python build.py --all` | 依次执行图标生成、快捷方式创建与自审校验 |

---

## 六、 常见问题排查

1. **手机扫码打不开网页，或点击快捷指令提示连接超时？**
   - 请确认电脑和 iPhone 连接在同一个局域网下；
   - 检查电脑的 Windows 防火墙网络类型：如果当前 Wi-Fi 在 Windows 中被设为「公用网络（Public Network）」，防火墙可能拦截局域网 `8899` 端口访问。可在 Windows 设置中将该 Wi-Fi 改为「专用网络（Private Network）」，或在防火墙入站规则中放行 Python / `8899` 端口。
2. **电脑 IP 地址变化或端口被占用？**
   - 若路由器分配给电脑的局域网 IP 发生变动（窗口顶部标题栏会实时显示当前 IP），只需在手机快捷指令中将 IP 修正为新地址；
   - 若默认的 `8899` 端口被其他软件占用，AppleDrop 会自动顺延端口并在顶部标题栏直接显式提示（如 `· 192.168.1.2:8900`），点击「手机连接」复制的网址也会自动同步对应端口。
