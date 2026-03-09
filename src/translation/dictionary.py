import re
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ── 英→中 (~800 条) ──────────────────────────────────────────────────────────
EN_ZH: dict = {

    # ── 问候 / 礼貌 ──────────────────────────────────────────────────────────
    'hello': '你好', 'hi': '嗨', 'hey': '嘿', 'bye': '再见',
    'goodbye': '再见', 'welcome': '欢迎', 'congratulations': '恭喜',

    # ── 基础代词 / 系动词（常出现于 UI 提示句）──────────────────────────────
    'i': '我', 'me': '我', 'my': '我的', 'we': '我们', 'our': '我们的',
    'you': '你', 'your': '你的', 'he': '他', 'she': '她', 'it': '它',
    'they': '他们', 'their': '他们的',
    'be': '是', 'this': '这', 'that': '那', 'here': '此处', 'there': '那里',
    'what': '什么', 'which': '哪个', 'where': '在哪', 'when': '何时',
    'how': '如何', 'why': '为何',
    'sure': '确定', 'wait': '等待', 'use': '使用', 'get': '获取',
    'set': '设置', 'go': '前往', 'try': '尝试', 'take': '获取',
    'want': '想要', 'need': '需要', 'like': '喜欢', 'make': '创建',
    'please': '请', 'thank': '谢谢', 'thanks': '谢谢',
    'sorry': '对不起', 'excuse': '打扰一下',

    # ── 肯定 / 否定 ──────────────────────────────────────────────────────────
    'yes': '是', 'no': '否', 'ok': '确定', 'okay': '好的',
    'true': '真', 'false': '假', 'on': '开', 'off': '关',
    'allow': '允许', 'deny': '拒绝', 'accept': '接受', 'reject': '拒绝',
    'agree': '同意', 'disagree': '不同意',

    # ── 时间 ─────────────────────────────────────────────────────────────────
    'time': '时间', 'date': '日期', 'datetime': '日期时间',
    'today': '今天', 'tomorrow': '明天', 'yesterday': '昨天',
    'morning': '早晨', 'afternoon': '下午', 'evening': '傍晚', 'night': '夜晚',
    'day': '天', 'week': '周', 'month': '月', 'year': '年',
    'hour': '小时', 'minute': '分钟', 'second': '秒', 'millisecond': '毫秒',
    'now': '现在', 'soon': '即将', 'later': '稍后', 'always': '始终',
    'never': '从不', 'often': '经常', 'sometimes': '有时',
    'daily': '每天', 'weekly': '每周', 'monthly': '每月', 'yearly': '每年',
    'expired': '已过期', 'expiry': '到期', 'timeout': '超时',
    'schedule': '计划', 'scheduled': '已计划', 'timestamp': '时间戳',
    'duration': '持续时间', 'interval': '间隔', 'delay': '延迟',

    # ── 人物 / 角色 ───────────────────────────────────────────────────────────
    'name': '名字', 'fullname': '全名', 'nickname': '昵称',
    'man': '男人', 'woman': '女人', 'boy': '男孩', 'girl': '女孩',
    'child': '孩子', 'children': '孩子们', 'people': '人们', 'person': '人',
    'user': '用户', 'users': '用户', 'admin': '管理员', 'administrator': '管理员',
    'author': '作者', 'owner': '所有者', 'member': '成员', 'guest': '访客',
    'operator': '操作员', 'developer': '开发者', 'designer': '设计师',
    'customer': '客户', 'client': '客户端', 'visitor': '访客',
    'moderator': '版主', 'supervisor': '主管', 'manager': '管理者',
    'team': '团队', 'staff': '员工', 'employee': '员工',
    'contact': '联系人', 'friend': '好友', 'follower': '关注者',

    # ── 生活 / 场所 ───────────────────────────────────────────────────────────
    'home': '主页/家', 'house': '房子', 'room': '房间', 'door': '门',
    'city': '城市', 'country': '国家/地区', 'world': '世界',
    'life': '生活', 'work': '工作', 'food': '食物', 'water': '水',
    'money': '钱', 'price': '价格', 'cost': '费用', 'fee': '费用',
    'tax': '税', 'discount': '折扣', 'total': '总计', 'subtotal': '小计',
    'balance': '余额', 'payment': '付款', 'invoice': '发票',
    'order': '订单', 'cart': '购物车', 'checkout': '结账',
    'shipping': '运送', 'delivery': '配送', 'address': '地址',

    # ── 软件 / UI 操作 ────────────────────────────────────────────────────────
    'open': '打开', 'close': '关闭', 'save': '保存', 'save as': '另存为',
    'delete': '删除', 'remove': '移除', 'copy': '复制', 'paste': '粘贴',
    'cut': '剪切', 'undo': '撤销', 'redo': '重做',
    'find': '查找', 'replace': '替换', 'select': '选择', 'select all': '全选',
    'new': '新建', 'create': '创建', 'add': '添加', 'append': '追加',
    'edit': '编辑', 'modify': '修改', 'update': '更新', 'rename': '重命名',
    'move': '移动', 'drag': '拖动', 'drop': '放置', 'resize': '调整大小',
    'view': '查看', 'preview': '预览', 'zoom': '缩放', 'zoom in': '放大',
    'zoom out': '缩小', 'fullscreen': '全屏', 'minimize': '最小化',
    'maximize': '最大化', 'restore': '恢复', 'collapse': '折叠',
    'expand': '展开', 'hide': '隐藏', 'show': '显示', 'toggle': '切换',
    'print': '打印', 'export': '导出', 'import': '导入', 'share': '分享',
    'send': '发送', 'receive': '接收', 'forward': '转发', 'reply': '回复',
    'upload': '上传', 'download': '下载', 'transfer': '传输',
    'install': '安装', 'uninstall': '卸载', 'upgrade': '升级',
    'update': '更新', 'patch': '补丁', 'rollback': '回滚',
    'restart': '重启', 'reboot': '重启', 'shutdown': '关机', 'sleep': '睡眠',
    'lock': '锁定', 'unlock': '解锁', 'login': '登录', 'logout': '退出登录',
    'sign in': '登录', 'sign out': '退出', 'sign up': '注册',
    'register': '注册', 'verify': '验证', 'authenticate': '认证',
    'authorize': '授权', 'grant': '授予', 'revoke': '撤销',
    'submit': '提交', 'cancel': '取消', 'confirm': '确认', 'apply': '应用',
    'reset': '重置', 'clear': '清除', 'clean': '清理',
    'back': '返回', 'next': '下一步', 'previous': '上一步', 'prev': '上一步',
    'finish': '完成', 'done': '完成', 'skip': '跳过', 'continue': '继续',
    'start': '开始', 'stop': '停止', 'pause': '暂停', 'resume': '恢复',
    'run': '运行', 'execute': '执行', 'launch': '启动', 'exit': '退出',
    'quit': '退出', 'abort': '中止', 'retry': '重试', 'refresh': '刷新',
    'reload': '重新加载', 'rebuild': '重新构建',
    'help': '帮助', 'about': '关于', 'feedback': '反馈',
    'report': '报告', 'diagnose': '诊断',
    # 软件常用词（精确含义，避免 SQLite 返回错误词义）
    'version': '版本', 'release': '发布', 'build': '构建', 'revision': '修订',
    'auto': '自动', 'force': '强制', 'quick': '快速',
    'check': '检查', 'scan': '扫描', 'detect': '检测',
    'sync': '同步', 'attach': '附加', 'detach': '分离',
    'mount': '挂载', 'bind': '绑定', 'unbind': '解绑',
    'trim': '修剪', 'crop': '裁切', 'rotate': '旋转',
    'flip': '翻转', 'scale': '缩放', 'transform': '变换',

    # ── 设置 / 配置 ───────────────────────────────────────────────────────────
    'settings': '设置', 'setting': '设置', 'option': '选项', 'options': '选项',
    'preferences': '偏好设置', 'configuration': '配置', 'config': '配置',
    'property': '属性', 'properties': '属性', 'parameter': '参数',
    'value': '值', 'default': '默认', 'custom': '自定义',
    'enable': '启用', 'disable': '禁用', 'enabled': '已启用',
    'disabled': '已禁用', 'activate': '激活', 'deactivate': '停用',
    'required': '必填', 'optional': '可选', 'advanced': '高级',
    'general': '通用', 'common': '通用', 'basic': '基础',
    'global': '全局', 'personal': '个人', 'profile': '配置文件',
    'account': '账户', 'subscription': '订阅', 'plan': '计划',
    'license': '许可证', 'trial': '试用', 'activate': '激活',

    # ── UI 组件 ──────────────────────────────────────────────────────────────
    'menu': '菜单', 'toolbar': '工具栏', 'sidebar': '侧边栏',
    'statusbar': '状态栏', 'titlebar': '标题栏', 'menubar': '菜单栏',
    'tab': '标签页', 'tabs': '标签页', 'panel': '面板', 'pane': '窗格',
    'dialog': '对话框', 'popup': '弹出框', 'modal': '模态框',
    'tooltip': '提示框', 'notification': '通知', 'alert': '警告',
    'toast': '提示', 'banner': '横幅', 'badge': '徽章',
    'button': '按钮', 'checkbox': '复选框', 'radio': '单选框',
    'dropdown': '下拉菜单', 'combobox': '组合框', 'listbox': '列表框',
    'slider': '滑块', 'scrollbar': '滚动条', 'progressbar': '进度条',
    'progress': '进度', 'spinner': '加载转圈', 'icon': '图标',
    'avatar': '头像', 'thumbnail': '缩略图', 'placeholder': '占位符',
    'label': '标签', 'title': '标题', 'subtitle': '副标题',
    'header': '页眉', 'footer': '页脚', 'body': '正文',
    'column': '列', 'row': '行', 'cell': '单元格', 'table': '表格',
    'grid': '网格', 'card': '卡片', 'widget': '小部件',
    'form': '表单', 'field': '字段', 'input': '输入', 'output': '输出',
    'textarea': '文本域', 'switch': '开关',

    # ── 文件 / 目录 ───────────────────────────────────────────────────────────
    'file': '文件', 'files': '文件', 'folder': '文件夹', 'directory': '目录',
    'path': '路径', 'drive': '驱动器', 'disk': '磁盘', 'volume': '卷',
    'extension': '扩展名', 'suffix': '后缀', 'prefix': '前缀',
    'filename': '文件名', 'basename': '基本名', 'archive': '归档',
    'zip': '压缩包', 'compress': '压缩', 'extract': '解压', 'unzip': '解压',
    'encrypt': '加密', 'decrypt': '解密', 'checksum': '校验和',
    'hash': '哈希', 'signature': '签名', 'certificate': '证书',
    'shortcut': '快捷方式', 'symlink': '符号链接', 'link': '链接',
    'recycle': '回收站', 'trash': '垃圾桶', 'temp': '临时', 'temporary': '临时',

    # ── 系统 / 进程 ───────────────────────────────────────────────────────────
    'system': '系统', 'os': '操作系统', 'kernel': '内核', 'driver': '驱动',
    'process': '进程', 'thread': '线程', 'task': '任务', 'job': '作业',
    'service': '服务', 'daemon': '后台进程', 'background': '后台',
    'foreground': '前台', 'priority': '优先级', 'queue': '队列',
    'stack': '堆栈', 'heap': '堆', 'buffer': '缓冲区',
    'memory': '内存', 'ram': '内存', 'cpu': '处理器', 'gpu': '显卡',
    'storage': '存储', 'swap': '交换', 'cache': '缓存',
    'registry': '注册表', 'environment': '环境', 'variable': '变量',
    'boot': '启动', 'bios': 'BIOS', 'firmware': '固件',
    'performance': '性能', 'benchmark': '基准测试', 'monitor': '监控',
    'resource': '资源', 'usage': '使用率', 'load': '负载',

    # ── 网络 ─────────────────────────────────────────────────────────────────
    'network': '网络', 'internet': '互联网', 'intranet': '局域网',
    'server': '服务器', 'host': '主机', 'hostname': '主机名',
    'ip': 'IP地址', 'port': '端口', 'protocol': '协议',
    'http': 'HTTP', 'https': 'HTTPS', 'ftp': 'FTP', 'ssh': 'SSH',
    'tcp': 'TCP', 'udp': 'UDP', 'dns': 'DNS', 'url': '网址',
    'domain': '域名', 'subdomain': '子域名', 'gateway': '网关',
    'router': '路由器', 'switch': '交换机', 'firewall': '防火墙',
    'proxy': '代理', 'vpn': 'VPN', 'tunnel': '隧道',
    'bandwidth': '带宽', 'latency': '延迟', 'ping': '延迟',
    'packet': '数据包', 'request': '请求', 'response': '响应',
    'api': 'API', 'endpoint': '端点', 'webhook': 'Webhook',
    'token': '令牌', 'session': '会话', 'cookie': 'Cookie',
    'connection': '连接', 'connected': '已连接', 'disconnected': '已断开',
    'online': '在线', 'offline': '离线', 'timeout': '超时',
    'retry': '重试', 'redirect': '重定向',

    # ── 数据库 / 数据 ─────────────────────────────────────────────────────────
    'database': '数据库', 'db': '数据库', 'table': '表', 'column': '列',
    'row': '行', 'record': '记录', 'field': '字段', 'index': '索引',
    'query': '查询', 'insert': '插入', 'update': '更新', 'delete': '删除',
    'select': '查询', 'join': '关联', 'transaction': '事务',
    'commit': '提交', 'rollback': '回滚', 'schema': '结构',
    'migration': '迁移', 'seed': '种子数据', 'backup': '备份',
    'restore': '恢复', 'sync': '同步', 'replicate': '复制',
    'data': '数据', 'dataset': '数据集', 'model': '模型',
    'entity': '实体', 'object': '对象', 'instance': '实例',
    'collection': '集合', 'array': '数组', 'list': '列表',
    'map': '映射', 'dict': '字典', 'set': '集合', 'tuple': '元组',
    'json': 'JSON', 'xml': 'XML', 'csv': 'CSV', 'yaml': 'YAML',
    'format': '格式', 'parse': '解析', 'serialize': '序列化',
    'encode': '编码', 'decode': '解码', 'convert': '转换',

    # ── 编程 / 开发 ───────────────────────────────────────────────────────────
    'code': '代码', 'script': '脚本', 'program': '程序', 'app': '应用',
    'application': '应用程序', 'software': '软件', 'framework': '框架',
    'library': '库', 'package': '包', 'module': '模块', 'plugin': '插件',
    'extension': '扩展', 'addon': '附加组件', 'component': '组件',
    'function': '函数', 'method': '方法', 'class': '类', 'interface': '接口',
    'variable': '变量', 'constant': '常量', 'parameter': '参数',
    'argument': '参数', 'return': '返回', 'callback': '回调',
    'event': '事件', 'handler': '处理器', 'listener': '监听器',
    'loop': '循环', 'condition': '条件', 'statement': '语句',
    'comment': '注释', 'debug': '调试', 'test': '测试', 'build': '构建',
    'compile': '编译', 'deploy': '部署', 'release': '发布',
    'commit': '提交', 'branch': '分支', 'merge': '合并', 'fork': '派生',
    'clone': '克隆', 'push': '推送', 'pull': '拉取', 'fetch': '获取',
    'repository': '仓库', 'repo': '仓库', 'tag': '标签',
    'diff': '差异', 'patch': '补丁', 'conflict': '冲突',
    'bug': '缺陷', 'fix': '修复', 'issue': '问题', 'ticket': '工单',
    'feature': '功能', 'enhancement': '改进', 'refactor': '重构',
    'optimize': '优化', 'performance': '性能', 'profiling': '性能分析',
    'log': '日志', 'logging': '日志记录', 'trace': '追踪',
    'breakpoint': '断点', 'exception': '异常', 'error': '错误',
    'warning': '警告', 'info': '信息', 'debug': '调试',
    'stdout': '标准输出', 'stderr': '标准错误', 'stdin': '标准输入',
    'terminal': '终端', 'console': '控制台', 'shell': '命令行',
    'command': '命令', 'argument': '参数', 'flag': '标志',
    'environment': '环境', 'container': '容器', 'image': '镜像',
    'docker': 'Docker', 'kubernetes': 'Kubernetes', 'pipeline': '管道',
    'workflow': '工作流', 'automation': '自动化', 'integration': '集成',

    # ── 状态 / 结果 ───────────────────────────────────────────────────────────
    'status': '状态', 'state': '状态', 'mode': '模式',
    'success': '成功', 'failed': '失败', 'failure': '失败',
    'error': '错误', 'warning': '警告', 'info': '提示',
    'loading': '加载中', 'processing': '处理中', 'waiting': '等待中',
    'pending': '待处理', 'running': '运行中', 'stopped': '已停止',
    'paused': '已暂停', 'finished': '已完成', 'canceled': '已取消',
    'queued': '排队中', 'scheduled': '已计划', 'skipped': '已跳过',
    'active': '激活', 'inactive': '未激活', 'idle': '空闲',
    'busy': '繁忙', 'ready': '就绪', 'available': '可用',
    'unavailable': '不可用', 'blocked': '已阻止', 'suspended': '已暂停',
    'deleted': '已删除', 'archived': '已归档', 'locked': '已锁定',
    'unlocked': '已解锁', 'hidden': '已隐藏', 'visible': '可见',
    'read': '已读', 'unread': '未读', 'new': '新',
    'open': '打开', 'closed': '已关闭', 'resolved': '已解决',
    'published': '已发布', 'draft': '草稿', 'private': '私有',
    'public': '公开', 'shared': '已共享', 'synced': '已同步',
    'syncing': '同步中', 'updated': '已更新', 'outdated': '已过期',
    'connected': '已连接', 'disconnected': '已断开',
    'enabled': '已启用', 'disabled': '已禁用',
    'valid': '有效', 'invalid': '无效', 'verified': '已验证',
    'unverified': '未验证', 'approved': '已批准', 'rejected': '已拒绝',
    'expired': '已过期', 'revoked': '已撤销',
    'installed': '已安装', 'uninstalled': '已卸载',
    'online': '在线', 'offline': '离线',

    # ── 安全 / 权限 ───────────────────────────────────────────────────────────
    'security': '安全', 'privacy': '隐私', 'permission': '权限',
    'access': '访问', 'role': '角色', 'policy': '策略',
    'password': '密码', 'passphrase': '口令', 'pin': 'PIN码',
    'username': '用户名', 'email': '电子邮件', 'phone': '电话',
    'two-factor': '两步验证', '2fa': '两步验证', 'otp': '一次性密码',
    'captcha': '验证码', 'token': '令牌', 'key': '密钥',
    'certificate': '证书', 'encryption': '加密', 'ssl': 'SSL',
    'tls': 'TLS', 'https': 'HTTPS', 'firewall': '防火墙',
    'antivirus': '杀毒软件', 'malware': '恶意软件',

    # ── 显示 / 媒体 ───────────────────────────────────────────────────────────
    'screen': '屏幕', 'display': '显示', 'monitor': '显示器',
    'resolution': '分辨率', 'brightness': '亮度', 'contrast': '对比度',
    'color': '颜色', 'theme': '主题', 'font': '字体', 'size': '大小',
    'style': '样式', 'bold': '粗体', 'italic': '斜体', 'underline': '下划线',
    'strikethrough': '删除线', 'align': '对齐', 'indent': '缩进',
    'spacing': '间距', 'margin': '边距', 'padding': '内边距',
    'border': '边框', 'shadow': '阴影', 'opacity': '透明度',
    'background': '背景', 'foreground': '前景', 'layer': '图层',
    'image': '图片', 'photo': '照片', 'icon': '图标', 'logo': '标志',
    'video': '视频', 'audio': '音频', 'music': '音乐', 'sound': '声音',
    'volume': '音量', 'mute': '静音', 'subtitle': '字幕',
    'caption': '字幕', 'screenshot': '截图',

    # ── 文档 / 内容 ───────────────────────────────────────────────────────────
    'text': '文本', 'document': '文档', 'page': '页面', 'pages': '页',
    'paragraph': '段落', 'sentence': '句子', 'word': '单词',
    'character': '字符', 'letter': '字母', 'number': '数字',
    'symbol': '符号', 'space': '空格', 'newline': '换行',
    'tab': '制表符', 'indent': '缩进', 'wrap': '换行',
    'header': '标题', 'footer': '页脚', 'title': '标题',
    'subtitle': '副标题', 'caption': '说明', 'description': '描述',
    'summary': '摘要', 'content': '内容', 'body': '正文',
    'article': '文章', 'post': '文章', 'comment': '评论', 'reply': '回复',
    'tag': '标签', 'category': '分类', 'topic': '话题',
    'keyword': '关键词', 'search': '搜索',

    # ── 数量 / 统计 ───────────────────────────────────────────────────────────
    'count': '数量', 'amount': '金额', 'quantity': '数量',
    'number': '数字', 'total': '总计', 'subtotal': '小计',
    'sum': '总和', 'average': '平均', 'avg': '平均',
    'max': '最大', 'maximum': '最大值', 'min': '最小', 'minimum': '最小值',
    'limit': '限制', 'quota': '配额', 'threshold': '阈值',
    'percent': '百分比', 'percentage': '百分比', 'ratio': '比率',
    'rate': '速率', 'speed': '速度', 'frequency': '频率',
    'all': '全部', 'none': '无', 'any': '任意', 'some': '部分',
    'each': '每个', 'every': '每个', 'both': '两者', 'other': '其他',
    'more': '更多', 'less': '更少', 'most': '最多', 'least': '最少',

    # ── 方向 / 位置 ───────────────────────────────────────────────────────────
    'top': '顶部', 'bottom': '底部', 'left': '左侧', 'right': '右侧',
    'center': '居中', 'middle': '中间', 'up': '向上', 'down': '向下',
    'front': '前面', 'back': '后面', 'inside': '内部', 'outside': '外部',
    'horizontal': '水平', 'vertical': '垂直', 'diagonal': '对角',
    'width': '宽度', 'height': '高度', 'depth': '深度', 'length': '长度',
    'position': '位置', 'location': '位置', 'region': '区域',
    'area': '区域', 'zone': '区域', 'section': '部分', 'part': '部分',

    # ── 形容词 ───────────────────────────────────────────────────────────────
    'big': '大的', 'small': '小的', 'large': '大的', 'tiny': '微小',
    'long': '长的', 'short': '短的', 'wide': '宽的', 'narrow': '窄的',
    'high': '高的', 'low': '低的', 'deep': '深的', 'shallow': '浅的',
    'fast': '快速', 'slow': '慢的', 'quick': '快速', 'instant': '即时',
    'hot': '热的', 'cold': '冷的', 'warm': '温暖', 'cool': '凉爽',
    'hard': '困难', 'easy': '简单', 'simple': '简单', 'complex': '复杂',
    'safe': '安全', 'dangerous': '危险', 'secure': '安全',
    'clean': '干净', 'dirty': '脏', 'clear': '清晰', 'blur': '模糊',
    'bright': '明亮', 'dark': '暗', 'light': '浅色', 'heavy': '重',
    'rich': '丰富', 'empty': '空', 'full': '满', 'complete': '完整',
    'incomplete': '不完整', 'partial': '部分',
    'correct': '正确', 'incorrect': '错误', 'wrong': '错误',
    'valid': '有效', 'invalid': '无效',
    'old': '旧的', 'modern': '现代', 'latest': '最新', 'legacy': '旧版',
    'stable': '稳定', 'unstable': '不稳定', 'beta': '测试版',
    'alpha': '内测版', 'preview': '预览版', 'release': '正式版',
    'free': '免费', 'paid': '付费', 'premium': '高级版',
    'local': '本地', 'remote': '远程', 'cloud': '云端',
    'online': '在线', 'offline': '离线', 'real-time': '实时',
    'manual': '手动', 'automatic': '自动', 'smart': '智能',
    'public': '公开', 'private': '私有', 'protected': '受保护',
    'visible': '可见', 'hidden': '隐藏', 'read-only': '只读',
    'required': '必须', 'optional': '可选',
    'active': '活跃', 'inactive': '未激活',

    # ── 通知 / 消息 ───────────────────────────────────────────────────────────
    'message': '消息', 'notification': '通知', 'alert': '提示',
    'reminder': '提醒', 'announcement': '公告', 'broadcast': '广播',
    'inbox': '收件箱', 'outbox': '发件箱', 'sent': '已发送',
    'draft': '草稿', 'spam': '垃圾邮件', 'trash': '垃圾桶',
    'read': '已读', 'unread': '未读', 'mark': '标记',

    # ── 其他常见缩写 ─────────────────────────────────────────────────────────
    'id': 'ID', 'uid': '用户ID', 'guid': '全局唯一ID',
    'ok': '确定', 'n/a': '不适用', 'na': '不适用', 'tbd': '待定',
    'todo': '待办', 'wip': '进行中', 'done': '完成',
    'faq': '常见问题', 'readme': '说明文档', 'changelog': '更新日志',
    'license': '许可证', 'terms': '条款', 'privacy': '隐私',
    'copyright': '版权', 'trademark': '商标',
    'kb': 'KB', 'mb': 'MB', 'gb': 'GB', 'tb': 'TB',
    'ms': '毫秒', 'sec': '秒', 'min': '分钟',
    'px': '像素', 'pt': '磅', 'em': 'em', 'rem': 'rem',
    'rgb': 'RGB', 'hex': '十六进制',
    'ltr': '从左到右', 'rtl': '从右到左',
    'utf-8': 'UTF-8', 'ascii': 'ASCII', 'unicode': 'Unicode',
}

# ── 中→英（从 EN_ZH 自动反向，再手动补充） ─────────────────────────────────
ZH_EN: dict = {}
for _en, _zh in EN_ZH.items():
    if _zh and '/' not in _zh and _zh not in ZH_EN:
        ZH_EN[_zh] = _en

ZH_EN.update({
    # 常见 UI 操作
    '确定': 'OK', '取消': 'Cancel', '关闭': 'Close', '退出': 'Exit',
    '保存': 'Save', '另存为': 'Save As', '打开': 'Open', '新建': 'New',
    '删除': 'Delete', '移除': 'Remove', '复制': 'Copy', '粘贴': 'Paste',
    '剪切': 'Cut', '撤销': 'Undo', '重做': 'Redo', '全选': 'Select All',
    '查找': 'Find', '替换': 'Replace', '刷新': 'Refresh',
    '编辑': 'Edit', '查看': 'View', '帮助': 'Help', '工具': 'Tools',
    '文件': 'File', '格式': 'Format', '插入': 'Insert',
    '设置': 'Settings', '选项': 'Options', '属性': 'Properties',
    '导入': 'Import', '导出': 'Export', '打印': 'Print', '分享': 'Share',
    '上传': 'Upload', '下载': 'Download', '安装': 'Install', '卸载': 'Uninstall',
    '更新': 'Update', '升级': 'Upgrade', '重启': 'Restart', '关机': 'Shutdown',
    '登录': 'Login', '退出登录': 'Logout', '注册': 'Register',
    '搜索': 'Search', '筛选': 'Filter', '排序': 'Sort',
    '提交': 'Submit', '确认': 'Confirm', '应用': 'Apply', '重置': 'Reset',
    '返回': 'Back', '下一步': 'Next', '上一步': 'Previous',
    '完成': 'Done', '跳过': 'Skip', '继续': 'Continue',
    '开始': 'Start', '停止': 'Stop', '暂停': 'Pause', '恢复': 'Resume',
    '运行': 'Run', '执行': 'Execute', '启动': 'Launch',
    '展开': 'Expand', '折叠': 'Collapse', '隐藏': 'Hide', '显示': 'Show',
    '切换': 'Toggle', '全屏': 'Fullscreen', '最小化': 'Minimize',
    '最大化': 'Maximize',
    # 状态
    '加载中': 'Loading', '处理中': 'Processing', '等待中': 'Waiting',
    '待处理': 'Pending', '运行中': 'Running', '已停止': 'Stopped',
    '已完成': 'Finished', '已取消': 'Canceled', '错误': 'Error',
    '警告': 'Warning', '成功': 'Success', '失败': 'Failed',
    '在线': 'Online', '离线': 'Offline', '已连接': 'Connected',
    '已断开': 'Disconnected', '已启用': 'Enabled', '已禁用': 'Disabled',
    '已锁定': 'Locked', '已删除': 'Deleted', '已归档': 'Archived',
    '草稿': 'Draft', '已发布': 'Published',
    # 常用名词
    '版本': 'Version', '语言': 'Language', '主题': 'Theme',
    '密码': 'Password', '用户名': 'Username', '电子邮件': 'Email',
    '通知': 'Notification', '消息': 'Message', '备份': 'Backup',
    '日志': 'Log', '进度': 'Progress', '配置': 'Configuration',
    '网络': 'Network', '服务器': 'Server', '数据库': 'Database',
    '缓存': 'Cache', '内存': 'Memory', '存储': 'Storage',
    '许可证': 'License', '版权': 'Copyright', '条款': 'Terms',
    '隐私': 'Privacy', '安全': 'Security', '权限': 'Permission',
})

# ── 正则 / 常量 ──────────────────────────────────────────────────────────────
_STRIP_RE   = re.compile(r'[^a-zA-Z0-9\u4e00-\u9fff\s\-]')
_ZH_LANGS   = {'zh-cn', 'zh', 'zh-tw', 'zh-hk', 'chinese'}
_CONSONANTS = set('bcdfghjklmnpqrstvwxyz')

# 冠词（短语翻译时跳过）
_ARTICLES  = frozenset({'a', 'an', 'the'})
# 否定词（含缩写形式；_normalize_en 会去掉撇号，如 don't → dont）
_NEGATIONS = frozenset({
    'not', 'never', 'neither', 'nor',
    'dont', 'cant', 'wont', 'isnt', 'arent', 'wasnt', 'werent',
    'havent', 'hasnt', 'hadnt', 'didnt', 'doesnt',
    'wouldnt', 'shouldnt', 'couldnt', 'mightnt', 'mustnt',
})

# ── 不规则词形表：变形 → 原形 ─────────────────────────────────────────────────
# 词典只存原形，所有变形通过此表或规则还原，无需重复存储
IRREGULAR: dict = {
    # ── 常用动词 ─────────────────────────────────────────────────────────────
    'ran': 'run',   'runs': 'run',   'running': 'run',
    'went': 'go',   'gone': 'go',    'goes': 'go',    'going': 'go',
    'was': 'be',    'were': 'be',    'been': 'be',    'being': 'be',
    'is': 'be',     'are': 'be',     'am': 'be',
    'had': 'have',  'has': 'have',   'having': 'have',
    'did': 'do',    'done': 'do',    'does': 'do',    'doing': 'do',
    'made': 'make', 'makes': 'make', 'making': 'make',
    'got': 'get',   'gotten': 'get', 'gets': 'get',   'getting': 'get',
    'came': 'come', 'comes': 'come', 'coming': 'come',
    'took': 'take', 'taken': 'take', 'takes': 'take', 'taking': 'take',
    'gave': 'give', 'given': 'give', 'gives': 'give', 'giving': 'give',
    'found': 'find','finds': 'find', 'finding': 'find',
    'said': 'say',  'says': 'say',   'saying': 'say',
    'saw':  'see',  'seen': 'see',   'sees': 'see',   'seeing': 'see',
    'knew': 'know', 'known': 'know', 'knows': 'know', 'knowing': 'know',
    'thought': 'think', 'thinks': 'think', 'thinking': 'think',
    'built': 'build',   'builds': 'build',  'building': 'build',
    'sent':  'send',    'sends': 'send',    'sending': 'send',
    'kept':  'keep',    'keeps': 'keep',    'keeping': 'keep',
    'left':  'leave',   'leaves': 'leave',  'leaving': 'leave',
    'held':  'hold',    'holds': 'hold',    'holding': 'hold',
    'brought': 'bring', 'brings': 'bring',  'bringing': 'bring',
    'bought': 'buy',    'buys': 'buy',      'buying': 'buy',
    'wrote': 'write',   'written': 'write', 'writes': 'write', 'writing': 'write',
    'lost':  'lose',    'loses': 'lose',    'losing': 'lose',
    'cut':   'cut',     'cuts': 'cut',      'cutting': 'cut',
    'put':   'put',     'puts': 'put',      'putting': 'put',
    'set':   'set',     'sets': 'set',      'setting': 'set',
    'read':  'read',    'reads': 'read',    'reading': 'read',
    'led':   'lead',    'leads': 'lead',    'leading': 'lead',
    'met':   'meet',    'meets': 'meet',    'meeting': 'meet',
    'chose': 'choose',  'chosen': 'choose', 'chooses': 'choose', 'choosing': 'choose',
    'began': 'begin',   'begun': 'begin',   'begins': 'begin',   'beginning': 'begin',
    'broke': 'break',   'broken': 'break',  'breaks': 'break',   'breaking': 'break',
    'threw': 'throw',   'thrown': 'throw',  'throws': 'throw',   'throwing': 'throw',
    'drew':  'draw',    'drawn': 'draw',    'draws': 'draw',     'drawing': 'draw',
    'flew':  'fly',     'flown': 'fly',     'flies': 'fly',      'flying': 'fly',
    'fell':  'fall',    'fallen': 'fall',   'falls': 'fall',     'falling': 'fall',
    'grew':  'grow',    'grown': 'grow',    'grows': 'grow',     'growing': 'grow',
    'wore':  'wear',    'worn': 'wear',     'wears': 'wear',     'wearing': 'wear',
    'spoke': 'speak',   'spoken': 'speak',  'speaks': 'speak',   'speaking': 'speak',
    'spent': 'spend',   'spends': 'spend',  'spending': 'spend',
    'stood': 'stand',   'stands': 'stand',  'standing': 'stand',
    'sold':  'sell',    'sells': 'sell',    'selling': 'sell',
    'told':  'tell',    'tells': 'tell',    'telling': 'tell',
    'paid':  'pay',     'pays': 'pay',      'paying': 'pay',
    'laid':  'lay',     'lays': 'lay',      'laying': 'lay',
    'sat':   'sit',     'sits': 'sit',      'sitting': 'sit',
    'hit':   'hit',     'hits': 'hit',      'hitting': 'hit',
    'let':   'let',     'lets': 'let',      'letting': 'let',
    'shut':  'shut',    'shuts': 'shut',    'shutting': 'shut',
    # ── 不规则名词复数 ──────────────────────────────────────────────────────
    'men': 'man', 'women': 'woman', 'children': 'child',
    'mice': 'mouse', 'geese': 'goose', 'feet': 'foot', 'teeth': 'tooth',
    'indices': 'index', 'matrices': 'matrix', 'vertices': 'vertex',
    'analyses': 'analysis', 'crises': 'crisis', 'theses': 'thesis',
    'phenomena': 'phenomenon', 'criteria': 'criterion',
    'data': 'datum',
    # ── 不规则形容词比较级 / 最高级 ────────────────────────────────────────
    'better': 'good', 'best': 'good',
    'worse': 'bad',   'worst': 'bad',
    'further': 'far', 'furthest': 'far',
    'farther': 'far', 'farthest': 'far',
    'elder':  'old',  'eldest': 'old',
}


def _normalize_en(text: str) -> str:
    return _STRIP_RE.sub('', text).lower().strip()


def _is_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def _lemmatize(word: str) -> list:
    """
    返回 word 的候选原形列表（按可信度从高到低）。
    策略：① 不规则表直查 → ② 分层规则剥离后缀。
    调用方按顺序在 EN_ZH 中查找，首次命中即返回。
    """
    # ① 不规则词直接命中
    if word in IRREGULAR:
        return [IRREGULAR[word]]

    n = len(word)
    cands: list = []

    # ② -ing（进行时 / 动名词 / 形容词）
    if word.endswith('ing') and n > 5:
        base = word[:-3]                         # loading → load
        cands.append(base)
        cands.append(base + 'e')                 # saving  → save
        # 双写辅音：running → runn → run
        if len(base) >= 2 and base[-1] == base[-2] and base[-1] in _CONSONANTS:
            cands.append(base[:-1])

    # ③ -ed（过去式 / 过去分词 / 形容词）
    if word.endswith('ed') and n > 4:
        base = word[:-2]                         # started → start
        cands.append(base)
        cands.append(base + 'e')                 # saved   → save
        if base.endswith('i'):
            cands.append(base[:-1] + 'y')        # denied  → deny, copied → copy
        if len(base) >= 2 and base[-1] == base[-2] and base[-1] in _CONSONANTS:
            cands.append(base[:-1])              # stopped → stop

    # ④ -er / -est（比较级 / 最高级）
    if word.endswith('iest') and n > 5:
        cands.append(word[:-4] + 'y')            # easiest → easy
    elif word.endswith('est') and n > 5:
        base = word[:-3]                         # fastest → fast
        cands.append(base)
        if len(base) >= 2 and base[-1] == base[-2] and base[-1] in _CONSONANTS:
            cands.append(base[:-1])              # biggest → big

    if word.endswith('ier') and n > 4:
        cands.append(word[:-3] + 'y')            # easier  → easy
    elif word.endswith('er') and n > 4:
        base = word[:-2]                         # faster  → fast
        cands.append(base)
        if len(base) >= 2 and base[-1] == base[-2] and base[-1] in _CONSONANTS:
            cands.append(base[:-1])              # bigger  → big

    # ⑤ -ies → -y（第三人称 / 复数）
    if word.endswith('ies') and n > 4:
        cands.append(word[:-3] + 'y')            # entries → entry

    # ⑥ -es / -s（复数 / 第三人称）
    if word.endswith('es') and n > 4:
        cands.append(word[:-2])                  # matches → match
        cands.append(word[:-1])
    elif word.endswith('s') and n > 3:
        cands.append(word[:-1])                  # errors  → error

    # ⑦ -ly → 形容词原形
    if word.endswith('ily') and n > 5:
        cands.append(word[:-3] + 'y')            # easily  → easy
    elif word.endswith('ly') and n > 4:
        cands.append(word[:-2])                  # quickly → quick

    # ⑧ -tion/-sion → 动词（粗略，命中率低，放最后）
    if word.endswith('ation') and n > 7:
        cands.append(word[:-5])                  # installation → install(ation) → install
        cands.append(word[:-5] + 'e')
    elif word.endswith('tion') and n > 6:
        cands.append(word[:-4])

    return cands


# ── SQLite 大词典（懒加载单例）────────────────────────────────────────────────
_db = None

def _get_db():
    global _db
    if _db is None:
        try:
            from translation.dict_db import DictDB
            _db = DictDB()
        except Exception as e:
            logger.debug(f'DictDB 不可用：{e}')
            _db = None
    return _db


def _word_translate(word: str) -> Optional[str]:
    """单词 → 中文，含词形还原；未命中返回 None。"""
    key = _normalize_en(word)
    if key in EN_ZH:
        return EN_ZH[key]
    for lemma in _lemmatize(key):
        if lemma in EN_ZH:
            return EN_ZH[lemma]
    db = _get_db()
    if db and db.ready:
        tr = db.lookup_en(key)
        if tr:
            return _first_meaning(tr)
        for lemma in _lemmatize(key):
            tr = db.lookup_en(lemma)
            if tr:
                return _first_meaning(tr)
    return None


# 从 ECDICT 多义释义中提取首个简洁含义的分隔符
_MEANING_SEP = re.compile(r'[；，\n;,、]')


def _first_meaning(tr: str) -> str:
    """从 ECDICT 多义释义中取第一个简短中文含义（用于短语拼合）。"""
    # ECDICT CSV 可能用字面 \n（两字符）作分隔
    tr = tr.replace('\\n', '\n')
    for part in _MEANING_SEP.split(tr):
        part = part.strip()
        # 去掉括号/方括号内的注释（如"permit的过去式"）
        part = re.sub(r'\s*[\(\[][^\)\]]*[\)\]]', '', part).strip()
        if part and re.search(r'[\u4e00-\u9fff]', part):
            return part
    return tr.split('\n')[0].strip() or tr


def _join_parts(parts: list) -> str:
    """拼合中英文片段：中文无间隔，中英文边界自动补空格。"""
    if not parts:
        return ''
    out = parts[0]
    for p in parts[1:]:
        prev_cjk = bool(re.search(r'[\u4e00-\u9fff]$', out))
        curr_cjk = bool(re.search(r'^[\u4e00-\u9fff]', p))
        if prev_cjk != curr_cjk:
            out += ' ' + p
        else:
            out += p
    return out


# 分段分隔符：句末标点后跟空格，或换行（不切数字小数点/网址/省略号中间的点）
_SEG_SPLIT = re.compile(r'([.!?:]\s+|\n+)')

# 英文分隔符 → 中文标点
_SEP_ZH = {'.': '。', '!': '！', '?': '？', ':': '：'}


def _sep_to_zh(sep: str) -> str:
    """将捕获到的分隔符转为中文标点；句末标点后若跟换行，保留换行。"""
    if sep[0] == '\n':
        return sep                          # 纯换行，直接保留
    zh = _SEP_ZH.get(sep[0], sep[0])
    return zh + ('\n' if '\n' in sep else '')   # 如 ".\n" → "。\n"


# ── 后端 ─────────────────────────────────────────────────────────────────────
class DictionaryBackend:

    def translate(self, text: str, target_lang: str = 'zh-CN',
                  source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None

        tgt = target_lang.lower()
        want_zh = tgt in _ZH_LANGS

        if _is_chinese(text):
            return self._zh_to_en(text)
        if want_zh:
            if _SEG_SPLIT.search(text):
                r = self._segment_translate(text)
                if r:
                    return r
            return self._en_to_zh(text)
        return None

    def _en_to_zh(self, text: str) -> Optional[Dict]:
        words = text.split()
        key = _normalize_en(text)

        # ① 内置词表精确匹配（优先，结果最简洁）
        if key in EN_ZH:
            return self._result(text, EN_ZH[key], 'en', 'zh-CN')

        # ② 词形还原后查内置表（仅单词）
        if len(words) == 1:
            for lemma in _lemmatize(key):
                if lemma in EN_ZH:
                    return self._result(text, EN_ZH[lemma], 'en', 'zh-CN')

        # ③ SQLite 大词典（10万+ 条）
        db = _get_db()
        if db and db.ready:
            tr = db.lookup_en(key)
            if tr:
                return self._result(text, tr, 'en', 'zh-CN')
            if len(words) == 1:
                for lemma in _lemmatize(key):
                    tr = db.lookup_en(lemma)
                    if tr:
                        return self._result(text, tr, 'en', 'zh-CN')

        # ④ 多词短语逐词翻译拼合
        if len(words) >= 2:
            return self._phrase_translate(text, words)

        return None

    def _segment_translate(self, text: str) -> Optional[Dict]:
        """
        按标点/换行分段，各段独立翻译后拼合。
        分隔符映射为对应中文标点（. → 。  ! → ！  ? → ？  : → ：  \\n → \\n）。
        """
        parts = _SEG_SPLIT.split(text)
        # re.split 含捕获组：[文本, 分隔符, 文本, 分隔符, ...]
        if len(parts) <= 1:
            return None

        out: list = []
        any_hit = False

        for i, part in enumerate(parts):
            if i % 2 == 1:
                # 捕获到的分隔符
                out.append(_sep_to_zh(part))
            else:
                seg = part.strip()
                if not seg:
                    continue
                r = self._en_to_zh(seg)
                if r:
                    out.append(r['translated'])
                    any_hit = True
                else:
                    out.append(seg)

        if not any_hit:
            return None
        return self._result(text, ''.join(out).strip(), 'en', 'zh-CN')

    def _phrase_translate(self, original: str, words: list) -> Optional[Dict]:
        """
        逐词翻译后按基础语法规则拼合：
        - 跳过冠词 (a / an / the)
        - 否定词 (not / never / 缩写) → 在下一个实词前加"不"
        - 其余词按原序翻译；未命中的词保留英文原形
        - 有效命中率 < 40% 时返回 None，交给在线后端
        """
        parts: list = []
        hit = 0
        content_count = 0
        i = 0

        while i < len(words):
            raw = words[i]
            w   = _normalize_en(raw)

            # 跳过冠词
            if w in _ARTICLES:
                i += 1
                continue

            content_count += 1

            # 否定词 → "不" + 下一个实词
            if w in _NEGATIONS:
                i += 1
                # 跳过其后紧跟的冠词
                while i < len(words) and _normalize_en(words[i]) in _ARTICLES:
                    i += 1
                if i < len(words):
                    content_count += 1
                    zh = _word_translate(words[i])
                    if zh:
                        # '已连接' 取反 → '未连接'（去掉'已'前缀）
                        if zh.startswith('已'):
                            parts.append('未' + zh[1:])
                        else:
                            parts.append('不' + zh)
                    else:
                        parts.append('不' + words[i])
                    hit += 2 if zh else 1
                    i += 1
                else:
                    parts.append('不')
                    hit += 1
                continue

            # 普通词翻译
            zh = _word_translate(w)
            if zh:
                parts.append(zh)
                hit += 1
            else:
                parts.append(raw)   # 保留英文原形
            i += 1

        if not parts or content_count == 0:
            return None

        # 有效命中率低于 40% → 交给在线后端处理
        if hit / content_count < 0.4:
            return None

        return self._result(original, _join_parts(parts), 'en', 'zh-CN')

    def _zh_to_en(self, text: str) -> Optional[Dict]:
        key = text.strip()

        # ① 内置中→英表
        if key in ZH_EN:
            return self._result(text, ZH_EN[key], 'zh-CN', 'en')

        # ② SQLite 大词典（模糊匹配 translation 字段）
        db = _get_db()
        if db and db.ready:
            en = db.lookup_zh(key)
            if en:
                return self._result(text, en, 'zh-CN', 'en')
        return None

    @staticmethod
    def _result(original, translated, src, tgt) -> Dict:
        return {
            'original': original,
            'translated': translated,
            'backend': 'dictionary',
            'source_lang': src,
            'target_lang': tgt,
        }
